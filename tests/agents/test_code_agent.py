"""
tests/agents/test_code_agent.py

Testes unitarios para o CodeAgent e GitTool.
"""
import os
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from aegis.agents.code import CodeAgent
from aegis.core.context import Context
from aegis.tools.base import ToolResult
from aegis.tools.git import GitTool

# Mock env vars
os.environ["ANTHROPIC_API_KEY"] = "test-key"

@pytest.fixture
def context():
    return Context(session_id="test_code_session")

@pytest.fixture
def mock_anthropic():
    client = AsyncMock()
    return client

class TestCodeAgent:
    @pytest.mark.asyncio
    async def test_code_agent_run_finish(self, context, mock_anthropic):
        # Mock do Claude finalizando a tarefa
        mock_message = MagicMock()
        mock_message.content = [
            MagicMock(text=json.dumps({
                "thought": "Tarefa concluida.",
                "finish": "O script foi corrigido e testado."
            }))
        ]
        mock_anthropic.messages.create = AsyncMock(return_value=mock_message)
        
        agent = CodeAgent(anthropic_client=mock_anthropic)
        result = await agent.run("Corrija o script main.py", context)
        
        assert result.success is True
        assert result.output == "O script foi corrigido e testado."
        assert result.steps_taken == 1

    @pytest.mark.asyncio
    async def test_code_agent_run_with_tools(self, context, mock_anthropic):
        # Passo 1: ler arquivo
        msg1 = MagicMock()
        msg1.content = [
            MagicMock(text=json.dumps({
                "thought": "Vou ler o arquivo main.py.",
                "tool": "file_system",
                "params": {"action": "read", "path": "main.py"}
            }))
        ]
        
        # Passo 2: executar codigo
        msg2 = MagicMock()
        msg2.content = [
            MagicMock(text=json.dumps({
                "thought": "Vou testar uma correção.",
                "tool": "run_code",
                "params": {"code": "print('hello')"}
            }))
        ]
        
        # Passo 3: finalizar
        msg3 = MagicMock()
        msg3.content = [
            MagicMock(text=json.dumps({
                "thought": "Tudo certo.",
                "finish": "Tarefa concluida com sucesso."
            }))
        ]
        
        mock_anthropic.messages.create = AsyncMock(side_effect=[msg1, msg2, msg3])
        
        with patch("aegis.agents.code.FileSystemTool") as MockFS, \
             patch("aegis.agents.code.RunCodeTool") as MockRun:
            
            MockFS.return_value.execute = AsyncMock(return_value=ToolResult(success=True, data="print('bug')"))
            MockFS.return_value.name = "file_system"
            
            MockRun.return_value.execute = AsyncMock(return_value=ToolResult(success=True, data="hello"))
            MockRun.return_value.name = "run_code"
            
            agent = CodeAgent(anthropic_client=mock_anthropic)
            result = await agent.run("Fix bug", context)
            
            assert result.success is True
            assert result.steps_taken == 3
            assert "file_system" in result.tools_used
            assert "run_code" in result.tools_used

class TestGitTool:
    @pytest.mark.asyncio
    async def test_git_tool_status(self):
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"On branch main", b"")
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc
            
            tool = GitTool()
            result = await tool.execute(action="status", repo_path=".")
            
            assert result.success is True
            assert "On branch main" in result.data

    @pytest.mark.asyncio
    async def test_git_tool_clone_missing_url(self):
        tool = GitTool()
        result = await tool.execute(action="clone", repo_path="new_repo")
        assert result.success is False
        assert "URL eh obrigatoria" in result.error
