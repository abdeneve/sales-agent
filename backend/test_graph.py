import asyncio
import uuid
from app.agent.graph import build_agent_graph
from app.agent.state import AgentState

async def test_graph():
    # 1. Instanciar o grafo
    graph = build_agent_graph()
    
    # 2. Definir um estado inicial simulando uma mensagem de "Oi, quero agendar"
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": "Olá, gostaria de agendar uma reunião para conhecer os serviços de IA."}],
        "lead_phone": "5511999999999",
        "conversation_id": uuid.uuid4(),
        "qualification_step": 0,
        "is_qualified": False,
        "should_handoff": False,
        "meeting_scheduled": False
    }
    
    print("--- Iniciando processamento do Grafo ---")
    
    # 3. Invocar o grafo
    # O grafo processa os nós conforme a lógica de roteamento
    result = await graph.ainvoke(initial_state)
    
    print("\n--- Estado Final ---")
    print(f"Intenção detectada: {result.get('user_intent')}")
    try:
        print(f"Resposta do Agente: {result.get('agent_response')}")
    except UnicodeEncodeError:
        print(f"Resposta do Agente: {result.get('agent_response').encode('ascii', 'ignore').decode('ascii')} (emoji removido para exibição no console)")

    print(f"Passo de qualificação: {result.get('qualification_step')}")
    print(f"Qualificado: {result.get('is_qualified')}")
    
    # Salvar o desenho do grafo como PNG
    try:
        print("\n--- Gerando PNG do Grafo ---")
        png_data = graph.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(png_data)
        print("Grafo salvo com sucesso em 'backend/graph.png'")
    except Exception as e:
        print(f"Não foi possível gerar o PNG do grafo: {e}")
        print("Dica: Verifique se as dependências (pygraphviz ou mermaid) estão instaladas.")

if __name__ == "__main__":
    asyncio.run(test_graph())
