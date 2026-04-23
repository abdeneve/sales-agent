# Plano de Implementação: Agente de Atendimento e Vendas (MRR)

Este plano delineia os passos técnicos para construir o sistema completo baseado no Monolito Modular + Real-Time First, usando a stack especificada no PRD (Python/FastAPI, LangGraph, React/Vite, PostgreSQL, Redis, EvolutionAPI).

## Resumo do Objetivo

Implementar a arquitetura completa para que o agente possa receber mensagens via WhatsApp, qualificar leads com GPT-4o-mini (baseado em 3 perguntas-chave), agendar reuniões (Google Calendar), salvar dados de CRM (Planilha Excel via MCP) e exibir todo o SLA em tempo real no Dashboard dos Consultores (via WebSocket), incluindo uma "Fila de Intervenção" para falhas da IA.

## User Review Required

> [!IMPORTANT]
> **Aprovação do Plano:** Por favor, revise a ordem de implementação abaixo e me confirme se podemos começar a executar as tarefas ou se você gostaria de alterar a prioridade de algum módulo.

## Proposed Changes

Abaixo está o detalhamento de módulos, diretórios e arquivos que precisaremos construir e configurar. Separamos o projeto de forma incremental.

---

### Phase 1: Setup da Infraestrutura e Base do Backend

Configurar o alicerce onde o agente vai rodar.

#### [NEW] `docker-compose.yml`
- Definir serviços: `postgres`, `redis`, `evolution-api`.

#### [NEW] `backend/pyproject.toml`
- Definir dependências via `uv` (fastapi, langgraph, langchain-openai, sqlalchemy, pydantic, redis, websockets, pytest, ruff).

#### [NEW] `backend/app/db/session.py` e `backend/app/models/`
- Configurar SQLAlchemy assíncrono.
- Modelos: `Lead` (status, info), `Conversation` (histórico e status na Fila de Intervenção).

#### [NEW] `backend/app/main.py`
- Setup do FastAPI com rotas básicas.

---

### Phase 2: Core do Agente IA (LangGraph) e EvolutionAPI

Construir o "cérebro" do sistema e conectá-lo ao WhatsApp.

#### [NEW] `backend/app/agent/state.py`
- TypedDict com `AgentState` e histórico de mensagens.

#### [NEW] `backend/app/agent/nodes.py` e `backend/app/agent/graph.py`
- **Nós necessários:**
  - `classify_intent`: Avaliar a intenção (Dúvida vs Agendamento).
  - `rag_qa`: Consulta de RAG no PDF fake (para tirar dúvidas).
  - `qualify_lead`: Aplicar as 3 perguntas de qualificação.
  - `handoff_intervention`: Encaminhar lead para a Fila de Intervenção do consultor.
- **Modelo:** GPT-4o-mini configurado.

#### [NEW] `backend/app/api/webhooks.py`
- Endpoint webhook (recebendo msgs do EvolutionAPI).
- Integração que dispara a chamada do grafo do LangGraph e salva o estado.

---

### Phase 3: Integração Remote MCP (Planilha Excel e Calendar)

Acrescentar as actions externas do fluxo usando a especificação MCP.

#### [NEW] `backend/app/integrations/mcp_client.py`
- Configuração de clientes MCP.
- Client para Excel (Mock/Simulação de escrita no arquivo/Planilha Google via API).
- Client para Google Calendar (Mock/Simulação de evento).

#### [MODIFY] `backend/app/agent/nodes.py`
- Atualizar o agente para chamar o MCP e persistir o agendamento e anotação de CRM na planilha via tools atreladas ao LLM.

---

### Phase 4: Observabilidade e Tempo Real (WebSockets)

O coração do monitoramento SLA para os consultores.

#### [NEW] `backend/app/services/sla_monitor.py`
- Gerenciador de SLA interno para monitorar o timing de <2 mins.

#### [NEW] `backend/app/api/ws.py`
- Connection Manager de WebSockets que recebe eventos do LangGraph.
- Broadcaster para disparar eventos: "Lead Recebido", "Lead Qualificado", "Aguardando Intervenção".

---

### Phase 5: Dashboard Frontend (Centro de Operações)

A interface que os 6 consultores usarão 24/7.

#### [NEW] `frontend/package.json` e `frontend/vite.config.ts`
- Setup do Vite, React, Zustand e CSS puro.

#### [NEW] `frontend/src/stores/dashboardStore.ts`
- Gerenciamento de estado global com Zustand. Conexão e parser das mensagens de WebSocket vindas do backend.

#### [NEW] `frontend/src/components/SLAIndicator.tsx` e `frontend/src/components/InterventionQueue.tsx`
- **SLA Indicator:** Cronômetro colorido (Verde <1m, Amarelo <2m, Vermelho >2m).
- **Intervention Queue:** Tabela/Lista visual de leads cuja conversação sofreu fallback da IA, exigindo clique do consultor para assumir (via API REST).

#### [NEW] `frontend/src/pages/Dashboard.tsx`
- Unificação dos componentes na view principal do Centro de Operações.

---

## Verification Plan

### Automated Tests
- Testes unitários com `pytest` e mock de EvolutionAPI no webhook.
- Testar a classificação de intenção do agente.
- Testar componentes React com Vitest (ex: SLA Indicator fica vermelho após 2 min).

### Manual Verification
1. Rodar `docker compose up --build`.
2. Acessar o dashboard frontend.
3. Simular envio de um JSON (padrão EvolutionAPI) de "Lead Dando Oi".
4. Visualizar evento aparecer no Dashboard e SLA rodando.
5. Fazer o Lead travar de propósito para cair na "Fila de Intervenção".
6. O consultor no Dashboard clica para assumir a conversa (mudar o status do Lead).
