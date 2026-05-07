import os
os.environ["ANTHROPIC_API_KEY"] = "fake-key-for-testing"

import pytest
from unittest.mock import MagicMock, patch
from aegis.tools.run_code import RunCodeTool
from aegis.core.config import Settings

@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.RUNCODE_DOCKER_IMAGE = "python:3.11-slim"
    settings.RUNCODE_TIMEOUT = 30
    return settings

@pytest.fixture
def tool():
    return RunCodeTool()

@pytest.mark.asyncio
class TestRunCodeTool:
    async def test_execute_success(self, tool, mock_settings):
        mock_container = MagicMock()
        mock_container.status = 'exited'
        mock_container.logs.return_value = b"hello from docker"
        mock_container.wait.return_value = {'StatusCode': 0}
        
        mock_docker_client = MagicMock()
        mock_docker_client.from_env.return_value = mock_docker_client
        mock_docker_client.containers.run.return_value = mock_container
        
        with patch("aegis.tools.run_code.get_settings", return_value=mock_settings), \
             patch("aegis.tools.run_code.docker", mock_docker_client):
            
            result = await tool.execute(code="print('hello from docker')")
            
            assert result.success is True
            assert result.data == "hello from docker"
            mock_docker_client.containers.run.assert_called_once()

    async def test_execute_failure(self, tool, mock_settings):
        mock_container = MagicMock()
        mock_container.status = 'exited'
        mock_container.logs.return_value = b"error trace"
        mock_container.wait.return_value = {'StatusCode': 1}
        
        mock_docker_client = MagicMock()
        mock_docker_client.from_env.return_value = mock_docker_client
        mock_docker_client.containers.run.return_value = mock_container
        
        with patch("aegis.tools.run_code.get_settings", return_value=mock_settings), \
             patch("aegis.tools.run_code.docker", mock_docker_client):
            
            result = await tool.execute(code="exit(1)")
            
            assert result.success is False
            assert "error trace" in result.data
            assert "exit code 1" in result.error

    async def test_docker_not_installed(self, tool, mock_settings):
        with patch("aegis.tools.run_code.docker", None), \
             patch("aegis.tools.run_code.get_settings", return_value=mock_settings):
            
            result = await tool.execute(code="print('hi')")
            assert result.success is False
            assert "não instalada" in result.error
