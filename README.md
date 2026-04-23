# Agente de Atendimento e Vendas (MRR)

Este projeto consiste em um **Agente de Atendimento e Vendas Inbound** operando através do WhatsApp. O agente recebe mensagens, analisa a intenção do usuário, qualifica leads, consulta uma base de conhecimento e agenda reuniões automaticamente, tudo orquestrado por um backend robusto integrado com LLMs e visível em tempo real em um dashboard.

## Principais Funcionalidades

- **Atendimento Automatizado via WhatsApp:** Integração via Webhook usando EvolutionAPI.
- **Orquestração AI:** Uso do LangGraph e Langchain (OpenAI) para controle de fluxo e tomada de decisão.
- **Integrações Externas (Remote MCP):** Integra-se com CRM (Planilha Excel) e Google Calendar para agendamento.
- **Observabilidade em Tempo Real:** Comunicação bidirecional usando WebSockets para refletir o estado do agente e do lead em um Dashboard web.
- **Monitoramento de SLA (Speed to Lead):** Sistema de semáforo para identificar se a resposta e agendamento estão dentro da métrica de < 2 minutos.
- **Handoff Manual:** Fila de intervenção para quando o agente não consegue prosseguir, permitindo que consultores assumam o controle.

## Tech Stack

### Backend
- **Linguagem:** Python 3.12+
- **Gerenciador de Dependências:** `uv`
- **API Framework:** FastAPI
- **Orquestração AI:** LangGraph
- **LLM SDK:** langchain-openai
- **Banco de Dados:** PostgreSQL 16 (SQLAlchemy + Alembic)
- **Cache e Real-time:** Redis 7
- **Integração WhatsApp:** EvolutionAPI

### Frontend
- **Linguagem / Framework:** TypeScript / React 18
- **Build Tool:** Vite 5
- **State Management:** Zustand
- **Comunicação Real-time:** Native WebSocket

### Infraestrutura
- Docker & Docker Compose (para implantação local/VPS)

## Estrutura do Projeto

- `docs/` - Documentações arquiteturais e de especificação.
- `backend/` - Aplicação FastAPI, banco de dados, grafos do agente e lógica de negócio.
- `frontend/` - Dashboard em React + Vite.
- `docker-compose.yml` - Orquestração local dos serviços (Postgres, Redis, EvolutionAPI).

## Como Iniciar (Getting Started)

### Pré-requisitos
- Python 3.12+
- Node.js e npm
- Docker e Docker Compose
- `uv` instalado globalmente (`pip install uv`)

### 1. Subindo os Serviços Base (Docker)
Levante os serviços de banco de dados, Redis e EvolutionAPI:
```bash
docker compose up -d
```

### 2. Configurando o Backend
```bash
cd backend
uv sync
cp .env.example .env # (ajuste as credenciais conforme necessário, como OPENAI_API_KEY)
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Configurando o Frontend
```bash
cd frontend
npm install
cp .env.example .env # (se aplicável, para definir a URL do backend)
npm run dev
```

## Documentação Adicional

A documentação detalhada da arquitetura, planos de implementação e especificações encontram-se no diretório `docs/`:

- [Especificação Principal (Spec)](./docs/01_spec.md)
- [Plano de Implementação](./docs/02_implementation_plan.md)
- [Arquitetura de Software](./docs/03_arquitetura.md)

## Testes e Qualidade

O projeto utiliza `pytest` para o backend e `vitest` para o frontend.
Recomenda-se executar a suite de testes antes de cada commit.

```bash
# Backend
cd backend && uv run pytest

# Frontend
cd frontend && npm test
```
