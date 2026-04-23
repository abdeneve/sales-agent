"""Módulo do agente LangGraph.

Exporta a factory `build_agent_graph` e o tipo `AgentState`.
"""

from __future__ import annotations

from app.agent.graph import build_agent_graph
from app.agent.state import AgentState

__all__ = ["AgentState", "build_agent_graph"]
