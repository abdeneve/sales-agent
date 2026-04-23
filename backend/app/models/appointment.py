"""Modelo SQLAlchemy para Agendamentos.

Um Appointment representa uma reunião de vendas agendada pelo agente
via Google Calendar (ou mock em desenvolvimento).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AppointmentStatus(str, enum.Enum):
    """Status do agendamento."""

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class Appointment(Base):
    """Reunião de vendas agendada pelo agente."""

    __tablename__ = "appointments"

    # FK para Lead
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
    )

    # Horário
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    duration_minutes: Mapped[int] = mapped_column(default=30, nullable=False)

    # Referência externa
    calendar_event_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="ID do evento no Google Calendar",
    )
    meeting_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Link do Google Meet ou outra plataforma",
    )

    # Observações
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    lead: Mapped["Lead"] = relationship(back_populates="appointments")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Appointment lead_id={self.lead_id} scheduled_at={self.scheduled_at}>"
