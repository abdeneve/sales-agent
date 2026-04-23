"""Testes unitários para o cliente EvolutionAPI.

Usa `respx` para mockar chamadas httpx sem conexão de rede real.
"""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from app.integrations.evolution import EvolutionClient

# Cliente configurado com URL de teste (não bate em produção)
_BASE_URL = "http://evolution-test"
_INSTANCE = "test_instance"
_API_KEY = "test-api-key"


@pytest.fixture()
def client() -> EvolutionClient:
    """Cliente EvolutionAPI com config de teste."""
    return EvolutionClient(
        base_url=_BASE_URL,
        instance=_INSTANCE,
        api_key=_API_KEY,
    )


# ---------------------------------------------------------------------------
# Testes: send_text_message
# ---------------------------------------------------------------------------


class TestSendTextMessage:
    """Testes para EvolutionClient.send_text_message."""

    @respx.mock
    async def test_envia_mensagem_com_sucesso_200(self, client: EvolutionClient) -> None:
        """Retorna True quando a API responde 200."""
        route = respx.post(
            f"{_BASE_URL}/message/sendText/{_INSTANCE}"
        ).mock(return_value=Response(200, json={"status": "ok"}))

        result = await client.send_text_message("5511999999999", "Olá!")

        assert result is True
        assert route.called

    @respx.mock
    async def test_envia_mensagem_com_sucesso_201(self, client: EvolutionClient) -> None:
        """Retorna True quando a API responde 201 (Created)."""
        respx.post(
            f"{_BASE_URL}/message/sendText/{_INSTANCE}"
        ).mock(return_value=Response(201, json={"status": "created"}))

        result = await client.send_text_message("5511999999999", "Olá!")

        assert result is True

    @respx.mock
    async def test_retorna_false_em_400(self, client: EvolutionClient) -> None:
        """Retorna False sem levantar exceção em resposta 4xx."""
        respx.post(
            f"{_BASE_URL}/message/sendText/{_INSTANCE}"
        ).mock(return_value=Response(400, json={"error": "bad request"}))

        result = await client.send_text_message("5511999999999", "Olá!")

        assert result is False

    @respx.mock
    async def test_retorna_false_em_500(self, client: EvolutionClient) -> None:
        """Retorna False sem levantar exceção em resposta 5xx."""
        respx.post(
            f"{_BASE_URL}/message/sendText/{_INSTANCE}"
        ).mock(return_value=Response(500, json={"error": "internal server error"}))

        result = await client.send_text_message("5511999999999", "Olá!")

        assert result is False

    @respx.mock
    async def test_envia_payload_correto(self, client: EvolutionClient) -> None:
        """Verifica que phone e text são enviados no body correto."""
        route = respx.post(
            f"{_BASE_URL}/message/sendText/{_INSTANCE}"
        ).mock(return_value=Response(200, json={}))

        await client.send_text_message("5511999999999", "Mensagem de teste")

        request = route.calls[0].request
        import json
        body = json.loads(request.content)
        assert body["number"] == "5511999999999"
        assert body["text"] == "Mensagem de teste"

    @respx.mock
    async def test_envia_header_apikey(self, client: EvolutionClient) -> None:
        """Verifica que o header apikey é enviado corretamente."""
        route = respx.post(
            f"{_BASE_URL}/message/sendText/{_INSTANCE}"
        ).mock(return_value=Response(200, json={}))

        await client.send_text_message("5511999999999", "Teste")

        request = route.calls[0].request
        assert request.headers["apikey"] == _API_KEY

    @respx.mock
    async def test_retry_em_timeout_e_retorna_false(
        self, client: EvolutionClient
    ) -> None:
        """Em caso de timeout, tenta novamente e retorna False após esgotamento."""
        import httpx

        respx.post(
            f"{_BASE_URL}/message/sendText/{_INSTANCE}"
        ).mock(side_effect=httpx.TimeoutException("timeout"))

        result = await client.send_text_message("5511999999999", "Olá!")

        assert result is False

    @respx.mock
    async def test_retorna_false_em_erro_de_conexao(
        self, client: EvolutionClient
    ) -> None:
        """Em caso de erro de conexão, retorna False sem levantar exceção."""
        import httpx

        respx.post(
            f"{_BASE_URL}/message/sendText/{_INSTANCE}"
        ).mock(side_effect=httpx.ConnectError("connection refused"))

        result = await client.send_text_message("5511999999999", "Olá!")

        assert result is False
