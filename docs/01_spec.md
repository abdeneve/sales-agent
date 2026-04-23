# Spec: Agente de Atendimento e Vendas (MRR)

## Suposições

> **Revise e corrija antes de prosseguir. Qualquer item errado aqui contamina todo o spec.**

1. Direção arquitetural: Variação 1+3 (Monolito Modular + Real-Time First)
2. Backend: Python 3.12+ / FastAPI / LangGraph
3. Frontend: React + Vite (SPA dashboard interno)
4. Banco de dados: PostgreSQL (leads, conversas, agendamentos)
5. Cache / Pub-Sub: Redis (real-time events + checkpointing LangGraph)
6. Canal: EvolutionAPI (WhatsApp) em Docker
7. Infraestrutura: Docker Compose — deploy local/VPS, **não é SaaS**
8. LLM Provider: OpenAI (GPT-4o)
9. Remote MCP Servers: CRM + Google Calendar
10. Autenticação: JWT simples ou API key (operação interna)

---

## Objetivo

### O que estamos construindo

Um **agente de atendimento e vendas inbound** que:

1. Recebe mensagens de leads via WhatsApp (EvolutionAPI webhook)
2. Analisa intenção e qualifica o lead usando LangGraph + LLM
3. Consulta base de conhecimento (RAG) para responder dúvidas técnicas
4. Aciona ferramentas externas via Remote MCP (CRM, Calendar)
5. Agenda reunião de vendas automaticamente em < 2 minutos
6. Exibe tudo em tempo real num dashboard para o consultor de vendas

### Quem usa

| Usuário | Canal | Interação |
|---|---|---|
| **Lead/Cliente** | WhatsApp | Conversa com o agente, é qualificado, tem reunião agendada |
| **Consultor de Vendas** | Dashboard web | Monitora SLA, intervém quando necessário, vê pipeline |

### Métricas de sucesso

| Métrica | Target |
|---|---|
| Speed to lead | < 2 minutos (webhook → reunião agendada) |
| Taxa de agendamento | Medida e visível no dashboard |
| Uptime do agente | > 99% durante horário comercial |
| Tempo de resposta do webhook | < 500ms (enfileirar e responder) |

---

## Tech Stack

| Camada | Tecnologia | Versão |
|---|---|---|
| Runtime | Python | >= 3.12 |
| Package Manager (back) | uv | latest |
| Framework API | FastAPI | >= 0.111 |
| Orquestração AI | LangGraph | >= 0.2.0 |
| LLM SDK | langchain-openai | >= 0.2.0 |
| Validação | Pydantic | >= 2.7 |
| ORM | SQLAlchemy | >= 2.0 |
| Migrations | Alembic | >= 1.13 |
| DB | PostgreSQL | 16 |
| Cache/PubSub | Redis | 7 |
| WhatsApp | EvolutionAPI | latest |
| Frontend | React | 18 |
| Build tool | Vite | 5 |
| State mgmt | Zustand | >= 4.5 |
| Real-time | native WebSocket | — |
| Infra | Docker Compose | v2 |
| Testes (back) | pytest + pytest-asyncio | >= 8.0 |
| Testes (front) | Vitest + Testing Library | >= 1.0 |
| Linting (back) | Ruff | >= 0.4 |
| Linting (front) | ESLint | >= 9 |
| Formatação (back) | Ruff formatter | >= 0.4 |

---

## Comandos

```bash
# === BACKEND ===
# Instalar dependências (com uv)
cd backend && uv sync

# Dev server (hot-reload)
cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Testes
cd backend && uv run pytest --cov=app --cov-report=term-missing

# Lint + format
cd backend && uv run ruff check . --fix
cd backend && uv run ruff format .

# Migrations
cd backend && uv run alembic upgrade head
cd backend && uv run alembic revision --autogenerate -m "descricao"

# === FRONTEND ===
# Instalar dependências
cd frontend && npm install

# Dev server
cd frontend && npm run dev

# Testes
cd frontend && npm test -- --coverage

# Lint
cd frontend && npm run lint -- --fix

# Build
cd frontend && npm run build

# === DOCKER (produção local) ===
docker compose up --build
docker compose down
docker compose logs -f backend
```

---

## Estrutura do Projeto

```text
sales_agent/
├── docs/
│   ├── spec.md                   → Este documento (fonte da verdade)
│   └── ideas/                    → Documentos de ideação e refinamento
│
├── backend/
│   ├── pyproject.toml            → Dependências e config (uv/ruff/pytest)
│   ├── alembic.ini               → Config do Alembic
│   ├── alembic/                  → Migrations do banco
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               → FastAPI app factory + lifespan
│   │   ├── config.py             → Settings com Pydantic BaseSettings
│   │   ├── dependencies.py       → Injeção de dependências FastAPI
│   │   │
│   │   ├── api/                  → Endpoints HTTP + WebSocket
│   │   │   ├── __init__.py
│   │   │   ├── router.py         → Router principal (agrega sub-routers)
│   │   │   ├── webhooks.py       → POST /webhooks/evolution (recebe msgs)
│   │   │   ├── conversations.py  → GET /conversations, GET /conversations/{id}
│   │   │   ├── leads.py          → CRUD de leads
│   │   │   ├── dashboard.py      → GET /dashboard/stats
│   │   │   └── ws.py             → WebSocket /ws/events (real-time)
│   │   │
│   │   ├── agent/                → LangGraph: grafo + nós
│   │   │   ├── __init__.py
│   │   │   ├── graph.py          → build_agent_graph() → CompiledGraph
│   │   │   ├── nodes.py          → analyze_intent, consult_kb, schedule, etc.
│   │   │   ├── state.py          → AgentState (TypedDict)
│   │   │   └── prompts.py        → System prompts centralizados
│   │   │
│   │   ├── integrations/         → Conectores externos
│   │   │   ├── __init__.py
│   │   │   ├── evolution.py      → EvolutionAPI client (enviar msgs)
│   │   │   ├── mcp_client.py     → Remote MCP client (CRM + Calendar)
│   │   │   └── calendar.py       → Google Calendar helper (fallback)
│   │   │
│   │   ├── models/               → SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── lead.py
│   │   │   ├── conversation.py
│   │   │   └── appointment.py
│   │   │
│   │   ├── schemas/              → Pydantic schemas (API I/O)
│   │   │   ├── __init__.py
│   │   │   ├── webhook.py
│   │   │   ├── lead.py
│   │   │   ├── conversation.py
│   │   │   └── dashboard.py
│   │   │
│   │   ├── services/             → Lógica de negócio
│   │   │   ├── __init__.py
│   │   │   ├── lead_service.py
│   │   │   ├── conversation_service.py
│   │   │   └── sla_monitor.py    → Monitora SLA < 2 min, emite alertas
│   │   │
│   │   └── db/                   → Database setup
│   │       ├── __init__.py
│   │       ├── session.py        → AsyncSession factory
│   │       └── base.py           → Base declarativa
│   │
│   └── tests/
│       ├── conftest.py           → Fixtures compartilhadas
│       ├── unit/
│       │   ├── test_nodes.py
│       │   ├── test_state.py
│       │   └── test_services.py
│       ├── integration/
│       │   ├── test_webhook.py
│       │   └── test_graph.py
│       └── factories.py          → Factory Boy para dados de teste
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx              → Entrypoint React
│   │   ├── App.tsx               → Router + Layout
│   │   ├── index.css             → Design tokens + reset
│   │   │
│   │   ├── components/           → Componentes reutilizáveis
│   │   │   ├── SLAIndicator.tsx  → Semáforo: verde/amarelo/vermelho
│   │   │   ├── LiveFeed.tsx      → Stream de eventos em tempo real
│   │   │   ├── LeadCard.tsx      → Card de lead com status
│   │   │   └── InterventionQueue.tsx → Fila de intervenção manual
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx     → Visão geral: KPIs + feed + semáforo
│   │   │   ├── Conversations.tsx → Lista de conversas ativas
│   │   │   └── ConversationDetail.tsx → Timeline de uma conversa
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts   → Hook para WebSocket events
│   │   │   └── useApi.ts         → Fetch wrapper com tipos
│   │   │
│   │   ├── stores/
│   │   │   └── dashboardStore.ts → Zustand store (estado real-time)
│   │   │
│   │   └── types/
│   │       └── api.ts            → Tipos compartilhados (espelham schemas backend)
│   │
│   └── tests/
│       └── components/
│           └── SLAIndicator.test.tsx
│
├── docker-compose.yml            → Orquestração de todos os serviços
├── .env.example                  → Template de variáveis de ambiente
├── .gitignore
└── README.md
```

---

## Code Style

### Backend (Python)

```python
# app/agent/nodes.py
"""Nós de execução do grafo LangGraph."""

from __future__ import annotations

import logging
from typing import Any

from app.agent.state import AgentState
from app.integrations.mcp_client import MCPClient

logger = logging.getLogger(__name__)


async def analyze_intent(state: AgentState) -> dict[str, Any]:
    """Analisa intenção do lead: suporte, vendas ou agendamento direto.

    Returns:
        Dicionário com 'user_intent' atualizado no estado.
    """
    messages = state["messages"]
    last_message = messages[-1]["content"]

    logger.info("Analisando intenção para mensagem: %s...", last_message[:50])

    # ... lógica de classificação com LLM
    return {"user_intent": "scheduling"}
```

**Convenções Python:**

| Regra | Exemplo |
|---|---|
| Nomes de módulo | `snake_case.py` |
| Classes | `PascalCase` |
| Funções / variáveis | `snake_case` |
| Constantes | `UPPER_SNAKE_CASE` |
| Type hints | Obrigatórios em assinaturas públicas |
| Docstrings | Google style, em português |
| Imports | `from __future__ import annotations` em todo arquivo |
| Async | Preferir `async def` para I/O bound |
| Logging | `logging.getLogger(__name__)`, nunca `print()` |
| Config | Pydantic `BaseSettings`, nunca `os.getenv()` direto |

### Frontend (TypeScript/React)

```tsx
// src/components/SLAIndicator.tsx
import { type FC } from 'react';
import './SLAIndicator.css';

interface SLAIndicatorProps {
  /** Tempo em segundos desde o primeiro contato do lead */
  elapsedSeconds: number;
}

type SLALevel = 'green' | 'yellow' | 'red';

function getSLALevel(seconds: number): SLALevel {
  if (seconds < 60) return 'green';
  if (seconds < 120) return 'yellow';
  return 'red';
}

export const SLAIndicator: FC<SLAIndicatorProps> = ({ elapsedSeconds }) => {
  const level = getSLALevel(elapsedSeconds);

  return (
    <div className={`sla-indicator sla-indicator--${level}`} id="sla-indicator">
      <span className="sla-indicator__time">{elapsedSeconds}s</span>
      <span className="sla-indicator__label">Speed to Lead</span>
    </div>
  );
};
```

**Convenções TypeScript/React:**

| Regra | Exemplo |
|---|---|
| Componentes | `PascalCase`, named export |
| Hooks | `useCamelCase` |
| Tipos/Interfaces | `PascalCase`, interface para props |
| Arquivos de componente | `PascalCase.tsx` |
| CSS | BEM: `block__element--modifier` |
| Estado global | Zustand stores em `camelCaseStore.ts` |
| Strict mode | `strict: true` no tsconfig |

---

## Estratégia de Testes

### Backend

| Nível | Framework | Localização | Cobertura |
|---|---|---|---|
| **Unitário** | pytest | `tests/unit/` | >= 80% nos módulos `agent/`, `services/` |
| **Integração** | pytest + httpx | `tests/integration/` | Endpoints críticos: webhook, WS |
| **Fixtures** | Factory Boy | `tests/factories.py` | Dados de teste consistentes |

```python
# tests/unit/test_nodes.py
"""Testes unitários para os nós do agente."""

import pytest
from app.agent.nodes import analyze_intent
from app.agent.state import AgentState


@pytest.fixture
def base_state() -> AgentState:
    return AgentState(
        messages=[{"role": "user", "content": "Quero agendar uma reunião"}],
        user_intent=None,
        is_qualified=False,
        meeting_scheduled=False,
        context_data=None,
    )


async def test_analyze_intent_detects_scheduling(base_state: AgentState) -> None:
    result = await analyze_intent(base_state)
    assert result["user_intent"] == "scheduling"
```

### Frontend

| Nível | Framework | Localização | Cobertura |
|---|---|---|---|
| **Unitário** | Vitest + Testing Library | `tests/components/` | Componentes com lógica |
| **Hook tests** | Vitest + renderHook | `tests/hooks/` | Hooks customizados |

```tsx
// tests/components/SLAIndicator.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { SLAIndicator } from '../../src/components/SLAIndicator';

describe('SLAIndicator', () => {
  it('mostra verde quando < 60s', () => {
    render(<SLAIndicator elapsedSeconds={45} />);
    const indicator = screen.getByText('45s');
    expect(indicator.closest('.sla-indicator')).toHaveClass('sla-indicator--green');
  });

  it('mostra vermelho quando >= 120s', () => {
    render(<SLAIndicator elapsedSeconds={150} />);
    const indicator = screen.getByText('150s');
    expect(indicator.closest('.sla-indicator')).toHaveClass('sla-indicator--red');
  });
});
```

### Regras gerais de teste

- Rodar testes **antes de cada commit**
- Mocks apenas para I/O externo (LLM, EvolutionAPI, MCP servers)
- Cada nó do LangGraph tem pelo menos 1 teste unitário
- Webhook endpoint tem teste de integração com payload real da EvolutionAPI

---

## Boundaries

### ✅ Sempre fazer

- Rodar `pytest` e `npm test` antes de commits
- Usar type hints em toda assinatura pública (Python) e `strict: true` (TS)
- Validar input com Pydantic schemas nos endpoints
- Usar `logging` (nunca `print`)
- Manter `.env.example` atualizado quando adicionar variáveis
- Documentar decisões arquiteturais em `docs/`
- Tratar erros do LLM/MCP com retry + fallback
- Emitir eventos WebSocket para cada mudança de estado do lead

### ⚠️ Perguntar primeiro

- Alterar schema do banco (migrations)
- Adicionar dependência nova ao `pyproject.toml` ou `package.json`
- Mudar a estrutura do grafo LangGraph (adicionar/remover nós)
- Alterar prompts do agente
- Mudar configuração do Docker Compose
- Alterar lógica de qualificação de leads

### 🚫 Nunca fazer

- Commitar secrets (`.env`, API keys, tokens)
- Usar `os.getenv()` direto — sempre via `config.py`
- Remover testes que falham sem aprovação
- Fazer chamadas síncronas bloqueantes no event loop
- Expor o dashboard na internet sem autenticação
- Hardcodar URLs, portas ou credenciais
- Ignorar erros silenciosamente (`except: pass`)

---

## Critérios de Sucesso

| # | Critério | Como verificar |
|---|---|---|
| 1 | Webhook da EvolutionAPI recebe mensagem e dispara o grafo em < 500ms | Teste de integração + log de timestamp |
| 2 | Agente qualifica lead e agenda reunião em < 2 minutos end-to-end | Teste E2E com mensagem simulada |
| 3 | Dashboard exibe eventos em tempo real via WebSocket | Abrir dashboard, enviar msg, ver atualização |
| 4 | Semáforo SLA muda de cor: verde (< 1 min), amarelo (< 2 min), vermelho (> 2 min) | Teste visual + teste unitário do componente |
| 5 | Consultor pode ver fila de intervenção e assumir conversa | Teste manual no dashboard |
| 6 | `docker compose up` sobe todo o sistema sem erros | CI pipeline + teste manual |
| 7 | Cobertura de testes backend >= 80% nos módulos core | `pytest --cov` |
| 8 | Zero secrets no repositório | `git-secrets` scan |

---

## Decisões Tomadas (Respostas das Perguntas Abertas)

1. **Modelo OpenAI:** GPT-4o-mini.
2. **CRM via MCP:** Planilha Excel.
3. **Google Calendar:** Integrado via service account/OAuth.
4. **Volume de acessos:** 6 consultores de vendas no dashboard.
5. **Base de conhecimento (RAG):** Arquivo PDF fake de exemplo.
6. **Critérios de Qualificação:** 3 perguntas básicas de exemplo (ex: Segmento de atuação, Orçamento estimado, e Prazo de implementação).
7. **Horário de Funcionamento:** Agente responde 24/7.
8. **Mensagem de Fallback:** O lead é colocado em uma "fila de intervenção" para que o consultor humano veja no dashboard e assuma a conversa.
