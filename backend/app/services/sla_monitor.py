"""Serviço de monitoramento de SLA (Service Level Agreement).

Garante que o tempo de resposta do agente ou consultor seja inferior a 2 minutos,
conforme definido nos requisitos de negócio.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.api.ws import manager
from app.config import settings

logger = logging.getLogger(__name__)

SLA_THRESHOLD_SECONDS = settings.sla_critical_seconds


class SLAMonitor:
    """Monitora o SLA de conversas e dispara eventos em tempo real."""

    @staticmethod
    async def track_lead_received(lead_id: str, phone: str, message: str) -> None:
        """Dispara evento de que um novo lead enviou mensagem."""
        event = {
            "type": "LEAD_RECEIVED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "lead_id": lead_id,
                "phone": phone,
                "message": message,
                "sla_limit": SLA_THRESHOLD_SECONDS,
            }
        }
        await manager.broadcast(event)

    @staticmethod
    async def track_agent_responded(lead_id: str, response: str) -> None:
        """Dispara evento de que o agente respondeu, cumprindo o SLA inicial."""
        event = {
            "type": "AGENT_RESPONDED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "lead_id": lead_id,
                "response": response,
            }
        }
        await manager.broadcast(event)

    @staticmethod
    async def track_intervention_required(lead_id: str, reason: str) -> None:
        """Dispara evento de que o lead caiu na fila de intervenção."""
        event = {
            "type": "INTERVENTION_REQUIRED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "lead_id": lead_id,
                "reason": reason,
                "priority": "high"
            }
        }
        await manager.broadcast(event)

    @staticmethod
    async def track_lead_qualified(lead_id: str, segment: str | None = None) -> None:
        """Dispara evento de que o lead foi qualificado com sucesso."""
        event = {
            "type": "LEAD_QUALIFIED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "lead_id": lead_id,
                "segment": segment,
            }
        }
        await manager.broadcast(event)

    @staticmethod
    def calculate_sla_status(last_message_at: datetime) -> dict[str, Any]:
        """Calcula o status atual do SLA para uma conversa.
        
        Retorna:
            Dict com 'elapsed', 'remaining' e 'status' (normal, warning, breached).
        """
        now = datetime.now(timezone.utc)
        if last_message_at.tzinfo is None:
            last_message_at = last_message_at.replace(tzinfo=timezone.utc)
            
        elapsed = (now - last_message_at).total_seconds()
        remaining = max(0, settings.sla_critical_seconds - elapsed)
        
        status = "normal"
        if elapsed >= settings.sla_critical_seconds:
            status = "breached"
        elif elapsed >= settings.sla_warning_seconds:
            status = "warning"
            
        return {
            "elapsed": int(elapsed),
            "remaining": int(remaining),
            "status": status,
            "threshold": settings.sla_critical_seconds,
            "warning_threshold": settings.sla_warning_seconds
        }
