"""Serviço de gerenciamento de Leads.

Toda lógica de negócio relacionada ao Lead fica aqui.
Os endpoints e os nós do agente chamam estas funções, nunca o ORM diretamente.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadStatus

logger = logging.getLogger(__name__)


async def get_or_create_lead(
    db: AsyncSession,
    phone_number: str,
) -> Lead:
    """Retorna o Lead existente ou cria um novo pelo número de telefone.

    O telefone é o identificador único do lead no sistema (vem do WhatsApp).

    Args:
        db: Sessão assíncrona do banco de dados.
        phone_number: Número do lead (apenas dígitos, ex: "5511999999999").

    Returns:
        Instância do Lead (existente ou recém-criado).
    """
    result = await db.execute(
        select(Lead).where(Lead.phone_number == phone_number)
    )
    lead = result.scalar_one_or_none()

    if lead is None:
        lead = Lead(phone_number=phone_number, status=LeadStatus.NEW)
        db.add(lead)
        await db.flush()  # Gera o UUID sem commitar
        logger.info("Novo lead criado: phone=%s id=%s", phone_number, lead.id)
    else:
        logger.debug("Lead existente encontrado: phone=%s id=%s", phone_number, lead.id)

    return lead


async def update_lead_qualification(
    db: AsyncSession,
    lead_id: uuid.UUID,
    segment: str | None = None,
    budget: str | None = None,
    timeline: str | None = None,
) -> Lead:
    """Atualiza os dados de qualificação do lead.

    Apenas campos não-None são atualizados (patch parcial).

    Args:
        db: Sessão assíncrona.
        lead_id: UUID do lead.
        segment: Segmento de atuação.
        budget: Orçamento estimado.
        timeline: Prazo de implementação.

    Returns:
        Lead atualizado.

    Raises:
        ValueError: Se o Lead não for encontrado.
    """
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if lead is None:
        raise ValueError(f"Lead não encontrado: id={lead_id}")

    if segment is not None:
        lead.segment = segment
    if budget is not None:
        lead.budget = budget
    if timeline is not None:
        lead.timeline = timeline

    await db.flush()
    logger.info("Qualificação do lead %s atualizada", lead_id)
    return lead


async def set_lead_status(
    db: AsyncSession,
    lead_id: uuid.UUID,
    status: LeadStatus,
) -> Lead:
    """Atualiza o status do lead no funil.

    Args:
        db: Sessão assíncrona.
        lead_id: UUID do lead.
        status: Novo status.

    Returns:
        Lead atualizado.

    Raises:
        ValueError: Se o Lead não for encontrado.
    """
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if lead is None:
        raise ValueError(f"Lead não encontrado: id={lead_id}")

    lead.status = status
    await db.flush()
    logger.info("Status do lead %s atualizado para %s", lead_id, status)
    return lead
