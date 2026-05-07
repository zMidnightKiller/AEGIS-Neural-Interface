
import asyncio
import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Adiciona o diretrio raiz ao path para permitir imports do aegis
sys.path.append(str(Path(__file__).parent.parent))

from aegis.core.engine import Engine
from aegis.core.models import UserInput, OperatingMode, AgentResponse
from aegis.core.context import Context
from aegis.agents.base import BaseAgent, AgentResult

async def run_smoke_test():
    print("=== AEGIS Phase 4 Smoke Test ===")
    
    # 1. Setup Engine with mocks
    # Patching where they are used to avoid instantiation issues
    with patch("anthropic.AsyncAnthropic") as mock_anthropic, \
         patch("aegis.agents.memory.EpisodicMemory") as mock_episodic, \
         patch("aegis.agents.memory.SemanticMemory") as mock_semantic, \
         patch("aegis.core.engine.WorkingMemory") as mock_working:
        
        # Mock classificador de intencao
        mock_anthropic.return_value.messages.create = AsyncMock()
        mock_anthropic.return_value.messages.create.side_effect = [
            # Primeira chamada: Classificacao de intencao
            AsyncMock(content=[AsyncMock(text="multi")]),
            # Segunda chamada: Decomposicao de tarefas
            AsyncMock(content=[AsyncMock(text='[{"agent": "research", "task": "preo ETH"}, {"agent": "code", "task": "save to file"}, {"agent": "task", "task": "schedule reminder"}]')]),
            # Terceira chamada: Resposta final (se necessario)
            AsyncMock(content=[AsyncMock(text="Processamento concluido.")])
        ]
        
        engine = Engine()
        session_id = "smoke-test-session"
        
        # 2. Test Parallel/Multi-Agent Orchestration
        complex_prompt = (
            "Pesquise o preo atual do Ethereum, salve em um arquivo chamado 'eth_price.txt' "
            "e agende um lembrete para eu checar isso amanh s 10h."
        )
        
        print(f"\n[Test 1] Multi-agent task: '{complex_prompt}'")
        user_input = UserInput(text=complex_prompt, session_id=session_id, mode=OperatingMode.STANDARD)
        
        try:
            # Mockando os agentes para nao executarem ferramentas reais
            for agent_name, agent in engine.agents.items():
                agent.run = AsyncMock(return_value=AgentResult(
                    success=True, 
                    output=f"Mocked output from {agent_name}", 
                    steps_taken=1, 
                    tools_used=[agent_name], 
                    error=None
                ))
            
            response = await engine.process(user_input)
            print(f"Response: {response.text}")
            print(f"Agents/Tools used: {response.tools_used}")
            
            # Verificacoes basicas
            if any(t in response.tools_used for t in ["research", "web_search"]):
                print("[OK] Research component executed.")
            if any(t in response.tools_used for t in ["code", "file_system"]):
                print("[OK] Code/File System component executed.")
            if any(t in response.tools_used for t in ["task", "calendar"]):
                print("[OK] Task component executed.")
                
        except Exception as e:
            print(f"[ERROR] Test 1 failed: {str(e)}")
            import traceback
            traceback.print_exc()

    # 3. Test Circuit Breaker
    print("\n[Test 2] Circuit Breaker validation (simulated failure)")
    from aegis.core.orchestrator import MultiAgentOrchestrator
    
    class FailingAgent(BaseAgent):
        name = "failing_agent"
        description = "Sempre falha"
        def get_tools(self): return []
        async def run(self, task, context):
            raise RuntimeError("Falha proposital")

    orchestrator = MultiAgentOrchestrator()
    agent = FailingAgent()
    ctx = Context(session_id="breaker-test")
    
    print("Attempting to call failing agent 4 times...")
    for i in range(1, 5):
        try:
            breaker = orchestrator._get_breaker(agent.name)
            await breaker.call(agent.run, "task", ctx)
        except Exception as e:
            print(f"Attempt {i}: {str(e)}")
    
    breaker = orchestrator._get_breaker(agent.name)
    if breaker.state.value == "OPEN":
        print("[OK] Circuit Breaker is OPEN as expected.")
    else:
        print(f"[ERROR] Circuit Breaker state is {breaker.state.value}, expected OPEN.")

    print("\n=== Smoke Test Completed ===")

if __name__ == "__main__":
    # Mockando variaveis de ambiente necessarias para inicializacao da Engine
    os.environ["ANTHROPIC_API_KEY"] = "mock-key"
    os.environ["OPENAI_API_KEY"] = "mock-key"
    os.environ["TAVILY_API_KEY"] = "mock-key"
    
    asyncio.run(run_smoke_test())
