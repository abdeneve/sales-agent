"""Google Calendar helper (Mock).

Simula a criação de eventos no Google Calendar.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from app.config import settings

logger = logging.getLogger(__name__)


class CalendarClient:
    """Cliente mock para o Google Calendar."""

    def __init__(self, api_key: str = settings.calendar_api_key):
        self.api_key = api_key

    async def schedule_meeting(
        self, lead_phone: str, segment: str, date_time: datetime | None = None
    ) -> dict[str, str]:
        """Simula o agendamento de uma reunião.

        Args:
            lead_phone: Telefone do lead.
            segment: Segmento do lead.
            date_time: Data e hora desejada (opcional).

        Returns:
            Dict com informações do evento agendado.
        """
        # Simula a escolha de um horário se não fornecido (ex: amanhã às 10:00)
        if not date_time:
            date_time = datetime.now() + timedelta(days=1)
            date_time = date_time.replace(hour=10, minute=0, second=0, microsecond=0)

        end_time = date_time + timedelta(minutes=30)

        logger.info(
            "Agendando reunião para lead %s (Segmento: %s) em %s",
            lead_phone,
            segment,
            date_time.isoformat(),
        )

        # Simulação de delay de rede
        # import asyncio
        # await asyncio.sleep(0.5)

        return {
            "status": "scheduled",
            "event_id": f"evt_{lead_phone}_{int(date_time.timestamp())}",
            "summary": f"Reunião de Vendas - {segment}",
            "start": date_time.isoformat(),
            "end": end_time.isoformat(),
            "link": f"https://meet.google.com/mock-{lead_phone}",
        }
