"""Testes unitários para o AgentState.

Verifica que o TypedDict aceita os campos corretos e que os valores
padrão/opcionais funcionam como esperado.
"""

from __future__ import annotations

import uuid

import pytest

from app.agent.state import AgentState


def test_agent_state_minimal() -> None:
    """AgentState pode ser criado com campos mínimos (total=False)."""
    state: AgentState = {
        "messages": [{"role": "user", "content": "Olá"}],
        "lead_phone": "5511999999999",
    }
    assert state["lead_phone"] == "5511999999999"
    assert len(state["messages"]) == 1


def test_agent_state_full() -> None:
    """AgentState aceita todos os campos opcionais."""
    conv_id = uuid.uuid4()
    state: AgentState = {
        "messages": [{"role": "user", "content": "Quero agendar"}],
        "lead_phone": "5511999999999",
        "conversation_id": conv_id,
        "user_intent": "scheduling",
        "qualification_step": 1,
        "is_qualified": False,
        "segment": None,
        "budget": None,
        "timeline": None,
        "should_handoff": False,
        "agent_response": None,
    }
    assert state["user_intent"] == "scheduling"
    assert state["conversation_id"] == conv_id


def test_agent_state_intent_values() -> None:
    """Valores válidos de user_intent são aceitos."""
    for intent in ("scheduling", "support", "unknown"):
        state: AgentState = {
            "messages": [],
            "lead_phone": "5511999999999",
            "user_intent": intent,  # type: ignore[typeddict-item]
        }
        assert state["user_intent"] == intent


@pytest.mark.parametrize("step", [0, 1, 2, 3])
def test_agent_state_qualification_steps(step: int) -> None:
    """qualification_step aceita valores inteiros de 0 a 3."""
    state: AgentState = {
        "messages": [],
        "lead_phone": "5511999999999",
        "qualification_step": step,
    }
    assert state["qualification_step"] == step
