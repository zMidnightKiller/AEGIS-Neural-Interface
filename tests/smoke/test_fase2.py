"""
tests/smoke/test_fase2.py

Smoke Test para a Fase 2 do AEGIS.
Valida o fluxo end-to-end integrando Memoria Episodica, Semantica e Agentes.
"""
import pytest
import json
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Definir variaveis de ambiente ficticias para evitar ValidationErrors
os.environ["ANTHROPIC_API_KEY"] = "fake-key"
os.environ["OPENAI_API_KEY"] = "fake-key"
os.environ["TAVILY_API_KEY"] = "fake-key"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["CHROMA_PERSIST_DIR"] = "./.tmp/chroma_test"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_PASSWORD"] = "fake-password"

from aegis.core.engine import Engine
from aegis.core.models import UserInput, OperatingMode, AgentResponse

@pytest.fixture
def mock_fase2_env():
    """Moca todas as dependencias externas para a Fase 2."""
    # Mocking AsyncAnthropic in all modules that use it
    with patch("aegis.core.engine.AsyncAnthropic") as mock_anthropic_engine_fn, \
         patch("aegis.memory.semantic.AsyncAnthropic") as mock_anthropic_semantic_fn, \
         patch("aegis.agents.research.AsyncAnthropic") as mock_anthropic_research_fn, \
         patch("aegis.core.config.get_settings") as mock_settings_fn, \
         patch("aegis.memory.working.redis.from_url") as mock_redis_fn, \
         patch("aegis.memory.episodic.chromadb.PersistentClient") as mock_chroma_fn, \
         patch("aegis.memory.semantic.AsyncGraphDatabase.driver") as mock_neo4j_fn, \
         patch("aegis.tools.web_search.httpx.AsyncClient") as mock_httpx_search_fn, \
         patch("aegis.tools.web_fetch.httpx.AsyncClient") as mock_httpx_fetch_fn:
        
        # Setup Settings
        mock_settings = MagicMock()
        mock_settings.PROJECT_NAME = "AEGIS Smoke Test Fase 2"
        mock_settings.VERSION = "1.0.0"
        mock_settings.REDIS_URL = "redis://localhost:6379"
        mock_settings.REDIS_SESSION_TTL = 3600
        mock_settings.CHROMA_PERSIST_DIR = "./.tmp/chroma_test"
        mock_settings.ANTHROPIC_API_KEY.get_secret_value.return_value = "fake-key"
        mock_settings.OPENAI_API_KEY.get_secret_value.return_value = "fake-key"
        mock_settings.TAVILY_API_KEY.get_secret_value.return_value = "fake-key"
        mock_settings.NEO4J_PASSWORD.get_secret_value.return_value = "fake-password"
        mock_settings.AEGIS_USER_NAME = "TestUser"
        mock_settings.CONTEXT_MAX_TOKENS = 4096
        
        # Define fields directly to bypass some Pydantic-like checks if any
        mock_settings.ANTHROPIC_API_KEY.__bool__.return_value = True
        mock_settings.OPENAI_API_KEY.__bool__.return_value = True
        mock_settings.TAVILY_API_KEY.__bool__.return_value = True
        
        mock_settings_fn.return_value = mock_settings
        
        # Setup Redis
        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = []
        mock_redis_fn.return_value = mock_redis
        
        # Setup ChromaDB
        mock_chroma_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["Fato de sessao anterior"]],
            "distances": [[0.1]], # 0.1 distancia = 0.9 similaridade
            "metadatas": [[{"session_id": "prev-session"}]]
        }
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        mock_chroma_fn.return_value = mock_chroma_client
        
        # Setup Neo4j
        mock_neo4j_driver = MagicMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = iter([
            {"relation": "PREFERS", "entity": "Python"}
        ])
        mock_session.run.return_value = mock_result
        mock_neo4j_driver.session.return_value.__aenter__.return_value = mock_session
        mock_neo4j_fn.return_value = mock_neo4j_driver
        
        # Setup Anthropic Common
        def setup_anthropic_mock(mock_class):
            m = MagicMock()
            m.messages = MagicMock()
            m.messages.create = AsyncMock()
            mock_class.return_value = m
            return m

        mock_anthropic_engine = setup_anthropic_mock(mock_anthropic_engine_fn)
        mock_anthropic_semantic = setup_anthropic_mock(mock_anthropic_semantic_fn)
        mock_anthropic_research = setup_anthropic_mock(mock_anthropic_research_fn)
        
        # Setup HTTPX
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Contedo da pagina Python 3.12</body></html>"
        mock_response.json.return_value = {
            "results": [
                {"title": "Python 3.12 Features", "url": "https://python.org", "content": "New features in Python 3.12 include f-string improvements."}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.post.return_value = mock_response
        
        mock_httpx_search_fn.return_value.__aenter__.return_value = mock_client
        mock_httpx_fetch_fn.return_value.__aenter__.return_value = mock_client
        
        yield {
            "settings": mock_settings,
            "redis": mock_redis,
            "chroma": mock_collection,
            "neo4j": mock_session,
            "anthropic_engine": mock_anthropic_engine,
            "anthropic_semantic": mock_anthropic_semantic,
            "anthropic_research": mock_anthropic_research,
            "httpx": mock_client
        }

@pytest.mark.asyncio
async def test_fase2_memory_integration(mock_fase2_env):
    """
    Valida se o MemoryAgent persiste fatos e recupera memorias.
    """
    engine = Engine()
    
    # 1. Mock do Classificador e Resposta LLM
    engine._classify_intent = AsyncMock(return_value="core_engine")
    
    mock_llm_response = MagicMock()
    mock_llm_response.content = [MagicMock(text="Entendido, TestUser. Voce gosta de Python.")]
    mock_fase2_env["anthropic_engine"].messages.create.return_value = mock_llm_response
    
    # 2. Mock do MemoryAgent para extracao (Semantic Memory)
    mock_extraction_response = MagicMock()
    mock_extraction_response.content = [MagicMock(text=json.dumps({
        "user_name": "TestUser",
        "preferences": [{"entity": "Python", "relation": "PREFERS"}],
        "facts": []
    }))]
    mock_fase2_env["anthropic_semantic"].messages.create.return_value = mock_extraction_response
    
    # Execucao
    user_input = UserInput(
        text="Eu prefiro programar em Python.",
        session_id="session-fase2-smoke",
        mode=OperatingMode.STANDARD
    )
    
    response = await engine.process(user_input)
    
    # Verificacoes
    mock_fase2_env["chroma"].query.assert_called()
    mock_fase2_env["neo4j"].run.assert_called()
    mock_fase2_env["chroma"].add.assert_called()
    
    assert "Python" in response.text
    assert response.memory_injected is True

@pytest.mark.asyncio
async def test_fase2_research_agent(mock_fase2_env):
    """
    Valida se o ResearchAgent entrega um relatorio com fontes.
    """
    engine = Engine()
    
    # Mock do Classificador
    engine._classify_intent = AsyncMock(return_value="research")
    
    # Mock do LLM para o ResearchAgent gerar o relatorio
    mock_report_response = MagicMock()
    mock_report_response.content = [MagicMock(text=json.dumps({
        "summary": "RESEARCH REPORT: Python 3.12 is out.",
        "confidence_score": 0.95,
        "key_findings": ["F-strings improved"]
    }))]
    mock_fase2_env["anthropic_research"].messages.create.return_value = mock_report_response
    
    user_input = UserInput(
        text="Quais as novidades do Python 3.12?",
        session_id="research-test",
        mode=OperatingMode.STANDARD
    )
    
    response = await engine.process(user_input)
    
    assert response.agent_used == "research"
    assert "Python 3.12" in response.text
    assert "web_search" in response.tools_used
    assert "web_fetch" in response.tools_used
