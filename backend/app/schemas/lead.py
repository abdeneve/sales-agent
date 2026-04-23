"""Schemas Pydantic para a entidade Lead."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.lead import LeadStatus


class LeadBase(BaseModel):
    """Campos compartilhados entre criação e resposta."""

    phone_number: str = Field(..., description="Número de telefone com DDI (ex: 5511999999999)")
    name: str | None = Field(default=None, description="Nome do lead")
    segment: str | None = Field(default=None, description="Segmento de atuação")
    budget: str | None = Field(default=None, description="Orçamento estimado")
    timeline: str | None = Field(default=None, description="Prazo de implementação")
    notes: str | None = Field(default=None, description="Observações adicionais")


class LeadCreate(LeadBase):
    """Schema para criação de um novo lead."""

    pass


class LeadUpdate(BaseModel):
    """Schema para atualização parcial de um lead."""

    name: str | None = None
    status: LeadStatus | None = None
    segment: str | None = None
    budget: str | None = None
    timeline: str | None = None
    notes: str | None = None


class LeadResponse(LeadBase):
    """Schema de resposta com todos os campos do lead."""

    id: uuid.UUID
    status: LeadStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
