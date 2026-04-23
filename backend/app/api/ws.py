"""Gerenciador de conexões WebSocket para o Dashboard em tempo real.

Permite que os consultores recebam atualizações sobre leads, 
intervenções e SLA sem necessidade de polling.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Gerencia as conexões WebSocket ativas."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Aceita uma nova conexão."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Nova conexão WebSocket estabelecida. Total: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove uma conexão encerrada."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("Conexão WebSocket encerrada. Total: %d", len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Envia uma mensagem para todos os clientes conectados."""
        if not self.active_connections:
            return

        logger.debug("Broadcasting message: %s", message)
        disconnected = []
        
        # Fazemos o dump para JSON uma única vez
        message_str = json.dumps(message)
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as exc:
                logger.error("Erro ao enviar mensagem via WebSocket: %s", exc)
                disconnected.append(connection)

        # Limpar conexões que falharam
        for conn in disconnected:
            self.disconnect(conn)


# Instância global do manager
manager = ConnectionManager()


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket) -> None:
    """Endpoint WebSocket para o dashboard dos consultores."""
    await manager.connect(websocket)
    try:
        while True:
            # Mantém a conexão aberta e aguarda mensagens (pings, etc)
            # Por enquanto, o dashboard apenas recebe (unidirecional do backend)
            data = await websocket.receive_text()
            logger.debug("Recebido via WS: %s", data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.exception("Erro inesperado no WebSocket: %s", exc)
        manager.disconnect(websocket)
