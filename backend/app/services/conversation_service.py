"""Serviço de gerenciamento de Conversas.

Toda lógica de negócio relacionada ao Conversation fica aqui.
Inclui upsert de conversa, append de mensagens e controle de intervenção.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationStatus

logger = logging.getLogger(__name__)


async def get_or_create_conversation(
    db: AsyncSession,
    lead_id: uuid.UUID,
) -> Conversation:
    """Retorna a conversa ACTIVE do lead ou cria uma nova.

    Um lead pode ter apenas uma conversa ativa por vez.

    Args:
        db: Sessão assíncrona.
        lead_id: UUID do Lead.

    Returns:
        Instância da Conversation (existente ou recém-criada).
    """
    result = await db.execute(
        select(Conversation).where(
            Conversation.lead_id == lead_id,
            Conversation.status == ConversationStatus.ACTIVE,
        )
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        now = datetime.now(UTC)
        conversation = Conversation(
            lead_id=lead_id,
            status=ConversationStatus.ACTIVE,
            messages=[],
            first_message_at=now,
        )
        db.add(conversation)
        await db.flush()
        logger.info(
            "Nova conversa criada: lead_id=%s conversation_id=%s",
            lead_id,
            conversation.id,
        )
    else:
        logger.debug(
            "Conversa ativa encontrada: lead_id=%s conversation_id=%s",
            lead_id,
            conversation.id,
        )

    return conversation


async def append_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    role: str,
    content: str,
) -> Conversation:
    """Adiciona uma mensagem ao histórico da conversa.

    Args:
        db: Sessão assíncrona.
        conversation_id: UUID da Conversation.
        role: "user" para mensagem do lead, "assistant" para resposta do agente.
        content: Texto da mensagem.

    Returns:
        Conversation atualizada.

    Raises:
        ValueError: Se a Conversation não for encontrada.
    """
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise ValueError(f"Conversation não encontrada: id={conversation_id}")

    new_message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    # SQLAlchemy não detecta mutações em listas JSON — precisamos reatribuir
    conversation.messages = [*conversation.messages, new_message]

    await db.flush()
    logger.debug(
        "Mensagem appendada à conversa %s (role=%s)", conversation_id, role
    )
    return conversation


async def save_agent_state(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    state_snapshot: dict,
) -> Conversation:
    """Salva o snapshot do estado do agente na conversa.

    Permite retomar o fluxo na próxima mensagem do lead.

    Args:
        db: Sessão assíncrona.
        conversation_id: UUID da Conversation.
        state_snapshot: Dict com o AgentState serializado.

    Returns:
        Conversation atualizada.

    Raises:
        ValueError: Se a Conversation não for encontrada.
    """
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise ValueError(f"Conversation não encontrada: id={conversation_id}")

    conversation.agent_state_snapshot = state_snapshot
    await db.flush()
    return conversation


async def request_intervention(
    db: AsyncSession,
    conversation_id: uuid.UUID,
) -> Conversation:
    """Coloca a conversa na fila de intervenção humana.

    Muda o status para WAITING_AGENT e registra o timestamp da solicitação.

    Args:
        db: Sessão assíncrona.
        conversation_id: UUID da Conversation.

    Returns:
        Conversation atualizada.

    Raises:
        ValueError: Se a Conversation não for encontrada.
    """
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise ValueError(f"Conversation não encontrada: id={conversation_id}")

    conversation.status = ConversationStatus.WAITING_AGENT
    conversation.intervention_requested_at = datetime.now(UTC)
    await db.flush()
    logger.warning(
        "Intervenção solicitada para conversa %s", conversation_id
    )
    return conversation
