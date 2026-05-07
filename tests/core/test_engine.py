import os
os.environ["ANTHROPIC_API_KEY"] = "fake_key"

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from aegis.core.engine import Engine
from aegis.core.models import UserInput, OperatingMode, AgentResponse
from aegis.agents.base import AgentResult

@pytest.fixture
def mock_engine_deps():
    with patch("aegis.core.engine.get_settings") as mock_settings_fn, \
         patch("aegis.core.engine.WorkingMemory") as mock_memory_class, \
         patch("aegis.core.engine.MemoryAgent") as mock_memory_agent_class, \
         patch("aegis.core.engine.AsyncAnthropic") as mock_anthropic_class, \
         patch("aegis.core.engine.SemanticCache") as mock_cache_class, \
         patch("aegis.core.engine.PluginManager") as mock_plugin_manager_class:
        
        mock_settings = MagicMock()
        mock_settings.PROJECT_NAME = "AEGIS Test"
        mock_settings.VERSION = "0.0.1"
        mock_settings.ANTHROPIC_API_KEY.get_secret_value.return_value = "fake-key"
        mock_settings.ENABLE_SEMANTIC_CACHE = False
        mock_settings.ENABLE_CONTEXT_COMPRESSION = False
        mock_settings.CONTEXT_MAX_TOKENS = 4000
        mock_settings.CONTEXT_COMPRESSION_TOKEN_LIMIT = 3000
        mock_settings_fn.return_value = mock_settings
        
        mock_memory = MagicMock()
        mock_memory.get_history = AsyncMock(return_value=[])
        mock_memory.save_message = AsyncMock()
        mock_memory.close = AsyncMock()
        mock_memory_class.return_value = mock_memory
        
        # Mock MemoryAgent
        mock_memory_agent = MagicMock()
        mock_memory_agent.pre_process = AsyncMock(return_value="Memory Context")
        mock_memory_agent.post_process = AsyncMock()
        mock_memory_agent_class.return_value = mock_memory_agent

        mock_anthropic = MagicMock()
        mock_anthropic_class.return_value = mock_anthropic

        # Mock Cache e Plugins
        mock_cache_class.return_value = MagicMock()
        mock_plugin_manager_class.return_value = MagicMock()
        
        yield mock_settings, mock_memory, mock_memory_agent, mock_anthropic

@pytest.mark.asyncio
class TestEngine:
    """Testes para o motor central AEGIS."""

    async def test_engine_process_basic(self, mock_engine_deps):
        """Garante que o processamento basico retorna uma resposta estruturada."""
        _, mock_memory, mock_memory_agent, mock_anthropic = mock_engine_deps
        engine = Engine()
        
        # Mock do classificador
        engine._classify_intent = AsyncMock(return_value="core_engine")
        
        # Mock da resposta do LLM
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Resposta mockada do AEGIS")]
        mock_anthropic.messages.create = AsyncMock(return_value=mock_response)
        
        user_input = UserInput(
            text="Ola AEGIS",
            session_id="test_session_123",
            mode=OperatingMode.STANDARD
        )
        
        response = await engine.process(user_input)
        
        assert isinstance(response, AgentResponse)
        assert "Resposta mockada" in response.text
        assert response.agent_used == "core_engine"
        assert response.latency_ms >= 0
        assert mock_memory.save_message.call_count == 2
        assert mock_memory_agent.pre_process.called
        assert mock_memory_agent.post_process.called

    async def test_engine_routing_research(self, mock_engine_deps):
        """Verifica se o roteamento identifica a intencao de pesquisa."""
        _, _, mock_memory_agent, _ = mock_engine_deps
        with patch("aegis.core.engine.ResearchAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=AgentResult(
                success=True,
                output="Resultado da pesquisa",
                steps_taken=2,
                tools_used=["web_search", "web_fetch"]
            ))
            mock_agent_class.return_value = mock_agent
            
            engine = Engine()
            # Mock do classificador
            engine._classify_intent = AsyncMock(return_value="research")
            
            user_input = UserInput(
                text="Por favor, faca uma busca sobre o tempo",
                session_id="test_session_456"
            )
            
            response = await engine.process(user_input)
            assert response.agent_used == "research"
            assert "web_search" in response.tools_used
            assert mock_memory_agent.pre_process.called

    async def test_engine_different_modes(self, mock_engine_deps):
        """Garante que diferentes modos sao passados corretamente."""
        _, _, _, mock_anthropic = mock_engine_deps
        engine = Engine()
        # Mock do classificador
        engine._classify_intent = AsyncMock(return_value="core_engine")
        
        # Mock da resposta do LLM
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Resposta em modo BRIEFING")]
        mock_anthropic.messages.create = AsyncMock(return_value=mock_response)
        
        user_input = UserInput(
            text="Teste",
            session_id="test_session_789",
            mode=OperatingMode.BRIEFING
        )
        
        response = await engine.process(user_input)
        assert "BRIEFING" in response.text
