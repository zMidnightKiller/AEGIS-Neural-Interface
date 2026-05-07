import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aegis.tools.browser import BrowserTool

@pytest.fixture
def tool():
    return BrowserTool()

@pytest.mark.asyncio
async def test_browser_goto_success(tool):
    with patch("aegis.tools.browser.async_playwright") as mock_pw:
        # Mocking the context manager 'async with async_playwright() as p'
        mock_p = mock_pw.return_value.__aenter__.return_value
        mock_browser = AsyncMock()
        mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
        
        mock_page = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.url = "https://example.com"
        
        result = await tool.execute(action="goto", url="https://example.com")
        
        assert result.success is True
        assert result.data["url"] == "https://example.com"
        assert result.data["status"] == 200

@pytest.mark.asyncio
async def test_browser_content_success(tool):
    with patch("aegis.tools.browser.async_playwright") as mock_pw:
        mock_p = mock_pw.return_value.__aenter__.return_value
        mock_browser = AsyncMock()
        mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_page = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        
        mock_page.content = AsyncMock(return_value="<html><body>Hello</body></html>")
        mock_page.url = "https://example.com"
        
        result = await tool.execute(action="content")
        
        assert result.success is True
        assert "Hello" in result.data

@pytest.mark.asyncio
async def test_browser_invalid_action(tool):
    with patch("aegis.tools.browser.async_playwright") as mock_pw:
        mock_p = mock_pw.return_value.__aenter__.return_value
        mock_browser = AsyncMock()
        mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_page = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        
        result = await tool.execute(action="invalid")
        
        assert result.success is False
        assert "desconhecida" in result.error
