"""Cliente HTTP para a EvolutionAPI.

Responsável por enviar mensagens de volta ao lead via WhatsApp.
Nunca propaga exceções para cima — falhas são logadas e o sistema continua.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Timeout padrão para chamadas à EvolutionAPI
_TIMEOUT_SECONDS = 10.0
# Número máximo de retentativas em caso de timeout
_MAX_RETRIES = 1


class EvolutionClient:
    """Cliente assíncrono para a EvolutionAPI.

    Uso:
        client = EvolutionClient()
        await client.send_text_message(phone="5511999999999", text="Olá!")

    Attributes:
        base_url: URL base da instância EvolutionAPI.
        instance: Nome da instância WhatsApp configurada.
        api_key: Chave de autenticação da API.
    """

    def __init__(
        self,
        base_url: str | None = None,
        instance: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.evolution_api_url).rstrip("/")
        self.instance = instance or settings.evolution_instance_name
        self.api_key = api_key or settings.evolution_api_key

    def _headers(self) -> dict[str, str]:
        """Cabeçalhos padrão para todas as requisições."""
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }

    async def create_instance(self) -> bool:
        """Cria a instância na EvolutionAPI se ela não existir.

        Note: Requer que o nome da instância e a API key global estejam configurados.
        """
        url = f"{self.base_url}/instance/create"
        payload = {
            "instanceName": self.instance,
            "token": self.api_key,
            "number": "",
            "qrcode": True,
        }
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                response = await client.post(url, json=payload, headers=self._headers())
            
            if response.status_code in (200, 201):
                logger.info("Instância '%s' criada com sucesso", self.instance)
                return True
            
            logger.warning("Falha ao criar instância: %s", response.text)
            return False
        except Exception:
            logger.exception("Erro ao tentar criar instância")
            return False

    async def set_webhook(self, webhook_url: str) -> bool:
        """Configura a URL do webhook para a instância atual.

        Args:
            webhook_url: URL completa que receberá os eventos.
        """
        url = f"{self.base_url}/webhook/set/{self.instance}"
        payload = {
            "enabled": True,
            "url": webhook_url,
            "webhook_by_events": False,
            "events": [
                "MESSAGES_UPSERT",
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                response = await client.post(url, json=payload, headers=self._headers())
            
            if response.status_code in (200, 201):
                logger.info("Webhook configurado para: %s", webhook_url)
                return True
            
            logger.warning("Falha ao configurar webhook: %s", response.text)
            return False
        except Exception:
            logger.exception("Erro ao configurar webhook")
            return False

    async def send_text_message(self, phone: str, text: str) -> bool:
        """Envia uma mensagem de texto para o lead via WhatsApp.

        Realiza uma retentativa em caso de timeout. Em caso de falha
        definitiva, loga o erro e retorna False sem propagar a exceção.

        Args:
            phone: Número de telefone do destinatário (apenas dígitos,
                   ex: "5511999999999").
            text: Texto da mensagem a ser enviada.

        Returns:
            True se a mensagem foi enviada com sucesso, False caso contrário.
        """
        # Garantir que o número termine com @s.whatsapp.net se não tiver
        if "@" not in phone:
            clean_phone = "".join(filter(str.isdigit, phone))
            recipient = clean_phone
        else:
            recipient = phone

        url = f"{self.base_url}/message/sendText/{self.instance}"
        payload: dict[str, Any] = {
            "number": recipient,
            "text": text,
        }

        for attempt in range(1 + _MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                    response = await client.post(url, json=payload, headers=self._headers())

                if response.status_code in (200, 201):
                    logger.info(
                        "Mensagem enviada com sucesso para %s (status=%d)",
                        phone,
                        response.status_code,
                    )
                    return True

                logger.warning(
                    "EvolutionAPI retornou status %d para phone=%s body=%.200s",
                    response.status_code,
                    phone,
                    response.text,
                )
                return False

            except httpx.TimeoutException:
                if attempt < _MAX_RETRIES:
                    logger.warning(
                        "Timeout ao enviar mensagem para %s (tentativa %d/%d) — retentando",
                        phone,
                        attempt + 1,
                        1 + _MAX_RETRIES,
                    )
                    continue
                logger.error(
                    "Timeout definitivo ao enviar mensagem para %s após %d tentativas",
                    phone,
                    1 + _MAX_RETRIES,
                )
                return False

            except httpx.HTTPError:
                logger.exception(
                    "Erro HTTP ao enviar mensagem para %s",
                    phone,
                )
                return False

        return False  # pragma: no cover
