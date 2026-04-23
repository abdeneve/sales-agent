"""Fixtures compartilhadas para todos os testes.

Usa banco de dados SQLite em memória para testes rápidos e isolados,
sem precisar de PostgreSQL rodando.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.dependencies import get_db_session
from app.main import app

# ======================================================
# Engine de teste: SQLite assíncrono em memória
# ======================================================

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session", autouse=True)
async def create_tables() -> None:
    """Cria todas as tabelas antes dos testes e remove no final."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def db_session() -> AsyncSession:
    """Sessão de banco de dados isolada por teste (rollback automático)."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture()
async def client(db_session: AsyncSession) -> AsyncClient:
    """Cliente HTTP assíncrono com banco de dados de teste injetado."""

    async def override_get_db_session() -> AsyncSession:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
