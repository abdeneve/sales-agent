"""Schemas Pydantic para a entidade Conversation."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.conversation import ConversationStatus


class MessageEntry(BaseModel):
    """Uma entrada no histórico de mensagens."""

    role: str = Field(..., description="'user' ou 'assistant'")
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ConversationResponse(BaseModel):
    """Schema de resposta de uma conversa."""

    id: uuid.UUID
    lead_id: uuid.UUID
    status: ConversationStatus
    messages: list[MessageEntry]
    assigned_to: str | None
    intervention_requested_at: datetime | None
    first_message_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    """Resumo de conversa para listas e dashboard."""

    id: uuid.UUID
    lead_id: uuid.UUID
    status: ConversationStatus
    message_count: int
    assigned_to: str | None
    first_message_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
