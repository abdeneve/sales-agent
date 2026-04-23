"""Configurações centralizadas via Pydantic BaseSettings.

Nunca use os.getenv() diretamente. Importe `settings` deste módulo.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- App ---
    environment: str = Field(default="development", description="development | production | testing")
    secret_key: str = Field(default="changeme", description="Chave secreta para JWT")
    log_level: str = Field(default="INFO", description="DEBUG | INFO | WARNING | ERROR")

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://sales_agent:sales_agent_secret@localhost:5432/sales_agent_db",
        description="URL de conexão com o PostgreSQL (asyncpg)",
    )

    # --- Redis ---
    redis_url: str = Field(
        default="redis://:redis_secret@localhost:6379",
        description="URL de conexão com o Redis",
    )

    # --- OpenAI ---
    openai_api_key: str = Field(default="", description="Chave da API OpenAI")
    openai_model: str = Field(default="gpt-4o-mini", description="Modelo OpenAI padrão")

    # --- EvolutionAPI ---
    evolution_api_url: str = Field(
        default="http://localhost:8080",
        description="URL base da EvolutionAPI",
    )
    evolution_api_key: str = Field(
        default="",
        description="API Key da EvolutionAPI",
    )
    evolution_instance_name: str = Field(
        default="sales_agent",
        description="Nome da instância WhatsApp na EvolutionAPI",
    )

    # --- SLA ---
    sla_warning_seconds: int = Field(default=60, description="SLA amarelo (segundos)")
    sla_critical_seconds: int = Field(default=120, description="SLA vermelho (segundos)")

    # --- MCP / Integrations ---
    excel_sheet_path: str = Field(default="data/leads.xlsx", description="Caminho para a planilha de CRM")
    calendar_api_key: str = Field(default="mock-key", description="Chave mock para Google Calendar")

    @property
    def is_production(self) -> bool:
        """Retorna True se o ambiente é produção."""
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        """Retorna True se o ambiente é de testes."""
        return self.environment == "testing"


settings = Settings()
