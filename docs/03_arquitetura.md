# Arquitetura Geral do Agente de Vendas

Este documento descreve a arquitetura geral da solução do Agente de Atendimento e Vendas, detalhando as tecnologias envolvidas, bancos de dados, filas de mensageria e integrações.

## Diagrama de Arquitetura

```mermaid
graph TD
    %% Estilos
    classDef frontend fill:#3182ce,stroke:#2b6cb0,stroke-width:2px,color:#fff
    classDef backend fill:#38a169,stroke:#2f855a,stroke-width:2px,color:#fff
    classDef database fill:#d69e2e,stroke:#b7791f,stroke-width:2px,color:#fff
    classDef queue fill:#805ad5,stroke:#6b46c1,stroke-width:2px,color:#fff
    classDef external fill:#e53e3e,stroke:#c53030,stroke-width:2px,color:#fff
    classDef api fill:#dd6b20,stroke:#c05621,stroke-width:2px,color:#fff

    subgraph "Frontend"
        Dashboard[Centro de Operações<br/>React / Next.js]:::frontend
    end

    subgraph "External Channels"
        WhatsApp[WhatsApp Cliente]:::external
    end

    subgraph "Evolution API"
        Evolution[Evolution API<br/>Node.js]:::api
    end

    subgraph "Backend Core"
        FastAPI[FastAPI<br/>REST Endpoints]:::backend
        WS[WebSocket Manager<br/>Observabilidade Real-time]:::backend
        
        subgraph "AI Engine"
            LangGraph[LangGraph<br/>Máquina de Estados]:::backend
            LLM[LLM / Agent Nodes]:::backend
            MCPClient[Remote MCP Client]:::backend
        end
    end

    subgraph "Mensageria e Cache"
        Redis[(Redis<br/>Pub/Sub & Cache)]:::queue
    end

    subgraph "Persistência"
        Postgres[(PostgreSQL<br/>Database / Estado)]:::database
    end

    subgraph "Serviços Externos / MCP"
        GSheets[Google Sheets]:::external
        GCalendar[Google Calendar]:::external
    end

    %% Fluxo WhatsApp -> Evolution -> Backend
    WhatsApp <-->|Mensagens / Webhooks| Evolution
    Evolution <-->|REST Webhooks| FastAPI

    %% Fluxo Backend -> AI
    FastAPI -->|Processar Mensagem| LangGraph
    LangGraph -->|Orquestração| LLM
    LangGraph -->|Ações MCP| MCPClient

    %% Fluxo Dados / Estado
    LangGraph <-->|Leitura / Escrita Estado| Postgres
    FastAPI <-->|Consultas Gerais| Postgres

    %% Fluxo Integrações MCP
    MCPClient <-->|Sincronização de Leads| GSheets
    MCPClient <-->|Agendamentos| GCalendar

    %% Fluxo Real-time / Observabilidade
    LangGraph -->|Publicar Eventos / Logs| Redis
    Redis -->|Subscrever Eventos| WS
    WS <-->|Streaming de Dados via WebSocket| Dashboard
```

## Componentes Principais

### Frontend
- **Centro de Operações (Dashboard Frontend):** Interface de usuário para monitoramento em tempo real do agente, visualização de logs (observabilidade), acompanhamento da qualificação de leads e controle operacional.

### Canais Externos & APIs
- **WhatsApp:** O canal primário de interação com os leads/clientes.
- **Evolution API:** Serviço responsável por fazer a ponte entre o WhatsApp e o backend do agente. Ele recebe e envia as mensagens via webhooks REST.

### Backend Core (Python)
- **FastAPI:** Recebe os webhooks da Evolution API, além de servir endpoints para o Dashboard e gerenciar conexões WebSocket.
- **WebSocket Manager:** Gerencia as conexões WebSocket com o Frontend para prover observabilidade em tempo real.
- **AI Engine (LangGraph):** O cérebro do agente. Implementa a máquina de estados (State Machine) que controla o fluxo da conversa (classificação, qualificação, transbordo/handoff).
- **Remote MCP Client:** Cliente para o Model Context Protocol (MCP) remoto, que permite ao agente interagir de forma padronizada com ferramentas externas.

### Filas e Mensageria
- **Redis:** Atua como broker de mensageria (Pub/Sub) para distribuir os eventos gerados pelo LangGraph. Permite o streaming assíncrono de logs e estados do agente para os WebSockets de forma desacoplada, além de atuar como cache se necessário.

### Bancos de Dados (Persistência)
- **PostgreSQL:** Banco de dados relacional principal. Armazena as interações, persistência de estado (checkpointer) do LangGraph, informações de leads processados e logs estruturados.

### Serviços Externos
- Acessados pelo agente através do Remote MCP para:
  - **Google Sheets:** Funciona como um banco de dados flexível para CRM simplificado/sync de leads.
  - **Google Calendar:** Para gestão de disponibilidade e agendamento automático de reuniões/apresentações de vendas.
