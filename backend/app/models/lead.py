"""Modelo SQLAlchemy para Leads.

Um Lead representa um contato que iniciou uma conversa via WhatsApp.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LeadStatus(str, enum.Enum):
    """Status de qualificação do lead no funil de vendas."""

    NEW = "new"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    SCHEDULED = "scheduled"
    INTERVENTION = "intervention"  # Requer intervenção humana
    DISQUALIFIED = "disqualified"
    CLOSED = "closed"


class Lead(Base):
    """Lead que iniciou contato via WhatsApp."""

    __tablename__ = "leads"

    # Contato
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status no funil
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status"),
        default=LeadStatus.NEW,
        nullable=False,
        index=True,
    )

    # Qualificação (3 perguntas-chave do PRD)
    segment: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Segmento de atuação da empresa do lead",
    )
    budget: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Orçamento estimado para implementação",
    )
    timeline: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Prazo estimado para implementação",
    )

    # Contexto adicional
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    conversations: Mapped[list["Conversation"]] = relationship(  # noqa: F821
        back_populates="lead",
        cascade="all, delete-orphan",
    )
    appointments: Mapped[list["Appointment"]] = relationship(  # noqa: F821
        back_populates="lead",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Lead phone={self.phone_number} status={self.status}>"
