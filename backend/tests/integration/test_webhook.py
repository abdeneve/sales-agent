"""Testes de integração para o endpoint de webhook da EvolutionAPI.

Testa o endpoint HTTP completo (request → response) com banco SQLite em memória.
O LangGraph e o EvolutionClient são mockados para evitar I/O externo.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.models.lead import Lead, LeadStatus


# ---------------------------------------------------------------------------
# Fixtures de payload (payload real da EvolutionAPI v2)
# ---------------------------------------------------------------------------


@pytest.fixture()
def evolution_payload_message() -> dict:
    """Payload real de mensagem recebida pela EvolutionAPI (messages.upsert)."""
    return {
        "event": "messages.upsert",
        "instance": "sales_agent",
        "data": {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "ABC123",
            },
            "message": {
                "conversation": "Quero agendar uma reunião",
            },
        },
    }


@pytest.fixture()
def evolution_payload_outbound() -> dict:
    """Payload de mensagem enviada pelo próprio agente (deve ser ignorada)."""
    return {
        "event": "messages.upsert",
        "instance": "sales_agent",
        "data": {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": True,  # Enviada pelo agente → deve ser ignorada
                "id": "DEF456",
            },
            "message": {
                "conversation": "Olá! Como posso te ajudar?",
            },
        },
    }


@pytest.fixture()
def evolution_payload_connection_update() -> dict:
    """Payload de evento de conexão (não é mensagem → deve ser ignorado)."""
    return {
        "event": "connection.update",
        "instance": "sales_agent",
        "data": {"state": "open"},
    }


# ---------------------------------------------------------------------------
# Testes: POST /api/v1/webhooks/evolution
# ---------------------------------------------------------------------------


class TestEvolutionWebhook:
    """Testes de integração para o endpoint de webhook."""

    async def test_retorna_accepted_para_mensagem_valida(
        self,
        client: AsyncClient,
        evolution_payload_message: dict,
    ) -> None:
        """Retorna 200 + status=accepted para mensagem válida."""
        # Mockar o grafo para não chamar o LLM real
        mock_graph_response: dict = {
            "user_intent": "scheduling",
            "qualification_step": 1,
            "is_qualified": False,
            "agent_response": "Qual é o segmento da sua empresa?",
            "should_handoff": False,
        }

        with (
            patch("app.api.webhooks._agent_graph") as mock_graph,
            patch("app.api.webhooks._evolution_client") as mock_evolution,
        ):
            mock_graph.ainvoke = AsyncMock(return_value=mock_graph_response)
            mock_evolution.send_text_message = AsyncMock(return_value=True)

            response = await client.post(
                "/api/v1/webhooks/evolution",
                json=evolution_payload_message,
            )

        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    async def test_retorna_ignored_para_evento_de_conexao(
        self,
        client: AsyncClient,
        evolution_payload_connection_update: dict,
    ) -> None:
        """Retorna status=ignored para eventos que não são mensagens."""
        response = await client.post(
            "/api/v1/webhooks/evolution",
            json=evolution_payload_connection_update,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    async def test_retorna_ignored_para_mensagem_de_saida(
        self,
        client: AsyncClient,
        evolution_payload_outbound: dict,
    ) -> None:
        """Retorna status=ignored para mensagens enviadas pelo agente (fromMe=True)."""
        response = await client.post(
            "/api/v1/webhooks/evolution",
            json=evolution_payload_outbound,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    async def test_retorna_422_para_payload_invalido(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna 422 para payload malformado (sem campos obrigatórios)."""
        response = await client.post(
            "/api/v1/webhooks/evolution",
            json={"invalid": "payload"},
        )

        assert response.status_code == 422

    async def test_cria_lead_no_banco(
        self,
        client: AsyncClient,
        evolution_payload_message: dict,
        db_session,
    ) -> None:
        """Verifica que o lead é criado no banco após processar o webhook."""
        from sqlalchemy import select

        mock_graph_response: dict = {
            "user_intent": "scheduling",
            "qualification_step": 1,
            "is_qualified": False,
            "agent_response": "Qual é o segmento?",
            "should_handoff": False,
        }

        with (
            patch("app.api.webhooks._agent_graph") as mock_graph,
            patch("app.api.webhooks._evolution_client") as mock_evolution,
        ):
            mock_graph.ainvoke = AsyncMock(return_value=mock_graph_response)
            mock_evolution.send_text_message = AsyncMock(return_value=True)

            await client.post(
                "/api/v1/webhooks/evolution",
                json=evolution_payload_message,
            )

        # Verificar que o lead foi criado
        result = await db_session.execute(
            select(Lead).where(Lead.phone_number == "5511999999999")
        )
        lead = result.scalar_one_or_none()
        assert lead is not None
        assert lead.phone_number == "5511999999999"

    async def test_evolution_client_chamado_com_resposta(
        self,
        client: AsyncClient,
        evolution_payload_message: dict,
    ) -> None:
        """Verifica que send_text_message é chamado com a resposta do agente."""
        mock_graph_response: dict = {
            "user_intent": "scheduling",
            "qualification_step": 1,
            "is_qualified": False,
            "agent_response": "Qual é o segmento da sua empresa?",
            "should_handoff": False,
        }

        with (
            patch("app.api.webhooks._agent_graph") as mock_graph,
            patch("app.api.webhooks._evolution_client") as mock_evolution,
        ):
            mock_graph.ainvoke = AsyncMock(return_value=mock_graph_response)
            mock_evolution.send_text_message = AsyncMock(return_value=True)

            await client.post(
                "/api/v1/webhooks/evolution",
                json=evolution_payload_message,
            )

        mock_evolution.send_text_message.assert_called_once_with(
            "5511999999999",
            "Qual é o segmento da sua empresa?",
        )
