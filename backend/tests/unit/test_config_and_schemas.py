"""Testes unitários: configurações e schemas base."""

from __future__ import annotations

import pytest

from app.config import settings
from app.schemas.webhook import EvolutionWebhookPayload


def test_settings_carrega_corretamente() -> None:
    """Settings deve carregar sem erros com valores padrão."""
    assert settings.environment in ("development", "testing", "production")
    assert settings.sla_warning_seconds == 60
    assert settings.sla_critical_seconds == 120


def test_settings_is_testing() -> None:
    """Ambiente de teste deve estar em development ou testing."""
    assert not settings.is_production


def test_evolution_webhook_payload_extrai_telefone() -> None:
    """Payload da EvolutionAPI deve extrair o número do remetente corretamente."""
    payload = EvolutionWebhookPayload(
        event="messages.upsert",
        instance="sales_agent",
        data={
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "ABC123",
            },
            "message": {"conversation": "Olá, quero saber mais sobre os serviços!"},
        },
    )
    assert payload.sender_phone == "5511999999999"
    assert payload.message_content is not None
    assert payload.message_content.text == "Olá, quero saber mais sobre os serviços!"


def test_evolution_webhook_payload_ignora_mensagens_proprias() -> None:
    """Mensagens enviadas pelo agente (fromMe=True) devem retornar sender_phone None."""
    payload = EvolutionWebhookPayload(
        event="messages.upsert",
        instance="sales_agent",
        data={
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": True,
                "id": "XYZ789",
            },
            "message": {"conversation": "Mensagem do agente"},
        },
    )
    assert payload.sender_phone is None
