"""
tests/agents/test_task_agent.py

Testes unitários para o TaskAgent.
"""
import os
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from aegis.agents.task import TaskAgent
from aegis.core.context import Context
from aegis.tools.base import ToolResult

# Mock env vars
os.environ["ANTHROPIC_API_KEY"] = "test-key"

@pytest.fixture
def context():
    return Context(session_id="test_task_session")

@pytest.fixture
def mock_anthropic():
    client = AsyncMock()
    return client

class TestTaskAgent:
    @pytest.mark.asyncio
    async def test_task_agent_run_finish(self, context, mock_anthropic):
        # Mock do Claude finalizando a tarefa
        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(text=json.dumps({
                "thought": "Tarefa concluída.",
                "finish": "Seu compromisso foi agendado."
            }))
        ]
        mock_anthropic.messages.create = AsyncMock(return_value=mock_message)
        
        agent = TaskAgent(anthropic_client=mock_anthropic)
        result = await agent.run("Agende uma reunião amanhã às 10h", context)
        
        assert result.success is True
        assert result.output == "Seu compromisso foi agendado."
        assert result.steps_taken == 1

    @pytest.mark.asyncio
    async def test_task_agent_run_with_tool_call(self, context, mock_anthropic):
        # Primeiro passo: chamar ferramenta calendar
        msg1 = MagicMock()
        msg1.content = [
            MagicMock(text=json.dumps({
                "thought": "Vou listar os eventos para ver se há conflito.",
                "tool": "calendar",
                "params": {"action": "list"}
            }))
        ]
        
        # Segundo passo: finalizar
        msg2 = MagicMock()
        msg2.content = [
            MagicMock(text=json.dumps({
                "thought": "Não há conflitos. Vou avisar o usuário.",
                "finish": "Nenhum conflito encontrado."
            }))
        ]
        
        mock_anthropic.messages.create = AsyncMock(side_effect=[msg1, msg2])
        
        with patch("aegis.agents.task.CalendarTool") as MockCalendar:
            mock_cal_inst = MockCalendar.return_value
            mock_cal_inst.execute = AsyncMock(return_value=ToolResult(
                success=True,
                data=[],
                metadata={}
            ))
            mock_cal_inst.name = "calendar"
            
            agent = TaskAgent(anthropic_client=mock_anthropic)
            result = await agent.run("Verifique minha agenda", context)
            
            assert result.success is True
            assert result.output == "Nenhum conflito encontrado."
            assert result.steps_taken == 2
            assert "calendar" in result.tools_used

    @pytest.mark.asyncio
    async def test_task_agent_max_steps_reached(self, context, mock_anthropic):
        # Agente que nunca finaliza
        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(text=json.dumps({
                "thought": "Continuo tentando...",
                "tool": "calendar",
                "params": {"action": "list"}
            }))
        ]
        mock_anthropic.messages.create = AsyncMock(return_value=mock_message)
        
        with patch("aegis.agents.task.CalendarTool") as MockCalendar:
            MockCalendar.return_value.execute = AsyncMock(return_value=ToolResult(success=True, data=[]))
            MockCalendar.return_value.name = "calendar"
            
            agent = TaskAgent(anthropic_client=mock_anthropic)
            # Reduzir max_steps para o teste ser rápido
            agent.max_steps = 2
            result = await agent.run("Tarefa infinita", context)
            
            assert result.success is False
            assert "Limite de passos atingido" in result.output
            assert result.steps_taken == 2
