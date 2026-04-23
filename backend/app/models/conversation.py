"""Modelo SQLAlchemy para Conversas.

Uma Conversation mapeia a troca de mensagens entre Lead e o Agente dentro
de uma sessão de atendimento. O histórico de mensagens é serializado em JSON.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConversationStatus(str, enum.Enum):
    """Status da conversa em andamento."""

    ACTIVE = "active"
    WAITING_AGENT = "waiting_agent"  # Na fila de intervenção
    TAKEN_OVER = "taken_over"       # Assumida pelo consultor humano
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Conversation(Base):
    """Sessão de atendimento entre Lead e o Agente."""

    __tablename__ = "conversations"

    # FK para Lead
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status da conversa
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="conversation_status"),
        default=ConversationStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Histórico de mensagens: lista de {"role": "user"|"assistant", "content": str, "timestamp": str}
    messages: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)

    # Estado interno do agente (snapshot do AgentState para retomada)
    agent_state_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Intervenção humana
    assigned_to: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Email/ID do consultor que assumiu a conversa",
    )
    intervention_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # SLA tracking
    first_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp da primeira mensagem do lead (início do SLA)",
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Quando o agendamento foi concluído (fim do SLA)",
    )

    # Relacionamentos
    lead: Mapped["Lead"] = relationship(back_populates="conversations")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Conversation lead_id={self.lead_id} status={self.status}>"
