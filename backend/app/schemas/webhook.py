"""Schemas Pydantic para payload do webhook da EvolutionAPI.

Estrutura baseada na documentação oficial da EvolutionAPI v2.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvolutionMessageKey(BaseModel):
    """Chave única da mensagem no WhatsApp."""

    remote_jid: str = Field(alias="remoteJid", description="JID do remetente (ex: 5511999999999@s.whatsapp.net)")
    from_me: bool = Field(alias="fromMe", description="True se a mensagem foi enviada pelo agente")
    id: str = Field(description="ID único da mensagem")

    model_config = {"populate_by_name": True}


class EvolutionMessageContent(BaseModel):
    """Conteúdo da mensagem recebida."""

    conversation: str | None = Field(default=None, description="Texto da mensagem")
    image_message: dict | None = Field(default=None, alias="imageMessage")
    audio_message: dict | None = Field(default=None, alias="audioMessage")

    model_config = {"populate_by_name": True}

    @property
    def text(self) -> str:
        """Retorna o texto da mensagem (simplificado para MVP)."""
        return self.conversation or "[mensagem de mídia]"


class EvolutionWebhookPayload(BaseModel):
    """Payload completo recebido do webhook da EvolutionAPI."""

    event: str = Field(description="Tipo de evento (ex: messages.upsert)")
    instance: str = Field(description="Nome da instância WhatsApp")
    data: dict = Field(description="Dados brutos do evento")

    @property
    def message_key(self) -> EvolutionMessageKey | None:
        """Extrai a chave da mensagem do payload."""
        key_data = self.data.get("key")
        if key_data:
            return EvolutionMessageKey(**key_data)
        return None

    @property
    def message_content(self) -> EvolutionMessageContent | None:
        """Extrai o conteúdo da mensagem do payload."""
        content_data = self.data.get("message")
        if content_data:
            return EvolutionMessageContent(**content_data)
        return None

    @property
    def sender_phone(self) -> str | None:
        """Extrai o número de telefone do remetente (sem @s.whatsapp.net)."""
        key = self.message_key
        if key and not key.from_me:
            return key.remote_jid.split("@")[0]
        return None
