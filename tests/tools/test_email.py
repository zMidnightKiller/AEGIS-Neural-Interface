import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aegis.tools.email import EmailTool

@pytest.fixture
def tool():
    return EmailTool()

@pytest.mark.asyncio
async def test_email_send_simulation(tool):
    # Test simulation when credentials are missing
    mock_settings = MagicMock()
    mock_settings.EMAIL_SENDER = None
    mock_settings.EMAIL_PASSWORD = None
    
    with patch("aegis.tools.email.get_settings", return_value=mock_settings):
        result = await tool.execute(to="test@example.com", subject="Hello", body="World", action="send")
        assert result.success is True
        assert result.data["status"] == "simulated"

@pytest.mark.asyncio
async def test_email_read_mock(tool):
    result = await tool.execute(action="read")
    assert result.success is True
    assert len(result.data) == 2
    assert result.data[0]["subject"] == "Relatorio Trimestral"

@pytest.mark.asyncio
async def test_email_invalid_action(tool):
    result = await tool.execute(action="invalid")
    assert result.success is False
    assert "nao suportada" in result.error
