# Agente de Atendimento e Vendas — Refinamento de Arquitetura

## Declaração do Problema

> **Como poderíamos transformar o boilerplate de demonstração ao vivo (Aula 30) em uma arquitetura de produção completa — backend + frontend — para um Agente de Atendimento e Vendas que capture leads inbound, os qualifique e agende reuniões em tempo real, sem perder a simplicidade que permite escalar e manter o sistema?**

---

## Contexto e Restrições

| Dimensão | Definição |
|---|---|
| **Usuários** | Lead (WhatsApp) + Consultor de vendas (Dashboard) |
| **Canais** | EvolutionAPI (WhatsApp) em Docker |
| **Deploy** | Docker Compose obrigatório |
| **Métrica** | Speed to lead < 2 min + taxa de agendamento |
| **Tipo** | Operação interna, NÃO é SaaS |

### Quem usa o sistema

- **Lead/Cliente:** Interage diretamente via WhatsApp. Recebe respostas automáticas do agente, é qualificado e tem reunião agendada — tudo sem sair da conversa.
- **Consultor de Vendas:** Acompanha o agendamento automático pelo dashboard e intervém nas sessões que requerem atendimento humano.

### O que define sucesso

- Um lead responde no WhatsApp e em **< 2 minutos** já tem uma reunião agendada.
- Métricas principais: **speed to lead** e **taxa de agendamento**.

---

## Variações de Arquitetura

### Variação 1: Monolito Modular (A base sólida óbvia)

```text
docker-compose.yml
├── backend (FastAPI + LangGraph em um único processo)
│   ├── api/          → REST + WebSocket endpoints
│   ├── agent/        → LangGraph graph + nodes
│   ├── core/         → State, models, schemas
│   ├── integrations/ → EvolutionAPI webhook handler, CRM, Calendar
│   └── db/           → SQLAlchemy/PostgreSQL
├── frontend (React/Vite dashboard)
├── postgres
├── redis (cache + pub/sub para real-time)
└── evolution-api
```

**A história:** Um único backend FastAPI contém toda a lógica. Recebe webhooks da EvolutionAPI, executa o grafo LangGraph e empurra eventos ao dashboard via WebSocket. PostgreSQL guarda estado dos leads e conversas. Redis faz pub/sub para que o dashboard atualize em tempo real.

**Por que existe:** É a arquitetura que 90% dos times deveria escolher primeiro. Módulos claros sem a complexidade de microsserviços. Para uma operação interna, é ideal.

**Trade-offs:**
- ✅ Simples de debugar e manter
- ✅ Deploy único com Docker Compose
- ✅ Perfeito para operação interna
- ⚠️ Se o agente travar, trava tudo (mitigável com workers)
- ⚠️ Observabilidade do SLA depende de implementação extra

---

### Variação 2: Event-Driven com Message Queue (A "correta" de livro)

```text
docker-compose.yml
├── webhook-receiver (FastAPI leve — só recebe e enfileira)
├── agent-worker (LangGraph — consome da fila, processa)
├── dashboard-api (FastAPI — serve o frontend)
├── frontend (React)
├── rabbitmq / redis-streams (message broker)
├── postgres
└── evolution-api
```

**A história:** Cada responsabilidade vive no seu próprio container. O webhook receiver só enfileira mensagens. Um worker consome e executa o agente. O dashboard-api serve dados. Se o agente crashar, as mensagens não se perdem — estão na fila.

**Por que existe:** Resiliência real. Se o agente leva 30s para responder, o webhook não dá timeout. Mas... você realmente precisa dessa complexidade para sua operação interna?

**Trade-offs:**
- ✅ Resiliente — mensagens nunca se perdem
- ✅ Escalável horizontalmente (mais workers)
- ⚠️ Complexidade alta para operação interna
- ⚠️ 4-6 semanas para implementar
- ❌ Debugging distribuído é significativamente mais difícil

---

### Variação 3: Real-Time First (Otimizada para a métrica < 2 min)

```text
docker-compose.yml
├── backend (FastAPI + LangGraph)
│   ├── streams/      → SSE/WebSocket event bus (cada passo do lead visível)
│   ├── agent/        → LangGraph com checkpointing em Redis
│   ├── webhooks/     → EvolutionAPI handler
│   └── monitors/     → SLA tracker (alerta se > 90s sem resposta)
├── frontend (React — Centro de Operações)
│   ├── LiveFeed      → Stream de mensagens em tempo real
│   ├── SLADashboard  → Semáforo: verde(<1min), amarelo(<2min), vermelho(>2min)
│   └── Interventions → Fila de "o agente não soube responder, intervenha"
├── postgres + redis
└── evolution-api
```

**A história:** Toda a arquitetura gira ao redor de tornar visível o SLA de < 2 min. O dashboard não é um CRUD — é um *centro de operações em tempo real*. Cada passo do agente emite um evento que o frontend renderiza como uma timeline. Um monitor de SLA alerta quando um lead está esperando demais.

**Por que existe:** Se sua métrica é "speed to lead", a arquitetura deveria tornar essa métrica *visível e mensurável* a todo momento. Não é só um backend que responde rápido — é um sistema que te diz QUANDO não está respondendo rápido.

**Trade-offs:**
- ✅ Observabilidade máxima da métrica principal
- ✅ Consultor sabe exatamente quando intervir
- ✅ Cada gargalo de tempo fica visível
- ⚠️ Frontend mais complexo (gerenciamento de estado real-time)
- ⚠️ 3-4 semanas para implementar

---

### Variação 4: 10x Mais Simples (Entregar em dias, não semanas)

```text
docker-compose.yml
├── backend (FastAPI + LangGraph — mínimo viável)
├── postgres
├── metabase (dashboard sem código customizado)
└── evolution-api
```

**A história:** Você não constrói frontend. Usa Metabase conectado direto ao PostgreSQL para visualizar leads, conversas e agendamentos. O backend é mínimo: recebe webhook → executa agente → salva resultado → responde. Nada mais.

**Por que existe:** É a versão que pode estar rodando em 2-3 dias. Se o que importa é *que funcione*, não que fique bonito. O dashboard você itera depois quando souber quais métricas realmente observa.

**Trade-offs:**
- ✅ Entrega em 2-5 dias
- ✅ Zero código frontend para manter
- ⚠️ UX limitada para o consultor
- ⚠️ Sem real-time — Metabase atualiza com polling
- ❌ Sem fila de intervenção manual para o consultor

---

### Variação 5: Dashboard-First (O frontend no centro)

```text
docker-compose.yml
├── frontend (Next.js full-stack — API routes + UI)
│   ├── app/api/webhooks/  → recebe EvolutionAPI
│   ├── app/api/agent/     → chama o agent service
│   ├── app/dashboard/     → UI do consultor
│   └── app/api/cron/      → SLA monitoring
├── agent-service (Python FastAPI + LangGraph — só AI)
├── postgres
└── evolution-api
```

**A história:** E se o frontend fosse o centro, não o backend? Next.js gerencia as rotas API, o webhook e serve o dashboard. O serviço de AI em Python é um microsserviço que só recebe "analise esta mensagem" e retorna "faça isto". O frontend orquestra.

**Por que existe:** Para cenários onde o consultor de vendas é o usuário principal e a experiência do dashboard é o mais importante. O backend AI se transforma em um "cérebro" que o frontend consulta.

**Trade-offs:**
- ✅ UX do consultor é prioridade máxima
- ✅ Full-stack JavaScript para iteração rápida no dashboard
- ⚠️ Duas linguagens (Python para AI + JS para o resto)
- ⚠️ Orquestração dividida entre frontend e backend
- ⚠️ 3-4 semanas para implementar

---

## Comparação

| Variação | Complexidade | Tempo p/ entregar | Resiliência | Observabilidade |
|---|---|---|---|---|
| 1. Monolito Modular | ⭐⭐ | 2-3 semanas | Média | Média |
| 2. Event-Driven | ⭐⭐⭐⭐ | 4-6 semanas | Alta | Alta |
| 3. Real-Time First | ⭐⭐⭐ | 3-4 semanas | Média | **Muito Alta** |
| 4. 10x Simples | ⭐ | 2-5 dias | Baixa | Baixa |
| 5. Dashboard-First | ⭐⭐⭐ | 3-4 semanas | Média | Alta |

---

## Recomendação Preliminar

A **Variação 3 (Real-Time First)** é a que mais se alinha com a métrica declarada (speed to lead < 2 min). Mas a **Variação 1 (Monolito Modular)** é o fundamento mais sólido para começar.

A pergunta interessante é: **é possível tomar a estrutura do Monolito Modular e adicionar a camada de observabilidade do Real-Time First?**

Essa combinação (1 + 3) daria:
- A simplicidade de deploy e manutenção do monolito
- A visibilidade de SLA e o centro de operações do real-time first
- Complexidade gerenciável (⭐⭐⭐)
- Tempo de entrega: ~3 semanas

---

## Próximos Passos

> **Quais dessas variações ressoam? Há algo que faça você dizer "é exatamente isso que preciso" ou "isso definitivamente NÃO"?**

Após a escolha da direção, o próximo passo será:
1. Avaliar e convergir (stress-test da direção escolhida)
2. Levantar suposições ocultas
3. Definir escopo do MVP com lista de "Não Fazer"
4. Produzir o one-pager final com arquitetura definitiva
