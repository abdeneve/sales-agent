"""Testes unitários para os serviços de negócio (lead e conversation).

Usa banco SQLite em memória via fixture `db_session` do conftest.py.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationStatus
from app.models.lead import Lead, LeadStatus
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_lead(db: AsyncSession, phone: str = "5511999999999") -> Lead:
    """Cria e faz flush de um lead para uso nos testes."""
    lead = Lead(phone_number=phone, status=LeadStatus.NEW)
    db.add(lead)
    await db.flush()
    return lead


# ---------------------------------------------------------------------------
# Testes: lead_service
# ---------------------------------------------------------------------------


class TestLeadService:
    """Testes para as funções do lead_service."""

    async def test_get_or_create_lead_cria_novo(
        self, db_session: AsyncSession
    ) -> None:
        """Cria um novo lead quando o telefone não existe."""
        lead = await get_or_create_lead(db_session, "5511111111111")

        assert lead.id is not None
        assert lead.phone_number == "5511111111111"
        assert lead.status == LeadStatus.NEW

    async def test_get_or_create_lead_retorna_existente(
        self, db_session: AsyncSession
    ) -> None:
        """Retorna o mesmo lead em chamadas subsequentes com o mesmo telefone."""
        lead1 = await get_or_create_lead(db_session, "5511222222222")
        lead2 = await get_or_create_lead(db_session, "5511222222222")

        assert lead1.id == lead2.id

    async def test_update_lead_qualification_parcial(
        self, db_session: AsyncSession
    ) -> None:
        """Atualiza apenas os campos passados (patch parcial)."""
        lead = await _make_lead(db_session, "5511333333333")

        updated = await update_lead_qualification(
            db_session, lead.id, segment="E-commerce"
        )

        assert updated.segment == "E-commerce"
        assert updated.budget is None  # Não foi passado
        assert updated.timeline is None

    async def test_update_lead_qualification_completo(
        self, db_session: AsyncSession
    ) -> None:
        """Atualiza os 3 campos de qualificação de uma vez."""
        lead = await _make_lead(db_session, "5511444444444")

        updated = await update_lead_qualification(
            db_session,
            lead.id,
            segment="Saúde",
            budget="R$ 10k",
            timeline="3 meses",
        )

        assert updated.segment == "Saúde"
        assert updated.budget == "R$ 10k"
        assert updated.timeline == "3 meses"

    async def test_update_lead_qualification_nao_encontrado(
        self, db_session: AsyncSession
    ) -> None:
        """Levanta ValueError se o lead não existir."""
        with pytest.raises(ValueError, match="Lead não encontrado"):
            await update_lead_qualification(db_session, uuid.uuid4())

    async def test_set_lead_status(self, db_session: AsyncSession) -> None:
        """Atualiza o status do lead corretamente."""
        lead = await _make_lead(db_session, "5511555555555")

        updated = await set_lead_status(
            db_session, lead.id, LeadStatus.QUALIFYING
        )

        assert updated.status == LeadStatus.QUALIFYING


# ---------------------------------------------------------------------------
# Testes: conversation_service
# ---------------------------------------------------------------------------


class TestConversationService:
    """Testes para as funções do conversation_service."""

    async def test_get_or_create_conversation_cria_nova(
        self, db_session: AsyncSession
    ) -> None:
        """Cria uma nova conversa para um lead sem conversa ativa."""
        lead = await _make_lead(db_session, "5511666666666")

        conv = await get_or_create_conversation(db_session, lead.id)

        assert conv.id is not None
        assert conv.lead_id == lead.id
        assert conv.status == ConversationStatus.ACTIVE
        assert conv.messages == []
        assert conv.first_message_at is not None

    async def test_get_or_create_conversation_retorna_existente(
        self, db_session: AsyncSession
    ) -> None:
        """Retorna a conversa ativa existente sem criar duplicata."""
        lead = await _make_lead(db_session, "5511777777777")

        conv1 = await get_or_create_conversation(db_session, lead.id)
        conv2 = await get_or_create_conversation(db_session, lead.id)

        assert conv1.id == conv2.id

    async def test_append_message_adiciona_ao_historico(
        self, db_session: AsyncSession
    ) -> None:
        """Adiciona mensagem ao histórico e incrementa a lista."""
        lead = await _make_lead(db_session, "5511888888888")
        conv = await get_or_create_conversation(db_session, lead.id)

        await append_message(db_session, conv.id, "user", "Olá!")
        updated = await append_message(db_session, conv.id, "assistant", "Oi!")

        assert len(updated.messages) == 2
        assert updated.messages[0]["role"] == "user"
        assert updated.messages[0]["content"] == "Olá!"
        assert updated.messages[1]["role"] == "assistant"
        assert "timestamp" in updated.messages[0]

    async def test_append_message_conversa_nao_encontrada(
        self, db_session: AsyncSession
    ) -> None:
        """Levanta ValueError se a conversa não existir."""
        with pytest.raises(ValueError, match="Conversation não encontrada"):
            await append_message(db_session, uuid.uuid4(), "user", "Teste")

    async def test_save_agent_state(self, db_session: AsyncSession) -> None:
        """Persiste o snapshot do estado do agente na conversa."""
        lead = await _make_lead(db_session, "5511900000001")
        conv = await get_or_create_conversation(db_session, lead.id)

        snapshot = {"user_intent": "scheduling", "qualification_step": 1}
        updated = await save_agent_state(db_session, conv.id, snapshot)

        assert updated.agent_state_snapshot == snapshot

    async def test_request_intervention_muda_status(
        self, db_session: AsyncSession
    ) -> None:
        """Muda o status da conversa para WAITING_AGENT e registra o timestamp."""
        lead = await _make_lead(db_session, "5511900000002")
        conv = await get_or_create_conversation(db_session, lead.id)

        updated = await request_intervention(db_session, conv.id)

        assert updated.status == ConversationStatus.WAITING_AGENT
        assert updated.intervention_requested_at is not None

    async def test_request_intervention_conversa_nao_encontrada(
        self, db_session: AsyncSession
    ) -> None:
        """Levanta ValueError se a conversa não existir."""
        with pytest.raises(ValueError, match="Conversation não encontrada"):
            await request_intervention(db_session, uuid.uuid4())
