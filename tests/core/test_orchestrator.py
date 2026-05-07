import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from aegis.core.orchestrator import MultiAgentOrchestrator, CircuitState, CircuitBreaker
from aegis.agents.base import BaseAgent, AgentResult
from aegis.core.context import Context

@pytest.fixture
def context():
    return Context("test_session")

class MockAgent(BaseAgent):
    name = "mock_agent"
    description = "test agent"
    def get_tools(self): return []
    async def run(self, task, context):
        return AgentResult(success=True, output=f"Result for {task}", steps_taken=1, tools_used=[])

@pytest.mark.asyncio
async def test_circuit_breaker_open_on_failure():
    breaker = CircuitBreaker(name="test", failure_threshold=2)
    
    async def failing_func():
        raise ValueError("Fail")

    # Primeira falha
    with pytest.raises(ValueError):
        await breaker.call(failing_func)
    assert breaker.state == CircuitState.CLOSED
    
    # Segunda falha -> Abre o circuito
    with pytest.raises(ValueError):
        await breaker.call(failing_func)
    assert breaker.state == CircuitState.OPEN
    assert breaker.failures == 2

    # Chamada bloqueada
    with pytest.raises(RuntimeError) as exc:
        await breaker.call(failing_func)
    assert "is OPEN" in str(exc.value)

@pytest.mark.asyncio
async def test_orchestrator_parallel_execution(context):
    orchestrator = MultiAgentOrchestrator()
    agent1 = MockAgent()
    agent1.name = "agent1"
    agent2 = MockAgent()
    agent2.name = "agent2"

    agent_tasks = [
        (agent1, "task 1", context),
        (agent2, "task 2", context)
    ]

    results = await orchestrator.run_parallel(agent_tasks)
    
    assert len(results) == 2
    assert results[0].output == "Result for task 1"
    assert results[1].output == "Result for task 2"

@pytest.mark.asyncio
async def test_orchestrator_handles_exceptions(context):
    orchestrator = MultiAgentOrchestrator()
    agent1 = MockAgent()
    agent1.name = "agent1"
    
    async def failing_run(task, context):
        raise ValueError("Agent Failed")
    
    agent1.run = failing_run

    agent_tasks = [(agent1, "task 1", context)]
    results = await orchestrator.run_parallel(agent_tasks)
    
    assert isinstance(results[0], ValueError)

@pytest.mark.asyncio
async def test_orchestrator_timeout(context):
    orchestrator = MultiAgentOrchestrator()
    agent1 = MockAgent()
    agent1.name = "slow_agent"
    
    async def slow_run(task, context):
        await asyncio.sleep(2)
        return AgentResult(success=True, output="Done", steps_taken=1, tools_used=[])
    
    agent1.run = slow_run
    
    agent_tasks = [(agent1, "task 1", context)]
    # Timeout pequeno para forçar a falha
    results = await orchestrator.run_parallel(agent_tasks, timeout=0.1)
    
    assert len(results) == 1
    assert isinstance(results[0], asyncio.TimeoutError)

@pytest.mark.asyncio
async def test_orchestrator_concurrency_limit(context):
    # Orquestrador com apenas 1 de concorrência
    orchestrator = MultiAgentOrchestrator(max_concurrency=1)
    agent1 = MockAgent()
    agent1.name = "agent1"
    
    execution_order = []
    
    async def track_run(task, context):
        execution_order.append(f"start_{task}")
        await asyncio.sleep(0.1)
        execution_order.append(f"end_{task}")
        return AgentResult(success=True, output="Done", steps_taken=1, tools_used=[])
    
    agent1.run = track_run
    
    agent_tasks = [
        (agent1, "t1", context),
        (agent1, "t2", context)
    ]
    
    await orchestrator.run_parallel(agent_tasks)
    
    # Se a concorrência for 1, t2 deve começar após t1 terminar
    assert execution_order == ["start_t1", "end_t1", "start_t2", "end_t2"]
