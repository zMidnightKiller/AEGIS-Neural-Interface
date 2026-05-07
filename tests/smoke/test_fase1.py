"""
tests/smoke/test_fase1.py

Smoke Test para a Fase 1 do AEGIS.
Valida o fluxo end-to-end: Engine + Context + Working Memory + Tools.
"""
import pytest
import json
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Definir variaveis de ambiente ficticias
os.environ["ANTHROPIC_API_KEY"] = "fake-key"
os.environ["TAVILY_API_KEY"] = "fake-key"

from aegis.core.engine import Engine
from aegis.core.models import UserInput, OperatingMode, AgentResponse
from aegis.tools.base import ToolResult

@pytest.fixture
def mock_env():
    """Moca todas as dependências externas (Redis, Tavily, Settings, Anthropic)."""
    with patch("aegis.core.engine.get_settings") as mock_engine_settings_fn, \
         patch("aegis.tools.web_search.get_settings") as mock_tool_settings_fn, \
         patch("aegis.memory.working.redis.from_url") as mock_redis_fn, \
         patch("aegis.tools.web_search.httpx.AsyncClient") as mock_httpx_fn, \
         patch("aegis.core.engine.AsyncAnthropic") as mock_anthropic_class, \
         patch("aegis.core.engine.MemoryAgent") as mock_memory_agent_class, \
         patch("aegis.agents.memory.EpisodicMemory") as mock_episodic_class, \
         patch("aegis.agents.memory.SemanticMemory") as mock_semantic_class, \
         patch("aegis.core.engine.SemanticCache") as mock_cache_class, \
         patch("aegis.core.engine.PluginManager") as mock_plugin_manager_class:
        
        # Setup Settings
        mock_settings = MagicMock()
        mock_settings.PROJECT_NAME = "AEGIS Smoke Test"
        mock_settings.VERSION = "1.0.0"
        mock_settings.REDIS_URL = "redis://localhost:6379"
        mock_settings.REDIS_SESSION_TTL = 3600
        mock_settings.CONTEXT_MAX_TOKENS = 4096
        mock_settings.AEGIS_MODE = "STANDARD"
        mock_settings.ANTHROPIC_API_KEY.get_secret_value.return_value = "fake-key"
        mock_settings.TAVILY_API_KEY.get_secret_value.return_value = "fake-key"
        mock_settings.ENABLE_SEMANTIC_CACHE = False
        mock_settings.ENABLE_CONTEXT_COMPRESSION = False
        mock_settings.CONTEXT_COMPRESSION_TOKEN_LIMIT = 3000
        
        mock_engine_settings_fn.return_value = mock_settings
        mock_tool_settings_fn.return_value = mock_settings
        
        # Setup Redis
        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = [] # Histórico vazio inicialmente
        mock_redis.rpush.return_value = 1
        mock_redis.expire.return_value = True
        mock_redis_fn.return_value = mock_redis
        
        # Setup HTTPX (Tavily)
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"title": "AEGIS Project", "url": "https://aegis.ai", "content": "A high-performance AI system."}
            ]
        }
        mock_client.post.return_value = mock_response
        mock_httpx_fn.return_value.__aenter__.return_value = mock_client

        # Setup Anthropic
        mock_anthropic = MagicMock()
        mock_anthropic_class.return_value = mock_anthropic
        
        # Setup Memory Mocks for Phase 2 compatibility
        mock_memory_agent = MagicMock()
        mock_memory_agent.pre_process = AsyncMock(return_value="Contexto de memoria mockado")
        mock_memory_agent.post_process = AsyncMock()
        mock_memory_agent_class.return_value = mock_memory_agent
        
        mock_episodic_class.return_value = MagicMock()
        mock_semantic_class.return_value = MagicMock()

        # Mock Cache e Plugins
        mock_cache_class.return_value = MagicMock()
        mock_plugin_manager_class.return_value = MagicMock()
        
        yield {
            "settings": mock_settings,
            "redis": mock_redis,
            "httpx": mock_client,
            "anthropic": mock_anthropic
        }

@pytest.mark.asyncio
async def test_fase1_full_flow(mock_env):
    """Valida o fluxo completo de uma requisição de pesquisa."""
    engine = Engine()
    
    # Mock do classificador
    engine._classify_intent = AsyncMock(return_value="research")
    
    session_id = "smoke-session-1"
    
    # 1. Primeira interação: Pesquisa
    user_input = UserInput(
        text="Faça uma pesquisa sobre o projeto AEGIS",
        session_id=session_id,
        mode=OperatingMode.STANDARD
    )
    
    # Mock do ResearchAgent para evitar chamadas reais (já testado em seu próprio módulo)
    with patch("aegis.core.engine.ResearchAgent") as mock_research_agent_class:
        mock_research_agent = MagicMock()
        mock_research_agent.run = AsyncMock(return_value=MagicMock(
            success=True,
            output="Resultado: AEGIS Project é um sistema de IA.",
            tools_used=["web_search"]
        ))
        mock_research_agent_class.return_value = mock_research_agent
        # Re-inicializar engine para pegar o mock do agente
        engine = Engine()
        engine._classify_intent = AsyncMock(return_value="research")
        
        response = await engine.process(user_input)
    
    # Verificações
    assert response.agent_used == "research"
    assert "web_search" in response.tools_used
    assert "AEGIS Project" in response.text
    
    # 2. Segunda interação: Contexto
    engine._classify_intent = AsyncMock(return_value="core_engine")
    mock_env["redis"].lrange.return_value = [
        json.dumps({"role": "user", "content": "Faça uma pesquisa sobre o projeto AEGIS"}),
        json.dumps({"role": "assistant", "content": response.text})
    ]
    
    # Mock da resposta do LLM para core_engine
    mock_llm_response = MagicMock()
    mock_llm_response.content = [MagicMock(text="Eu descobri que o projeto AEGIS é focado em performance.")]
    mock_env["anthropic"].messages.create = AsyncMock(return_value=mock_llm_response)
    
    user_input_2 = UserInput(
        text="O que você descobriu?",
        session_id=session_id,
        mode=OperatingMode.BRIEFING
    )
    
    response_2 = await engine.process(user_input_2)
    
    assert response_2.agent_used == "core_engine"
    assert response_2.memory_injected is True
    assert "descobri" in response_2.text

@pytest.mark.asyncio
async def test_fase1_operating_modes(mock_env):
    """Valida se os modos de operação alteram o comportamento."""
    engine = Engine()
    engine._classify_intent = AsyncMock(return_value="core_engine")
    
    # Mock da resposta do LLM
    mock_llm_response = MagicMock()
    mock_llm_response.content = [MagicMock(text="Resposta em modo ANALYSIS")]
    mock_env["anthropic"].messages.create = AsyncMock(return_value=mock_llm_response)
    
    user_input = UserInput(
        text="Teste de modo",
        session_id="mode-test",
        mode=OperatingMode.ANALYSIS
    )
    
    response = await engine.process(user_input)
    assert "ANALYSIS" in response.text
