import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aegis.core.engine import Engine
from aegis.core.models import UserInput, OperatingMode

@pytest.mark.asyncio
async def test_semantic_cache_hit():
    with patch("aegis.core.engine.AsyncAnthropic"), \
         patch("aegis.core.engine.SemanticCache") as mock_cache_class, \
         patch("aegis.core.engine.WorkingMemory"), \
         patch("aegis.core.engine.obs_manager"), \
         patch("aegis.core.engine.MemoryAgent"), \
         patch("aegis.core.engine.ResearchAgent"), \
         patch("aegis.core.engine.MediaAgent"), \
         patch("aegis.core.engine.TaskAgent"), \
         patch("aegis.core.engine.CodeAgent"), \
         patch("aegis.core.engine.MultiAgentOrchestrator"):
        
        mock_cache = mock_cache_class.return_value
        mock_cache.get = AsyncMock(return_value="Resposta em cache")
        
        engine = Engine()
        user_input = UserInput(text="Olá", session_id="test_session")
        
        response = await engine.process(user_input)
        
        assert response.text == "Resposta em cache"
        assert response.agent_used == "semantic_cache"

@pytest.mark.asyncio
async def test_context_compression_trigger():
    with patch("aegis.core.engine.AsyncAnthropic") as mock_anthropic_class, \
         patch("aegis.core.engine.SemanticCache") as mock_cache_class, \
         patch("aegis.core.engine.WorkingMemory") as mock_wm_class, \
         patch("aegis.core.engine.obs_manager"), \
         patch("aegis.core.engine.MemoryAgent") as mock_mem_agent_class, \
         patch("aegis.core.engine.ResearchAgent"), \
         patch("aegis.core.engine.MediaAgent"), \
         patch("aegis.core.engine.TaskAgent"), \
         patch("aegis.core.engine.CodeAgent"), \
         patch("aegis.core.engine.MultiAgentOrchestrator"):
        
        # Setup Cache
        mock_cache = mock_cache_class.return_value
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        
        # Setup WorkingMemory
        mock_wm = mock_wm_class.return_value
        mock_wm.get_history = AsyncMock(return_value=[])
        mock_wm.save_message = AsyncMock()
        mock_wm.close = AsyncMock()
        
        # Setup MemoryAgent
        mock_mem_agent = mock_mem_agent_class.return_value
        mock_mem_agent.pre_process = AsyncMock(return_value=None)
        mock_mem_agent.post_process = AsyncMock()
        
        engine = Engine()
        engine.settings.ENABLE_CONTEXT_COMPRESSION = True
        engine.settings.CONTEXT_COMPRESSION_TOKEN_LIMIT = 5 # Bem baixo
        
        # Mock LLM calls
        mock_llm = mock_anthropic_class.return_value
        mock_intent = MagicMock()
        mock_intent.content = [MagicMock(text="core_engine")]
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="Resposta do LLM")]
        mock_summary = MagicMock()
        mock_summary.content = [MagicMock(text="Resumo comprimido")]
        
        mock_llm.messages.create = AsyncMock(side_effect=[mock_intent, mock_resp, mock_summary])
        
        user_input = UserInput(text="Texto longo para compressão", session_id="test_session")
        
        with patch.object(Engine, "_compress_context", wraps=engine._compress_context) as mock_compress:
            response = await engine.process(user_input)
            
        assert response.text == "Resposta do LLM"
        assert mock_compress.called
