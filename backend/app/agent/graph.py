"""Construção e compilação do grafo LangGraph do agente.

Exporta ``build_agent_graph()`` que retorna um grafo compilado pronto para
ser invocado com ``await graph.ainvoke(state)``.

Fluxo principal:
    START
      └─► classify_intent
            ├─ "scheduling" ──► qualify_lead ──► END
            ├─ "support"    ──► rag_qa        ──► END
            └─ "unknown"    ──► handoff_intervention ──► END
"""

from __future__ import annotations

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    classify_intent,
    handoff_intervention,
    qualify_lead,
    rag_qa,
    schedule_and_crm,
)
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


def _route_after_classify(
    state: AgentState,
) -> Literal["qualify_lead", "rag_qa", "handoff_intervention"]:
    """Roteamento condicional após classify_intent.

    Lê ``state["user_intent"]`` e retorna o nome do próximo nó.
    """
    intent = state.get("user_intent", "unknown")
    if intent == "scheduling":
        return "qualify_lead"
    if intent == "support":
        return "rag_qa"
    return "handoff_intervention"


def _route_after_qualify(state: AgentState) -> Literal["schedule_and_crm", "__end__"]:
    """Roteamento condicional após qualify_lead.

    Se qualificado, vai para o agendamento. Caso contrário, encerra e aguarda próxima msg.
    """
    if state.get("is_qualified"):
        return "schedule_and_crm"
    return END


def build_agent_graph() -> StateGraph:
    """Monta e compila o grafo do agente.

    Returns:
        Grafo LangGraph compilado e pronto para invocação.
    """
    graph = StateGraph(AgentState)

    # Registrar nós
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("qualify_lead", qualify_lead)
    graph.add_node("rag_qa", rag_qa)
    graph.add_node("handoff_intervention", handoff_intervention)
    graph.add_node("schedule_and_crm", schedule_and_crm)

    # Edges
    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        _route_after_classify,
        {
            "qualify_lead": "qualify_lead",
            "rag_qa": "rag_qa",
            "handoff_intervention": "handoff_intervention",
        },
    )
    graph.add_conditional_edges(
        "qualify_lead",
        _route_after_qualify,
        {
            "schedule_and_crm": "schedule_and_crm",
            END: END,
        },
    )
    graph.add_edge("rag_qa", END)
    graph.add_edge("handoff_intervention", END)
    graph.add_edge("schedule_and_crm", END)

    compiled = graph.compile()
    logger.info("Grafo do agente compilado com sucesso")
    return compiled
