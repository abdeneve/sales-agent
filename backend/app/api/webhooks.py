"""Endpoint de webhook da EvolutionAPI.

Recebe mensagens do WhatsApp, valida, enfileira o processamento em background
e retorna imediatamente (< 500ms conforme o SLA do spec).

Fluxo:
    POST /api/v1/webhooks/evolution
        → valida payload
        → retorna {"status": "accepted"} imediatamente
        → background: upsert lead → upsert conversation → roda grafo → envia resposta
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import build_agent_graph
from app.agent.state import AgentState
from app.dependencies import DBSession
from app.integrations.evolution import EvolutionClient
from app.models.lead import LeadStatus
from app.schemas.webhook import EvolutionWebhookPayload
from app.services.conversation_service import (
    append_message,
    get_or_create_conversation,
    request_intervention,
    save_agent_state,
)
from app.services.lead_service import (
    get_or_create_lead,
    set_lead_status,
    update_lead_qualification,
)
from app.services.sla_monitor import SLAMonitor

logger = logging.getLogger(__name__)

router = APIRouter()

# Grafo compilado uma única vez no startup do módulo (stateless, thread-safe)
_agent_graph = build_agent_graph()
_evolution_client = EvolutionClient()


# ---------------------------------------------------------------------------
# Background task: processa a mensagem com o grafo LangGraph
# ---------------------------------------------------------------------------


async def _process_message(
    db: AsyncSession,
    phone: str,
    message_text: str,
) -> None:
    """Processa uma mensagem recebida com o grafo LangGraph.

    Etapas:
    1. Upsert do Lead
    2. Upsert da Conversation
    3. Append da mensagem do lead ao histórico
    4. Montar o AgentState com o contexto da conversa
    5. Invocar o grafo
    6. Persistir o resultado (estado + resposta do agente)
    7. Enviar a resposta ao lead via EvolutionAPI
    8. Se handoff → marcar conversa para intervenção

    Args:
        db: Sessão de banco (criada no contexto da background task).
        phone: Número do lead.
        message_text: Texto da mensagem recebida.
    """
    try:
        # 1. Upsert lead
        lead = await get_or_create_lead(db, phone)

        # 2. Upsert conversa
        conversation = await get_or_create_conversation(db, lead.id)

        # 3. Append da mensagem do lead
        await append_message(db, conversation.id, "user", message_text)
        
        # [Phase 4] Emitir evento de recebimento para o dashboard
        await SLAMonitor.track_lead_received(str(lead.id), phone, message_text)

        # 4. Montar estado — retoma snapshot se existir
        snapshot: dict = conversation.agent_state_snapshot or {}
        messages = conversation.messages  # Já inclui a mensagem recém-adicionada

        initial_state: AgentState = {
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            "lead_phone": phone,
            "conversation_id": conversation.id,
            "user_intent": snapshot.get("user_intent"),
            "qualification_step": snapshot.get("qualification_step", 0),
            "is_qualified": snapshot.get("is_qualified", False),
            "segment": lead.segment,
            "budget": lead.budget,
            "timeline": lead.timeline,
            "should_handoff": False,
            "agent_response": None,
        }

        # 5. Invocar o grafo
        logger.info("Invocando grafo para phone=%s", phone)
        final_state: AgentState = await _agent_graph.ainvoke(initial_state)

        # 6. Persistir resultado
        state_to_save = {
            "user_intent": final_state.get("user_intent"),
            "qualification_step": final_state.get("qualification_step", 0),
            "is_qualified": final_state.get("is_qualified", False),
        }
        await save_agent_state(db, conversation.id, state_to_save)

        # Atualizar qualificação se avançou
        await update_lead_qualification(
            db,
            lead.id,
            segment=final_state.get("segment"),
            budget=final_state.get("budget"),
            timeline=final_state.get("timeline"),
        )

        # 7. Enviar resposta ao lead
        agent_response = final_state.get("agent_response")
        if agent_response:
            await append_message(db, conversation.id, "assistant", agent_response)
            await _evolution_client.send_text_message(phone, agent_response)
            
            # [Phase 4] Emitir evento de resposta do agente
            await SLAMonitor.track_agent_responded(str(lead.id), agent_response)

        # 8. Handoff → fila de intervenção
        if final_state.get("should_handoff"):
            await request_intervention(db, conversation.id)
            await set_lead_status(db, lead.id, LeadStatus.INTERVENTION)
            
            # [Phase 4] Emitir evento de intervenção
            await SLAMonitor.track_intervention_required(str(lead.id), "Handoff solicitado pelo agente")
            logger.warning("Lead %s enviado para fila de intervenção", phone)
        elif final_state.get("is_qualified"):
            await set_lead_status(db, lead.id, LeadStatus.QUALIFIED)
            
            # [Phase 4] Emitir evento de qualificação
            await SLAMonitor.track_lead_qualified(str(lead.id), final_state.get("segment"))

        await db.commit()
        logger.info("Mensagem de %s processada com sucesso", phone)

    except Exception:
        await db.rollback()
        logger.exception("Erro ao processar mensagem de %s", phone)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/evolution",
    summary="Webhook da EvolutionAPI",
    description=(
        "Recebe eventos do WhatsApp via EvolutionAPI. "
        "Retorna imediatamente e processa o grafo em background."
    ),
    status_code=200,
)
async def evolution_webhook(
    payload: EvolutionWebhookPayload,
    background_tasks: BackgroundTasks,
    db: DBSession,
) -> dict[str, str]:
    """Endpoint principal do webhook.

    Aceita o payload, valida e enfileira o processamento assíncrono.
    Retorna em < 500ms conforme especificado no PRD.

    Args:
        payload: Payload validado pelo Pydantic.
        background_tasks: Runner de background tasks do FastAPI.
        db: Sessão de banco de dados injetada.

    Returns:
        Dict com status "accepted" ou "ignored".
    """
    # Ignorar eventos que não são mensagens recebidas
    if payload.event != "messages.upsert":
        logger.debug("Evento ignorado: %s", payload.event)
        return {"status": "ignored", "reason": f"event '{payload.event}' not handled"}

    sender_phone = payload.sender_phone
    message_content = payload.message_content

    # Ignorar mensagens enviadas pelo próprio agente (from_me)
    if sender_phone is None or message_content is None:
        logger.debug("Mensagem de saída ou sem conteúdo ignorada")
        return {"status": "ignored", "reason": "outbound or empty message"}

    message_text = message_content.text
    logger.info(
        "Webhook recebido: phone=%s event=%s msg=%.50s",
        sender_phone,
        payload.event,
        message_text,
    )

    # Enfileirar processamento em background (retorno imediato = SLA < 500ms)
    background_tasks.add_task(_process_message, db, sender_phone, message_text)

    return {"status": "accepted"}
