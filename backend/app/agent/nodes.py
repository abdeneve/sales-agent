"""Nós de execução do grafo LangGraph.

Cada função recebe o AgentState completo e retorna um dict com os campos
a serem atualizados. Os nós são stateless — todo o estado é no TypedDict.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.agent.prompts import (
    HANDOFF_MESSAGE,
    INTENT_CLASSIFIER_HUMAN,
    INTENT_CLASSIFIER_SYSTEM,
    KB_QA_SYSTEM,
    QUALIFICATION_COMPLETE_MESSAGE,
    QUALIFICATION_QUESTIONS,
    SCHEDULING_SUCCESS_MESSAGE,
)
from app.agent.state import AgentState
from app.config import settings
from app.integrations.calendar import CalendarClient
from app.integrations.mcp_client import MCPClient
from app.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM compartilhado (instanciado uma vez no módulo)
# ---------------------------------------------------------------------------

_llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    temperature=0,
)

_kb_service = KnowledgeService()
_calendar_client = CalendarClient()
_mcp_client = MCPClient()


# ---------------------------------------------------------------------------
# Nó 1: classify_intent
# ---------------------------------------------------------------------------


async def classify_intent(state: AgentState) -> dict[str, Any]:
    """Analisa a última mensagem e classifica a intenção do lead.

    Returns:
        Dict com ``user_intent`` atualizado: "scheduling" | "support" | "unknown".
    """
    messages = state.get("messages", [])
    last_message = messages[-1]["content"] if messages else ""

    logger.info("Classificando intenção para mensagem: %.50s…", last_message)

    try:
        response = await _llm.ainvoke(
            [
                SystemMessage(content=INTENT_CLASSIFIER_SYSTEM),
                HumanMessage(
                    content=INTENT_CLASSIFIER_HUMAN.format(last_message=last_message)
                ),
            ]
        )
        raw = response.content.strip().lower()
        intent = raw if raw in ("scheduling", "support", "unknown") else "unknown"
    except Exception:
        logger.exception("Erro ao classificar intenção; assumindo 'unknown'")
        intent = "unknown"

    logger.info("Intenção detectada: %s", intent)
    return {"user_intent": intent}


# ---------------------------------------------------------------------------
# Nó 2: qualify_lead
# ---------------------------------------------------------------------------


async def _extract_info(field: str, description: str, message: str) -> str | None:
    """Extrai uma informação específica da mensagem usando o LLM.

    Returns:
        O valor extraído ou None se for 'UNKNOWN'.
    """
    from app.agent.prompts import QUALIFICATION_EXTRACTOR_HUMAN, QUALIFICATION_EXTRACTOR_SYSTEM

    try:
        response = await _llm.ainvoke(
            [
                SystemMessage(
                    content=QUALIFICATION_EXTRACTOR_SYSTEM.format(
                        field=field, description=description
                    )
                ),
                HumanMessage(content=QUALIFICATION_EXTRACTOR_HUMAN.format(message=message)),
            ]
        )
        raw = response.content.strip()
        return raw if raw.upper() != "UNKNOWN" else None
    except Exception:
        logger.exception("Erro ao extrair campo %s", field)
        return None


async def qualify_lead(state: AgentState) -> dict[str, Any]:
    """Faz a próxima pergunta de qualificação ou marca o lead como qualificado.

    O campo ``qualification_step`` representa quantas perguntas já foram FEITAS:
    - step=0 → nenhuma pergunta feita → envia Q1 (segmento)
    - step=1 → Q1 foi feita → extrai resposta como segmento → envia Q2 (orçamento)
    - step=2 → Q2 foi feita → extrai resposta como budget → envia Q3 (prazo)
    - step=3 → Q3 foi feita → extrai resposta como timeline → marca qualificado

    Returns:
        Dict com o campo da pergunta respondida, ``qualification_step`` incrementado
        e, se concluído, ``is_qualified=True`` e ``agent_response`` de confirmação.
    """
    step = state.get("qualification_step", 0)
    messages = state.get("messages", [])
    updates: dict[str, Any] = {}

    # Salvar a resposta da pergunta anterior (step indica qual pergunta acabou)
    if step >= 1 and messages:
        answer = messages[-1]["content"]
        if step == 1:
            val = await _extract_info("segment", "Setor de atuação da empresa", answer)
            updates["segment"] = val or answer  # Fallback para o texto bruto se não extrair
        elif step == 2:
            val = await _extract_info("budget", "Orçamento para implementação de IA", answer)
            updates["budget"] = val or answer
        elif step == 3:
            val = await _extract_info("timeline", "Prazo desejado para o projeto", answer)
            updates["timeline"] = val or answer

    # Qualificação completa quando todas as 3 respostas foram coletadas (ou tentadas)
    if step >= 3:
        updates["is_qualified"] = True
        updates["qualification_step"] = step + 1
        updates["agent_response"] = QUALIFICATION_COMPLETE_MESSAGE
        logger.info("Lead qualificado com sucesso (phone=%s)", state.get("lead_phone"))
        return updates

    # Fazer a próxima pergunta (step é o índice da próxima pergunta a fazer)
    question = QUALIFICATION_QUESTIONS[step]
    updates["qualification_step"] = step + 1
    updates["agent_response"] = question

    logger.info("Pergunta de qualificação %d enviada (step=%d)", step + 1, step)
    return updates


# ---------------------------------------------------------------------------
# Nó 3: rag_qa
# ---------------------------------------------------------------------------


async def rag_qa(state: AgentState) -> dict[str, Any]:
    """Responde dúvidas do lead usando a base de conhecimento (RAG).

    Busca o contexto dinamicamente via KnowledgeService.

    Returns:
        Dict com ``agent_response`` contendo a resposta gerada pelo LLM.
    """
    messages = state.get("messages", [])
    last_message = messages[-1]["content"] if messages else ""

    logger.info("Consultando KB para: %.50s…", last_message)

    context = _kb_service.get_context()

    try:
        response = await _llm.ainvoke(
            [
                SystemMessage(
                    content=KB_QA_SYSTEM.format(context=context)
                ),
                HumanMessage(content=last_message),
            ]
        )
        answer = response.content.strip()
    except Exception:
        logger.exception("Erro ao consultar KB; usando fallback")
        answer = (
            "Desculpe, não consegui buscar essa informação agora. "
            "Um consultor entrará em contato em breve! 🙏"
        )

    return {"agent_response": answer}


# ---------------------------------------------------------------------------
# Nó 4: handoff_intervention
# ---------------------------------------------------------------------------


async def handoff_intervention(state: AgentState) -> dict[str, Any]:
    """Marca a conversa para intervenção humana e envia mensagem de handoff.

    Returns:
        Dict com ``should_handoff=True`` e ``agent_response`` de handoff.
    """
    logger.warning(
        "Handoff solicitado para lead %s (intent=%s)",
        state.get("lead_phone"),
        state.get("user_intent"),
    )
    return {
        "should_handoff": True,
        "agent_response": HANDOFF_MESSAGE,
    }


# ---------------------------------------------------------------------------
# Nó 5: schedule_and_crm
# ---------------------------------------------------------------------------


async def schedule_and_crm(state: AgentState) -> dict[str, Any]:
    """Agenda a reunião no Calendar e salva os dados no CRM (Excel via MCP).

    Returns:
        Dict com ``meeting_scheduled=True`` e ``agent_response`` de sucesso.
    """
    from datetime import datetime

    phone = state.get("lead_phone", "unknown")
    segment = state.get("segment", "N/A")
    budget = state.get("budget", "N/A")
    timeline = state.get("timeline", "N/A")

    logger.info("Iniciando agendamento e CRM para lead %s", phone)

    # 1. Salvar no CRM (MCP)
    crm_data = {
        "phone": phone,
        "segment": segment,
        "budget": budget,
        "timeline": timeline,
    }
    await _mcp_client.update_lead_crm(crm_data)

    # 2. Agendar no Calendar
    event = await _calendar_client.schedule_meeting(phone, segment)

    # 3. Formatar resposta
    # Ex: "2024-05-20T10:00:00" -> "20/05 às 10:00"
    try:
        dt = datetime.fromisoformat(event["start"])
        formatted_date = dt.strftime("%d/%m às %H:%M")
    except Exception:
        formatted_date = event["start"]

    response = SCHEDULING_SUCCESS_MESSAGE.format(
        date_time=formatted_date, meeting_link=event["link"]
    )

    return {
        "meeting_scheduled": True,
        "agent_response": response,
    }
