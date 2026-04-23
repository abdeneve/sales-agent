"""FastAPI application factory com lifespan e rotas base.

Ponto de entrada: `uvicorn app.main:app --reload`
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.config import settings
from app.db.session import engine

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(application: FastAPI) -> Any:
    """Gerencia o ciclo de vida da aplicação (startup / shutdown)."""
    logger.info("🚀 Iniciando Agente de Atendimento e Vendas [%s]", settings.environment)

    # Startup: testar conexão com o banco
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("✅ Conexão com o banco de dados estabelecida")
    except Exception as exc:
        logger.warning("⚠️  Banco de dados não disponível: %s", exc)

    yield

    # Shutdown
    logger.info("🛑 Encerrando aplicação...")
    await engine.dispose()
    logger.info("✅ Engine do banco de dados encerrada")


def create_app() -> FastAPI:
    """Factory que cria e configura a instância FastAPI."""
    application = FastAPI(
        title="Agente de Atendimento e Vendas",
        description=(
            "API do agente de atendimento inbound para qualificação de leads e "
            "agendamento de reuniões via WhatsApp. Dashboard em tempo real para consultores."
        ),
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # CORS — apenas para desenvolvimento; em produção restringir origins
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else ["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Registrar routers
    application.include_router(router, prefix="/api/v1")

    return application


app = create_app()


@app.get("/health", tags=["infra"], summary="Health check")
async def health_check() -> dict[str, str]:
    """Endpoint de health check para balanceadores de carga e Docker healthcheck."""
    return {"status": "ok", "environment": settings.environment}
