"""
tests/agents/test_innovation_agent.py

Testes unitarios para o InnovationAgent.
Garante que a arquitetura e as ferramentas exclusivas estao acessiveis.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from aegis.agents.innovation import InnovationAgent, InnovationPriority
from aegis.core.context import Context
from aegis.agents.base import AgentResult


@pytest.fixture
def agent() -> InnovationAgent:
    return InnovationAgent()


@pytest.fixture
def context() -> Context:
    return Context(session_id="test-innovation-session")


class TestInnovationAgent:
    """Testes para validar a integridade do InnovationAgent."""

    def test_agent_initialization(self, agent: InnovationAgent) -> None:
        """Verifica se o agente inicializa com nome e descricao corretos."""
        assert agent.name == "innovation"
        assert "AEGIS" in agent.description
        assert agent.max_steps == 10

    def test_get_tools(self, agent: InnovationAgent) -> None:
        """Verifica se o agente possui as ferramentas exclusivas de inovacao."""
        tools = agent.get_tools()
        tool_names = [t.name for t in tools]
        
        expected_tools = [
            "read_metrics",
            "read_friction_log",
            "read_codebase",
            "write_prd_tasks",
            "write_directive",
            "run_benchmark"
        ]
        
        for expected in expected_tools:
            assert expected in tool_names

    @pytest.mark.asyncio
    async def test_run_basic(self, agent: InnovationAgent, context: Context) -> None:
        """Verifica se o agente coleta dados e gera uma proposta via LLM."""
        # Mock do Anthropic Client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "title": "Teste de Inovação",
            "rationale": "Justificativa de teste",
            "priority": "low",
            "risk_level": 1,
            "tasks": [{
                "id": "7.9.9",
                "phase": 7,
                "title": "Tarefa de Teste",
                "description": "Desc",
                "deliverables": [],
                "acceptance_criteria": [],
                "estimated_complexity": 1
            }]
        }))]
        
        agent.anthropic_client.messages.create = AsyncMock(return_value=mock_response)
        
        # Mock das ferramentas (opcional, pois elas já funcionam ou têm mocks internos)
        with patch("aegis.tools.innovation.ReadMetricsTool.execute", new_callable=AsyncMock) as m_metrics, \
             patch("aegis.tools.innovation.ReadFrictionLogTool.execute", new_callable=AsyncMock) as m_friction, \
             patch("aegis.tools.innovation.ReadCodebaseTool.execute", new_callable=AsyncMock) as m_code, \
             patch("aegis.tools.innovation.WritePRDTasksTool.execute", new_callable=AsyncMock) as m_write:
            
            m_metrics.return_value = MagicMock(success=True, data={})
            m_friction.return_value = MagicMock(success=True, data="No errors")
            m_code.return_value = MagicMock(success=True, data={})
            m_write.return_value = MagicMock(success=True)
            
            result = await agent.run("all_phases_complete", context)
        
        assert result.success is True
        assert "Inovação proposta: Teste de Inovação" in result.output
        assert result.steps_taken == 4  # 3 reads + 1 write
        assert "read_metrics" in result.tools_used
        assert "write_prd_tasks" in result.tools_used

    @pytest.mark.asyncio
    async def test_run_failure_handling(self, agent: InnovationAgent, context: Context) -> None:
        """Verifica se o agente lida com falhas graciosamente."""
        # Simula erro na coleta de dados
        with patch("aegis.tools.innovation.ReadMetricsTool.execute", side_effect=Exception("Data error")):
            result = await agent.run("trigger", context)
            
        assert result.success is False
        assert "Erro ao executar" in result.output
        assert "Data error" in result.error
