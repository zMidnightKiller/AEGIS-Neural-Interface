import os
os.environ["ANTHROPIC_API_KEY"] = "fake-key-for-testing"

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from aegis.tools.file_system import FileSystemTool
from aegis.tools.base import ToolResult
from aegis.core.config import Settings

@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.ALLOWED_FS_PATHS = ["./data", "./.tmp"]
    return settings

@pytest.fixture
def tool():
    return FileSystemTool()

@pytest.mark.asyncio
class TestFileSystemTool:
    async def test_is_path_allowed(self, tool, mock_settings):
        with patch("aegis.tools.file_system.get_settings", return_value=mock_settings):
            # Resolve the mock paths relative to current dir for comparison
            mock_settings.ALLOWED_FS_PATHS = [str(Path("./data").resolve()), str(Path("./.tmp").resolve())]
            
            assert tool._is_path_allowed("./data/test.txt") is True
            assert tool._is_path_allowed("./.tmp/log.txt") is True
            assert tool._is_path_allowed("/etc/passwd") is False
            assert tool._is_path_allowed("../outside.txt") is False

    async def test_read_file(self, tool, tmp_path, mock_settings):
        test_file = tmp_path / "data" / "test.txt"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("hello world", encoding="utf-8")
        
        mock_settings.ALLOWED_FS_PATHS = [str(tmp_path.resolve())]
        
        with patch("aegis.tools.file_system.get_settings", return_value=mock_settings):
            result = await tool.execute(action="read", path=str(test_file))
            
            assert result.success is True
            assert result.data == "hello world"

    async def test_write_file(self, tool, tmp_path, mock_settings):
        test_file = tmp_path / "data" / "new.txt"
        mock_settings.ALLOWED_FS_PATHS = [str(tmp_path.resolve())]
        
        with patch("aegis.tools.file_system.get_settings", return_value=mock_settings):
            result = await tool.execute(action="write", path=str(test_file), content="new content")
            
            assert result.success is True
            assert test_file.read_text(encoding="utf-8") == "new content"

    async def test_list_dir(self, tool, tmp_path, mock_settings):
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "file1.txt").touch()
        (data_dir / "file2.txt").touch()
        
        mock_settings.ALLOWED_FS_PATHS = [str(tmp_path.resolve())]
        
        with patch("aegis.tools.file_system.get_settings", return_value=mock_settings):
            result = await tool.execute(action="list", path=str(data_dir))
            
            assert result.success is True
            assert "file1.txt" in result.data
            assert "file2.txt" in result.data

    async def test_denied_path(self, tool, mock_settings):
        mock_settings.ALLOWED_FS_PATHS = ["./data"]
        with patch("aegis.tools.file_system.get_settings", return_value=mock_settings):
            result = await tool.execute(action="read", path="/unauthorized/path.txt")
            assert result.success is False
            assert "Acesso negado" in result.error
