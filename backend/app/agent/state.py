"""Estado tipado do agente LangGraph.

O AgentState é o único objeto que trafega entre os nós do grafo.
Cada nó recebe o estado completo e retorna um dict com os campos a atualizar.
"""

from __future__ import annotations

import uuid
from typing import Literal, TypedDict


class AgentState(TypedDict, total=False):
    """Estado compartilhado entre todos os nós do grafo.

    Campos:
        messages: Histórico de mensagens no formato {role, content}.
        lead_phone: Número de telefone do lead (sem @s.whatsapp.net).
        conversation_id: UUID da conversa no banco de dados.
        user_intent: Intenção detectada pelo classificador.
        qualification_step: Passo atual da qualificação (0 = início).
        is_qualified: True quando as 3 perguntas foram respondidas.
        segment: Segmento de atuação da empresa do lead.
        budget: Orçamento estimado para implementação.
        timeline: Prazo estimado para implementação.
        should_handoff: True quando o agente não consegue processar.
        agent_response: Resposta que será enviada ao lead via WhatsApp.
    """

    messages: list[dict[str, str]]
    lead_phone: str
    conversation_id: uuid.UUID | None
    user_intent: Literal["scheduling", "support", "unknown"] | None
    qualification_step: int
    is_qualified: bool
    segment: str | None
    budget: str | None
    timeline: str | None
    should_handoff: bool
    meeting_scheduled: bool
    agent_response: str | None
