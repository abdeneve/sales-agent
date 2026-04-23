"""Router principal da API.

Agrega todos os sub-routers dos módulos.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api import webhooks, ws

router = APIRouter()

# Webhooks (Phase 2)
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

# WebSockets (Phase 4)
router.include_router(ws.router, tags=["websockets"])

# Sub-routers das fases seguintes serão adicionados aqui:
# from app.api import conversations, leads, dashboard
# router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
# router.include_router(leads.router, prefix="/leads", tags=["leads"])
# router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
