"""Remote MCP client (CRM).

Simula a integração com uma planilha Excel via MCP.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class MCPClient:
    """Cliente mock para o servidor MCP de Excel."""

    def __init__(self, sheet_path: str = settings.excel_sheet_path):
        self.sheet_path = sheet_path
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Garante que o diretório de dados existe."""
        os.makedirs(os.path.dirname(self.sheet_path), exist_ok=True)

    async def update_lead_crm(self, lead_data: dict[str, Any]) -> bool:
        """Simula a escrita de dados do lead na planilha de CRM.

        Args:
            lead_data: Dicionário com as informações do lead (segment, budget, timeline, etc).

        Returns:
            True se a operação foi bem-sucedida.
        """
        phone = lead_data.get("phone", "unknown")
        segment = lead_data.get("segment", "N/A")
        budget = lead_data.get("budget", "N/A")
        timeline = lead_data.get("timeline", "N/A")

        logger.info(
            "Enviando dados para o CRM MCP (Planilha: %s): Lead=%s, Segment=%s, Budget=%s",
            self.sheet_path,
            phone,
            segment,
            budget,
        )

        # Aqui simulamos o salvamento em um arquivo CSV real como "mock" de Excel
        try:
            line = f"{phone},{segment},{budget},{timeline}\n"
            with open(self.sheet_path.replace(".xlsx", ".csv"), "a", encoding="utf-8") as f:
                f.write(line)
            return True
        except Exception:
            logger.exception("Falha ao salvar no CRM MCP")
            return False
