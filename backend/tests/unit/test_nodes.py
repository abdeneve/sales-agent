"""Testes unitários para os nós do agente LangGraph.

Todos os testes mockam o LLM para não consumir créditos de API.
Os nós são testados de forma isolada — sem banco de dados, sem EvolutionAPI.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.nodes import classify_intent, handoff_intervention, qualify_lead, rag_qa
from app.agent.prompts import (
    HANDOFF_MESSAGE,
    QUALIFICATION_COMPLETE_MESSAGE,
    QUALIFICATION_QUESTIONS,
)
from app.agent.state import AgentState


# ---------------------------------------------------------------------------
# Fixtures base
# ---------------------------------------------------------------------------


@pytest.fixture()
def base_state() -> AgentState:
    """Estado mínimo para iniciar o grafo."""
    return AgentState(
        messages=[{"role": "user", "content": "Quero agendar uma reunião"}],
        lead_phone="5511999999999",
        conversation_id=None,
        user_intent=None,
        qualification_step=0,
        is_qualified=False,
        segment=None,
        budget=None,
        timeline=None,
        should_handoff=False,
        agent_response=None,
    )


@pytest.fixture()
def support_state() -> AgentState:
    """Estado com mensagem de suporte."""
    return AgentState(
        messages=[{"role": "user", "content": "Quanto custa a solução?"}],
        lead_phone="5511999999999",
        conversation_id=None,
        user_intent="support",
        qualification_step=0,
        is_qualified=False,
        segment=None,
        budget=None,
        timeline=None,
        should_handoff=False,
        agent_response=None,
    )


# ---------------------------------------------------------------------------
# Testes: classify_intent
# ---------------------------------------------------------------------------


class TestClassifyIntent:
    """Testes para o nó classify_intent."""

    async def test_detecta_scheduling(self, base_state: AgentState) -> None:
        """Classifica 'Quero agendar uma reunião' como scheduling."""
        mock_response = MagicMock()
        mock_response.content = "scheduling"

        with patch("app.agent.nodes._llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            result = await classify_intent(base_state)

        assert result["user_intent"] == "scheduling"

    async def test_detecta_support(self, support_state: AgentState) -> None:
        """Classifica pergunta de suporte como support."""
        mock_response = MagicMock()
        mock_response.content = "support"

        with patch("app.agent.nodes._llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            result = await classify_intent(support_state)

        assert result["user_intent"] == "support"

    async def test_detecta_unknown(self, base_state: AgentState) -> None:
        """Classifica mensagem ambígua como unknown."""
        state: AgentState = {**base_state, "messages": [{"role": "user", "content": "Oi"}]}
        mock_response = MagicMock()
        mock_response.content = "unknown"

        with patch("app.agent.nodes._llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            result = await classify_intent(state)

        assert result["user_intent"] == "unknown"

    async def test_fallback_em_erro_llm(self, base_state: AgentState) -> None:
        """Em caso de erro do LLM, retorna 'unknown' sem levantar exceção."""
        with patch("app.agent.nodes._llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("timeout"))
            result = await classify_intent(base_state)

        assert result["user_intent"] == "unknown"

    async def test_resposta_invalida_vira_unknown(self, base_state: AgentState) -> None:
        """Resposta inesperada do LLM é normalizada para 'unknown'."""
        mock_response = MagicMock()
        mock_response.content = "banana"

        with patch("app.agent.nodes._llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            result = await classify_intent(base_state)

        assert result["user_intent"] == "unknown"


# ---------------------------------------------------------------------------
# Testes: qualify_lead
# ---------------------------------------------------------------------------


class TestQualifyLead:
    """Testes para o nó qualify_lead."""

    async def test_primeira_pergunta_enviada(self, base_state: AgentState) -> None:
        """No passo 0, envia a primeira pergunta (segmento)."""
        result = await qualify_lead(base_state)

        assert result["qualification_step"] == 1
        assert result["agent_response"] == QUALIFICATION_QUESTIONS[0]

    async def test_segunda_pergunta_salva_segmento(self, base_state: AgentState) -> None:
        """No passo 1, salva segmento e envia pergunta de orçamento."""
        state: AgentState = {
            **base_state,
            "messages": [{"role": "user", "content": "E-commerce"}],
            "qualification_step": 1,
        }
        result = await qualify_lead(state)

        assert result["segment"] == "E-commerce"
        assert result["qualification_step"] == 2
        assert result["agent_response"] == QUALIFICATION_QUESTIONS[1]

    async def test_terceira_pergunta_salva_budget(self, base_state: AgentState) -> None:
        """No passo 2 (Q2 já foi feita), salva orçamento e envia Q3 (prazo)."""
        state: AgentState = {
            **base_state,
            "messages": [{"role": "user", "content": "R$ 10k"}],
            "qualification_step": 2,  # Q2 (orçamento) foi feita, recebendo a resposta
        }
        result = await qualify_lead(state)

        # Salva a resposta do orçamento
        assert result["budget"] == "R$ 10k"
        # Avança para o passo 3 (Q3 = prazo)
        assert result["qualification_step"] == 3
        # Envia a pergunta de prazo (índice 2 = 3ª pergunta)
        assert result["agent_response"] == QUALIFICATION_QUESTIONS[2]

    async def test_qualificacao_completa(self, base_state: AgentState) -> None:
        """No passo 3, salva prazo e marca lead como qualificado."""
        state: AgentState = {
            **base_state,
            "messages": [{"role": "user", "content": "3 meses"}],
            "qualification_step": 3,
            "segment": "E-commerce",
            "budget": "R$ 10k",
        }
        result = await qualify_lead(state)

        assert result["timeline"] == "3 meses"
        assert result["is_qualified"] is True
        assert result["agent_response"] == QUALIFICATION_COMPLETE_MESSAGE


# ---------------------------------------------------------------------------
# Testes: rag_qa
# ---------------------------------------------------------------------------


class TestRagQA:
    """Testes para o nó rag_qa."""

    async def test_responde_duvida(self, support_state: AgentState) -> None:
        """Retorna resposta do LLM para pergunta de suporte."""
        mock_response = MagicMock()
        mock_response.content = "O preço começa em R$ 3.000/mês."

        with patch("app.agent.nodes._llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            result = await rag_qa(support_state)

        assert result["agent_response"] == "O preço começa em R$ 3.000/mês."

    async def test_fallback_em_erro_llm(self, support_state: AgentState) -> None:
        """Em caso de erro, retorna mensagem de fallback sem levantar exceção."""
        with patch("app.agent.nodes._llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("timeout"))
            result = await rag_qa(support_state)

        assert "consultor" in result["agent_response"].lower()


# ---------------------------------------------------------------------------
# Testes: handoff_intervention
# ---------------------------------------------------------------------------


class TestHandoffIntervention:
    """Testes para o nó handoff_intervention."""

    async def test_define_should_handoff(self, base_state: AgentState) -> None:
        """Marca should_handoff=True e retorna mensagem de handoff."""
        result = await handoff_intervention(base_state)

        assert result["should_handoff"] is True
        assert result["agent_response"] == HANDOFF_MESSAGE

    async def test_mensagem_handoff_nao_vazia(self, base_state: AgentState) -> None:
        """A mensagem de handoff não é vazia."""
        result = await handoff_intervention(base_state)

        assert result["agent_response"]
        assert len(result["agent_response"]) > 10
