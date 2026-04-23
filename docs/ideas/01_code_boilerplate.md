# Live Code Boilerplate: Agente de Atendimento e Vendas (MRR)

Abaixo está a estrutura do projeto, dependências e esqueletos de código para a demonstração ao vivo da "Aula 30". Este *boilerplate* preparará a arquitetura limpa (LangGraph + Remote MCP), permitindo que você foque nas explicações de negócio e construção da lógica principal sem perder tempo com tipagem e configurações base.

## 1. Estrutura do Projeto

```text
sales_agent/
├── agents/
│   ├── __init__.py
│   ├── graph.py
│   └── nodes.py
├── core/
│   ├── __init__.py
│   └── state.py
├── tools/
│   ├── __init__.py
│   └── mcp_clients.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── requirements.txt
└── main.py
```

**Comando Terminal para criar estrutura inicial:**
```bash
mkdir -p sales_agent/{agents,core,tools,config}
touch sales_agent/agents/{__init__.py,graph.py,nodes.py}
touch sales_agent/core/{__init__.py,state.py}
touch sales_agent/tools/{__init__.py,mcp_clients.py}
touch sales_agent/config/{__init__.py,settings.py}
touch sales_agent/{requirements.txt,main.py}
```

## 2. Gestão de Dependências

`requirements.txt`
```text
langchain>=0.2.0
langgraph>=0.0.60
pydantic>=2.7.0
python-dotenv>=1.0.0
langchain-openai>=0.1.0
```

## 3. Esqueletos de Código (Boilerplate)

### Estado do Grafo
```python
# core/state.py
from typing import TypedDict, Annotated, List, Optional, Dict, Any
import operator

class AgentState(TypedDict):
    """
    Representa o estado do nosso Agente de Vendas INBOUND (Speed to Lead).
    Armazena a memória das mensagens, a intenção detectada e o status da qualificação.
    """
    messages: Annotated[List[Dict[str, Any]], operator.add]
    user_intent: Optional[str]
    is_qualified: bool
    meeting_scheduled: bool
    context_data: Optional[Dict[str, Any]]
```

### Configurações Iniciais
```python
# config/settings.py
import os
from dotenv import load_dotenv

def initialize_environment() -> None:
    """
    Carrega variáveis de ambiente necessárias (OpenAI, EvolutionAPI, endpoints MCP).
    """
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY ausente. Verifique o arquivo .env")
```

### Clientes do Protocolo MCP
```python
# tools/mcp_clients.py
from typing import List, Any
from pydantic import BaseModel, Field

class CRMQuerySchema(BaseModel):
    """Estrutura exigida pelo MCP Server de CRM para consultas"""
    email: str = Field(description="O e-mail do lead para verificação no CRM")

def create_mcp_toolkit() -> List[Any]:
    """
    Configura a conexão segura com os servidores MCP Remotos do cliente 
    (Ex: Consulta CRM e Inserção no Google Calendar).
    """
    # TODO: Implementar lógica de 'Configuração do Remote MCP Client' ao vivo
    pass
```

### Nós de Execução (LangGraph)
```python
# agents/nodes.py
from core.state import AgentState
from typing import Dict, Any

def analyze_intent(state: AgentState) -> Dict[str, Any]:
    """
    Nó 1: Avalia se a mensagem do cliente demanda suporte técnico, 
    dúvida de vendas ou agendamento direto.
    """
    # TODO: Implementar lógica de 'Análise de Intenção e Qualificação' ao vivo
    pass

def consult_knowledge_base(state: AgentState) -> Dict[str, Any]:
    """
    Nó 2: Aciona o RAG corporativo para tirar dúvidas técnicas que impeçam
    o agendamento, diminuindo o atrito do usuário.
    """
    # TODO: Implementar lógica de 'Consulta de Contexto RAG' ao vivo
    pass

def trigger_mcp_action(state: AgentState) -> Dict[str, Any]:
    """
    Nó 3: Executa as chamadas aos MCP Servers (CRM Status ou Ferramentas Internas).
    Afastando a IA do código duro.
    """
    # TODO: Implementar lógica de 'Chamada Dinâmica das Tools / Execução de Tool' ao vivo
    pass

def schedule_meeting(state: AgentState) -> Dict[str, Any]:
    """
    Nó Final: Formaliza o hand-off pré-agendando a call de vendas no calendário 
    do consultor apropriado.
    """
    # TODO: Implementar lógica de 'Agendamento/Handoff via Calendar API' ao vivo
    pass
```

### Orquestrador de Agentes
```python
# agents/graph.py
from langgraph.graph import StateGraph, END
from core.state import AgentState
from agents.nodes import (
    analyze_intent,
    consult_knowledge_base,
    trigger_mcp_action,
    schedule_meeting
)

def build_agent_graph() -> StateGraph:
    """
    Define a arquitetura modular e de roteamento (StateGraph) do agente, conectando
    nós e validando intenções através de arestas condicionais.
    """
    # TODO: Implementar lógica de 'Orquestração do Grafo e Arestas Condicionais' ao vivo
    pass
```

### Ponto de Entrada Principal
```python
# main.py
from config.settings import initialize_environment
from agents.graph import build_agent_graph

def main() -> None:
    """
    Ponto de entrada do Worker/Demonstração ao vivo. 
    Inicia o ambiente, compila o grafo e manda uma mensagem de teste.
    """
    initialize_environment()
    
    print("[INFO] Subindo orquestrador do Agente de Vendas (MRR)...\n")
    
    # TODO: Implementar lógica de 'Execução da Trilha (Teste Invocation) e Prints' ao vivo
    pass

if __name__ == "__main__":
    main()
```
