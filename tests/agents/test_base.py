"""
tests/agents/test_base.py

Testes unitarios para a classe base de agentes.
"""
import pytest
from unittest.mock import MagicMock, patch
from aegis.agents.base import BaseAgent, AgentResult
from aegis.core.context import Context
from aegis.tools.base import BaseTool


class MockAgent(BaseAgent):
    """Subclasse concreta para testar a interface BaseAgent."""

    name = "mock_agent"
    description = "Agente para fins de teste unitario."

    def get_tools(self) -> list[BaseTool]:
        return []

    async def run(self, task: str, context: Context) -> AgentResult:
        """Simula a execucao de uma tarefa."""
        return AgentResult(
            success=True,
            output=f"Executado: {task}",
            steps_taken=1,
            tools_used=[],
        )


@pytest.fixture
def mock_settings():
    """Moca o get_settings para evitar ValidationError do Pydantic."""
    with patch("aegis.core.context.get_settings") as mock:
        settings = MagicMock()
        settings.CONTEXT_MAX_TOKENS = 4000
        mock.return_value = settings
        yield settings


@pytest.fixture
def context(mock_settings):
    """Fixture para criar um contexto de teste."""
    return Context(session_id="test_session")


@pytest.mark.asyncio
async def test_agent_result_structure():
    """Valida se o AgentResult possui os campos obrigatorios."""
    result = AgentResult(
        success=True,
        output="Sucesso",
        steps_taken=3,
        tools_used=["tool1", "tool2"],
    )
    assert result.success is True
    assert result.output == "Sucesso"
    assert result.steps_taken == 3
    assert len(result.tools_used) == 2
    assert result.error is None


@pytest.mark.asyncio
async def test_base_agent_interface(context):
    """Valida se uma subclasse concreta pode ser instanciada e executada."""
    agent = MockAgent()
    assert agent.name == "mock_agent"
    assert agent.max_steps == 5

    result = await agent.run("Fazer café", context)
    assert result.success is True
    assert "Fazer café" in result.output
    assert result.steps_taken == 1
