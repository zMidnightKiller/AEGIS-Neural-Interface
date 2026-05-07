"""
tests/agents/test_memory_agent.py

Testes unitarios para o MemoryAgent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aegis.agents.memory import MemoryAgent
from aegis.core.context import Context
from aegis.agents.base import AgentResult

@pytest.fixture
def mock_episodic():
    return AsyncMock()

@pytest.fixture
def mock_semantic():
    return AsyncMock()

@pytest.fixture
def context():
    ctx = MagicMock(spec=Context)
    ctx.metadata = {"user_name": "test_user"}
    return ctx

@pytest.fixture
def agent(mock_episodic, mock_semantic):
    return MemoryAgent(episodic=mock_episodic, semantic=mock_semantic)

@pytest.mark.asyncio
class TestMemoryAgent:
    async def test_pre_process_injects_episodic_memory(self, agent, mock_episodic, mock_semantic, context):
        # Setup
        mock_episodic.search_similar.return_value = [
            {"content": "O usuario gosta de pizza.", "similarity": 0.9}
        ]
        mock_semantic.get_user_profile.return_value = []
        
        # Execute
        result = await agent.pre_process("O que eu gosto?", context)
        
        # Assert
        assert "### Memorias Episodicas Relevantes:" in result
        assert "O usuario gosta de pizza." in result
        mock_episodic.search_similar.assert_called_once()

    async def test_pre_process_injects_semantic_memory(self, agent, mock_episodic, mock_semantic, context):
        # Setup
        mock_episodic.search_similar.return_value = []
        mock_semantic.get_user_profile.return_value = [
            {"relation": "PREFERS", "entity": "Python"}
        ]
        
        # Execute
        result = await agent.pre_process("Qual minha linguagem favorita?", context)
        
        # Assert
        assert "### Preferencias e Fatos do Usuario:" in result
        assert "o usuario prefers python" in result.lower()
        mock_semantic.get_user_profile.assert_called_once()

    async def test_post_process_persists_interaction(self, agent, mock_episodic, mock_semantic):
        # Execute
        await agent.post_process("Usuario: Ola. Assistente: Oi.")
        
        # Assert
        mock_episodic.save_episode.assert_called_once()
        mock_semantic.extract_entities_from_text.assert_called_once()

    async def test_run_returns_success(self, agent, context):
        # Execute
        result = await agent.run("Limpar cache", context)
        
        # Assert
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert "Limpar cache" in result.output
