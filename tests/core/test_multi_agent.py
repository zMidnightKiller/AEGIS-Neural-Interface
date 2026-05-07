import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aegis.core.engine import Engine
from aegis.core.models import UserInput, OperatingMode

@pytest.fixture
def engine():
    with patch("aegis.core.engine.AsyncAnthropic"), \
         patch("aegis.core.engine.MemoryAgent") as mock_memory, \
         patch("aegis.core.engine.ResearchAgent") as mock_research, \
         patch("aegis.core.engine.MediaAgent") as mock_media, \
         patch("aegis.core.engine.TaskAgent") as mock_task, \
         patch("aegis.core.engine.CodeAgent") as mock_code:
        
        # Configurar métodos awaitable
        mock_memory.return_value.pre_process = AsyncMock(return_value="memory context")
        mock_memory.return_value.post_process = AsyncMock()
        mock_research.return_value.run = AsyncMock()
        mock_media.return_value.run = AsyncMock()
        mock_task.return_value.run = AsyncMock()
        mock_code.return_value.run = AsyncMock()
        
        return Engine()

@pytest.mark.asyncio
async def test_engine_handles_multi_intent(engine):
    # Mock do classificador
    engine._classify_intent = AsyncMock(return_value="multi")
    
    # Mock do handle_multi_agent_request
    engine._handle_multi_agent_request = AsyncMock(return_value=("Result from multi-agents", ["tool1", "tool2"]))
    
    user_input = UserInput(text="Pesquise X e agende Y", session_id="test_multi")
    
    with patch("aegis.core.engine.WorkingMemory") as mock_mem:
        mock_mem_instance = mock_mem.return_value
        mock_mem_instance.get_history = AsyncMock(return_value=[])
        mock_mem_instance.save_message = AsyncMock()
        mock_mem_instance.close = AsyncMock()
        
        response = await engine.process(user_input)
        
    assert response.agent_used == "multi"
    assert response.text == "Result from multi-agents"
    assert "tool1" in response.tools_used

@pytest.mark.asyncio
async def test_handle_multi_agent_request_real_logic(engine):
    # Mock do LLM para decomposição
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='[{"agent": "research", "task": "search X"}, {"agent": "task", "task": "schedule Y"}]')]
    engine.llm_client.messages.create = AsyncMock(return_value=mock_msg)
    
    # Mock dos agentes
    engine.agents["research"].run = AsyncMock(return_value=MagicMock(success=True, output="Research done", tools_used=["web_search"]))
    engine.agents["task"].run = AsyncMock(return_value=MagicMock(success=True, output="Task scheduled", tools_used=["calendar"]))
    
    from aegis.core.context import Context
    ctx = Context("test_multi_logic")
    user_input = UserInput(text="Pesquise X e agende Y", session_id="test_multi_logic")
    
    output, tools = await engine._handle_multi_agent_request(user_input, ctx)
    
    assert "Research done" in output
    assert "Task scheduled" in output
    assert "web_search" in tools
    assert "calendar" in tools
    assert engine.agents["research"].run.called
    assert engine.agents["task"].run.called
