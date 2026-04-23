"""Schemas Pydantic para o Dashboard dos Consultores."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.conversation import ConversationStatus
from app.models.lead import LeadStatus


class SLAStats(BaseModel):
    """Estatísticas de SLA em tempo real."""

    average_response_seconds: float = Field(description="Média de tempo de resposta em segundos")
    conversations_within_sla: int = Field(description="Conversas dentro do SLA de 2 minutos")
    conversations_breached_sla: int = Field(description="Conversas que ultrapassaram o SLA")
    sla_compliance_rate: float = Field(description="Taxa de conformidade com SLA (0.0 a 1.0)")


class LeadFunnelStats(BaseModel):
    """Funil de leads por status."""

    status_counts: dict[LeadStatus, int] = Field(description="Contagem de leads por status")
    total: int = Field(description="Total de leads")
    scheduled_today: int = Field(description="Agendamentos realizados hoje")


class InterventionItem(BaseModel):
    """Item na fila de intervenção do consultor."""

    conversation_id: str
    lead_id: str
    lead_name: str | None
    lead_phone: str
    intervention_requested_at: datetime
    elapsed_seconds: float = Field(description="Tempo decorrido desde a solicitação de intervenção")
    last_message_preview: str = Field(description="Prévia da última mensagem do lead")


class DashboardStats(BaseModel):
    """Estatísticas completas para o Dashboard."""

    sla: SLAStats
    funnel: LeadFunnelStats
    active_conversations: int
    intervention_queue: list[InterventionItem]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class WebSocketEvent(BaseModel):
    """Evento emitido via WebSocket para o Dashboard."""

    event_type: str = Field(
        description=(
            "lead_received | lead_qualifying | lead_qualified | "
            "meeting_scheduled | intervention_requested | consultant_took_over"
        )
    )
    conversation_id: str
    lead_id: str
    lead_phone: str
    data: dict = Field(default_factory=dict, description="Dados adicionais do evento")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
