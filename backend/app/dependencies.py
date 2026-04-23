"""Injeção de dependências do FastAPI.

Centraliza providers para DB session, settings, etc.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, settings
from app.db.session import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provider de sessão assíncrona do banco de dados.

    Uso:
        @router.get("/exemplo")
        async def handler(db: DBSession) -> ...:
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_settings() -> Settings:
    """Provider das configurações da aplicação."""
    return settings


# Tipos anotados para uso nos handlers com `Depends`
DBSession = Annotated[AsyncSession, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]
