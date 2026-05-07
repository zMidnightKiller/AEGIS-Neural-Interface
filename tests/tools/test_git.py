import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aegis.tools.git import GitTool

@pytest.fixture
def tool():
    return GitTool()

@pytest.mark.asyncio
async def test_git_status_success(tool):
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"On branch main\nnothing to commit", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process
        
        result = await tool.execute(action="status", repo_path=".")
        assert result.success is True
        assert "On branch main" in result.data

@pytest.mark.asyncio
async def test_git_commit_success(tool):
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"[main 1234567] Auto-commit", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process
        
        result = await tool.execute(
            action="commit", 
            repo_path=".", 
            params={"message": "Test commit"}
        )
        assert result.success is True
        assert "Auto-commit" in result.data

@pytest.mark.asyncio
async def test_git_invalid_action(tool):
    # GitTool uses Literal, so this might cause a type error in some checkers,
    # but at runtime it should hit the 'else' block.
    result = await tool.execute(action="invalid", repo_path=".") # type: ignore
    assert result.success is False
    assert "desconhecida" in result.error
