"""Testes de integração: health check e rotas base da API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Health check deve retornar status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "environment" in body


@pytest.mark.asyncio
async def test_docs_available_in_non_production(client: AsyncClient) -> None:
    """Docs Swagger devem estar disponíveis em desenvolvimento."""
    response = await client.get("/docs")
    # Em testing (não-produção) a UI do Swagger deve carregar
    assert response.status_code == 200
