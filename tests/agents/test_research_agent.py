"""
tests/agents/test_research_agent.py

Testes unitarios para o ResearchAgent.
"""
import os
# Definir env vars antes de importar qualquer modulo que instancie Settings
os.environ["ANTHROPIC_API_KEY"] = "fake_key"

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from aegis.agents.research import ResearchAgent
from aegis.agents.base import AgentResult
from aegis.core.context import Context
from aegis.tools.base import ToolResult

@pytest.fixture(autouse=True)
def mock_settings():
    with patch("aegis.core.config.get_settings") as mock:
        mock_settings = MagicMock()
        mock_settings.ANTHROPIC_API_KEY.get_secret_value.return_value = "fake_key"
        mock_settings.TAVILY_API_KEY.get_secret_value.return_value = "fake_key"
        mock.return_value = mock_settings
        yield mock

@pytest.fixture
def context():
    return Context(session_id="test_session")

@pytest.fixture
def mock_anthropic():
    client = AsyncMock()
    # Mock da resposta do Claude
    mock_message = MagicMock()
    mock_message.content = [
        MagicMock(text=json.dumps({
            "summary": "Resumo de teste da pesquisa.",
            "confidence_score": 0.9,
            "key_findings": ["Descoberta 1", "Descoberta 2"]
        }))
    ]
    client.messages.create = AsyncMock(return_value=mock_message)
    return client

class TestResearchAgent:
    @pytest.mark.asyncio
    async def test_research_agent_run_success(self, context, mock_anthropic):
        # Setup mocks para as ferramentas
        with patch("aegis.agents.research.WebSearchTool") as MockSearch, \
             patch("aegis.agents.research.WebFetchTool") as MockFetch:
            
            # Mock Search
            mock_search_inst = MockSearch.return_value
            mock_search_inst.execute = AsyncMock(return_value=ToolResult(
                success=True,
                data=[
                    {"title": "Resultado 1", "url": "https://test1.com", "content": "Snippet 1"},
                    {"title": "Resultado 2", "url": "https://test2.com", "content": "Snippet 2"}
                ]
            ))
            mock_search_inst.name = "web_search"
            
            # Mock Fetch
            mock_fetch_inst = MockFetch.return_value
            mock_fetch_inst.execute = AsyncMock(return_value=ToolResult(
                success=True,
                data="Conteudo extraido da pagina de teste."
            ))
            mock_fetch_inst.name = "web_fetch"
            
            agent = ResearchAgent(anthropic_client=mock_anthropic)
            result = await agent.run("Quem ganhou a copa de 2022?", context)
            
            assert result.success is True
            assert "Relatório de Pesquisa" in result.output
            assert "Descoberta 1" in result.output
            assert result.steps_taken > 0
            assert "web_search" in result.tools_used
            assert "web_fetch" in result.tools_used

    @pytest.mark.asyncio
    async def test_research_agent_handle_search_failure(self, context, mock_anthropic):
        with patch("aegis.agents.research.WebSearchTool") as MockSearch:
            mock_search_inst = MockSearch.return_value
            mock_search_inst.execute = AsyncMock(return_value=ToolResult(
                success=False,
                error="Erro na busca"
            ))
            mock_search_inst.name = "web_search"
            
            agent = ResearchAgent(anthropic_client=mock_anthropic)
            result = await agent.run("Query invalida", context)
            
            assert result.success is False
            assert "Falha ao realizar busca inicial" in result.output

    @pytest.mark.asyncio
    async def test_research_agent_partial_fetch_success(self, context, mock_anthropic):
        with patch("aegis.agents.research.WebSearchTool") as MockSearch, \
             patch("aegis.agents.research.WebFetchTool") as MockFetch:
            
            mock_search_inst = MockSearch.return_value
            mock_search_inst.execute = AsyncMock(return_value=ToolResult(
                success=True,
                data=[{"title": "R1", "url": "url1"}]
            ))
            mock_search_inst.name = "web_search"
            
            mock_fetch_inst = MockFetch.return_value
            mock_fetch_inst.execute = AsyncMock(return_value=ToolResult(
                success=False,
                error="Erro no fetch"
            ))
            mock_fetch_inst.name = "web_fetch"
            
            agent = ResearchAgent(anthropic_client=mock_anthropic)
            result = await agent.run("Query test", context)
            
            # Deve continuar mesmo com falha no fetch (usa snippet)
            assert result.success is True
            assert mock_anthropic.messages.create.called
