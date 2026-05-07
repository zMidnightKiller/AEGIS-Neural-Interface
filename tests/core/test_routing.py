import os
from unittest.mock import AsyncMock, patch, MagicMock

# Mocks de ambiente e dependencias pesadas antes de qualquer import do projeto
os.environ["ANTHROPIC_API_KEY"] = "sk-fake-key-for-testing"
os.environ["TAVILY_API_KEY"] = "tvly-fake-key"
os.environ["OPENAI_API_KEY"] = "sk-fake-openai-key"
os.environ["ELEVENLABS_API_KEY"] = "sk-fake-eleven-key"
os.environ["NEO4J_PASSWORD"] = "fake-pass"

# Mocar redis globalmente com metodos assincronos
import redis.asyncio
mock_redis_client = MagicMock()
mock_redis_client.rpush = AsyncMock()
mock_redis_client.lrange = AsyncMock(return_value=[])
mock_redis_client.expire = AsyncMock()
mock_redis_client.close = AsyncMock()
redis.asyncio.from_url = MagicMock(return_value=mock_redis_client)

import pytest
from aegis.core.engine import Engine
from aegis.core.models import UserInput, OperatingMode, AgentResponse
from aegis.agents.base import AgentResult

@pytest.fixture
def engine():
    with patch("aegis.core.engine.get_settings") as mock_settings:
        mock_settings.return_value.ANTHROPIC_API_KEY.get_secret_value.return_value = "fake_key"
        mock_settings.return_value.PROJECT_NAME = "AEGIS"
        mock_settings.return_value.VERSION = "1.0.0"
        with patch("aegis.core.engine.AsyncAnthropic"):
            # Mocar WorkingMemory onde ele e usado
            with patch("aegis.core.engine.WorkingMemory") as mock_wm_cls:
                mock_wm_instance = MagicMock()
                mock_wm_instance.get_history = AsyncMock(return_value=[])
                mock_wm_instance.save_message = AsyncMock()
                mock_wm_instance.close = AsyncMock()
                mock_wm_cls.return_value = mock_wm_instance
                
                with patch("aegis.core.engine.ResearchAgent") as mock_research_cls:
                    with patch("aegis.core.engine.MemoryAgent") as mock_memory_cls:
                        with patch("aegis.core.engine.SemanticCache") as mock_cache_cls:
                            # Mocks dos agentes e cache
                            mock_research_cls.return_value = MagicMock()
                            mock_memory_cls.return_value = MagicMock()
                            
                            mock_cache = mock_cache_cls.return_value
                            mock_cache.get = AsyncMock(return_value=None)
                            mock_cache.set = AsyncMock()
                            
                            e = Engine()
                            e.agents["research"] = mock_research_cls.return_value
                            e.agents["memory"] = mock_memory_cls.return_value
                            # Desativa compressão nos testes de roteamento para simplificar
                            e.settings.ENABLE_CONTEXT_COMPRESSION = False
                            return e

@pytest.mark.asyncio
class TestRouting:
    async def test_routing_to_research(self, engine):
        # Setup mocks
        engine.llm_client.messages.create = AsyncMock()
        # Mock classificador para retornar 'research'
        engine.llm_client.messages.create.side_effect = [
            MagicMock(content=[MagicMock(text="research")]), # Classificação
        ]
        
        # Mock ResearchAgent
        engine.agents["research"].run = AsyncMock(return_value=AgentResult(
            success=True, output="Resultado da pesquisa", steps_taken=1, tools_used=["web_search"], error=None
        ))
        
        # Mock MemoryAgent methods
        engine.agents["memory"].pre_process = AsyncMock(return_value="Contexto de memoria")
        engine.agents["memory"].post_process = AsyncMock()

        user_input = UserInput(text="Quem ganhou o Oscar 2024?", session_id="test_session", mode=OperatingMode.STANDARD)
        response = await engine.process(user_input)

        assert response.agent_used == "research"
        assert "Resultado da pesquisa" in response.text
        engine.agents["research"].run.assert_called_once()

    async def test_routing_to_core_engine(self, engine):
        # Setup mocks
        engine.llm_client.messages.create = AsyncMock()
        # Mock classificador para retornar 'core_engine'
        engine.llm_client.messages.create.side_effect = [
            MagicMock(content=[MagicMock(text="core_engine")]), # Classificação
            MagicMock(content=[MagicMock(text="Olá, eu sou o AEGIS.")]), # Resposta do Core
        ]
        
        # Mock MemoryAgent methods
        engine.agents["memory"].pre_process = AsyncMock(return_value=None)
        engine.agents["memory"].post_process = AsyncMock()

        user_input = UserInput(text="Oi, quem e voce?", session_id="test_session", mode=OperatingMode.STANDARD)
        response = await engine.process(user_input)

        assert response.agent_used == "core_engine"
        assert "Olá, eu sou o AEGIS." in response.text
        engine.agents["research"].run.assert_not_called()

    async def test_classification_fallback(self, engine):
        # Setup mocks
        engine.llm_client.messages.create = AsyncMock()
        # Mock classificador para retornar algo invalido
        engine.llm_client.messages.create.side_effect = [
            MagicMock(content=[MagicMock(text="unknown_intent")]), # Classificação falha
            MagicMock(content=[MagicMock(text="Resposta de fallback")]), # Resposta do Core
        ]
        
        # Mock MemoryAgent
        engine.agents["memory"].pre_process = AsyncMock(return_value=None)
        engine.agents["memory"].post_process = AsyncMock()

        user_input = UserInput(text="Algum texto", session_id="test_session", mode=OperatingMode.STANDARD)
        response = await engine.process(user_input)

        assert response.agent_used == "core_engine"
        assert response.text == "Resposta de fallback"
