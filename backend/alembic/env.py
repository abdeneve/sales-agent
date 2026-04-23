"""Alembic env.py — configurado para uso assíncrono com asyncpg.

Lê a DATABASE_URL via Pydantic Settings (app/config.py).
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Importar Base e todos os modelos para auto-geração de migrations
from app.db.base import Base
import app.models  # noqa: F401 — garante que todos os modelos são registrados na Base

from app.config import settings

# Configuração de logging do Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata para --autogenerate
target_metadata = Base.metadata

# Injetar a URL do banco via Settings (nunca hardcodado)
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """Rodar migrations em modo 'offline' (sem conexão real ao DB)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Executar as migrations numa conexão já estabelecida."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Criar engine assíncrona e rodar migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Ponto de entrada para modo online (com conexão assíncrona)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
