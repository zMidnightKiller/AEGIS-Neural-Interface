import os
os.environ["ANTHROPIC_API_KEY"] = "fake-key-for-testing"

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from aegis.tools.web_fetch import WebFetchTool

@pytest.fixture
def tool():
    return WebFetchTool()

@pytest.mark.asyncio
class TestWebFetchTool:
    async def test_execute_success(self, tool):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()
        
        # Mocking robots.txt as well
        mock_robots = MagicMock()
        mock_robots.status_code = 200
        mock_robots.text = "User-agent: *\nAllow: /"

        with patch("httpx.AsyncClient.get") as mock_get:
            # First call for robots.txt, second for the actual page
            mock_get.side_effect = [mock_robots, mock_response]
            
            result = await tool.execute(url="https://example.com/page")
            
            assert result.success is True
            assert "Hello World" in result.data
            assert result.metadata["url"] == "https://example.com/page"

    async def test_blocked_by_robots(self, tool):
        mock_robots = MagicMock()
        mock_robots.status_code = 200
        mock_robots.text = "User-agent: *\nDisallow: /"

        with patch("httpx.AsyncClient.get", return_value=mock_robots):
            result = await tool.execute(url="https://example.com/secret")
            
            assert result.success is False
            assert "bloqueado pelo robots.txt" in result.error

    async def test_clean_html(self, tool):
        html = """
        <html>
            <head><style>.css{}</style></head>
            <body>
                <nav>Menu</nav>
                <header>Header</header>
                <main>
                    <h1>Title</h1>
                    <script>alert('hi')</script>
                    <p>Content</p>
                </main>
                <footer>Footer</footer>
            </body>
        </html>
        """
        clean = tool._clean_html(html)
        assert "Title Content" in clean
        assert "Menu" not in clean
        assert "Header" not in clean
        assert "Footer" not in clean
        assert "alert" not in clean

    async def test_http_error(self, tool):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)
        
        # Mocking robots.txt allowed
        mock_robots = MagicMock()
        mock_robots.status_code = 404 # robots.txt not found means allowed

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = [mock_robots, mock_response]
            result = await tool.execute(url="https://example.com/notfound")
            
            assert result.success is False
            assert "Erro HTTP 404" in result.error
