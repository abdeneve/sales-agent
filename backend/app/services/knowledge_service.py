"""Serviço de busca na base de conhecimento (RAG).

Nesta versão MVP, lemos um arquivo de texto local e o usamos como contexto.
Em versões futuras, pode ser substituído por um banco de vetores (ex: ChromaDB, Pinecone).
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Caminho para o arquivo de KB
KB_FILE_PATH = Path(__file__).parent.parent / "agent" / "knowledge_base.txt"


class KnowledgeService:
    """Serviço para gerenciar e consultar a base de conhecimento."""

    def __init__(self, file_path: Path = KB_FILE_PATH) -> None:
        self.file_path = file_path
        self._cached_content: str | None = None

    def get_context(self) -> str:
        """Retorna o conteúdo da base de conhecimento.

        Faz cache em memória para evitar I/O repetitivo.
        """
        if self._cached_content is not None:
            return self._cached_content

        try:
            if self.file_path.exists():
                self._cached_content = self.file_path.read_text(encoding="utf-8")
                return self._cached_content
            
            logger.warning("Arquivo de KB não encontrado em: %s", self.file_path)
            return "Informação não disponível no momento."
        except Exception:
            logger.exception("Erro ao ler arquivo de KB")
            return "Erro ao carregar base de conhecimento."

    def clear_cache(self) -> None:
        """Limpa o cache em memória (útil se o arquivo mudar)."""
        self._cached_content = None
