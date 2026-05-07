"""
tests/tools/test_web_search.py

Testes unitários para a WebSearchTool.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aegis.tools.base import ToolResult
from aegis.tools.web_search import WebSearchTool


@pytest.fixture
def tool() -> WebSearchTool:
    return WebSearchTool()


@pytest.mark.asyncio
class TestWebSearchTool:
    """Suíte de testes para a ferramenta de busca web."""

    async def test_returns_results_on_valid_query(self, tool: WebSearchTool) -> None:
        """Testa se a ferramenta retorna resultados em uma consulta válida."""
        mock_response_data = {
            "results": [
                {
                    "title": "Python Async",
                    "url": "https://example.com/async",
                    "content": "Learning async...",
                }
            ]
        }

        # Mock do httpx.Response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response_data
        mock_resp.raise_for_status.return_value = None

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            with patch("aegis.tools.web_search.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    TAVILY_API_KEY=MagicMock(get_secret_value=lambda: "fake-key")
                )

                result = await tool.execute("Python async patterns")

        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["title"] == "Python Async"
        assert result.metadata["total_results"] == 1

    async def test_returns_error_on_rate_limit(self, tool: WebSearchTool) -> None:
        """Testa o tratamento de rate limit (429)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 429

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            with patch("aegis.tools.web_search.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    TAVILY_API_KEY=MagicMock(get_secret_value=lambda: "fake-key")
                )

                result = await tool.execute("any query")

        assert result.success is False
        assert "Rate limit" in result.error
        assert result.metadata["status_code"] == 429

    async def test_missing_api_key(self, tool: WebSearchTool) -> None:
        """Testa o comportamento quando a chave de API está ausente."""
        with patch("aegis.tools.web_search.get_settings") as mock_settings:
            mock_settings.return_value.TAVILY_API_KEY = None

            result = await tool.execute("query")

        assert result.success is False
        assert "não configurada" in result.error

    async def test_handles_http_error(self, tool: WebSearchTool) -> None:
        """Testa o tratamento de erros HTTP genéricos."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            # Simulando erro de status sem raise_for_status explícito no mock pois usamos except HTTPStatusError
            import httpx
            
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 500
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Internal Server Error", request=MagicMock(), response=mock_resp
            )
            mock_post.return_value = mock_resp

            with patch("aegis.tools.web_search.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    TAVILY_API_KEY=MagicMock(get_secret_value=lambda: "fake-key")
                )

                result = await tool.execute("query")

        assert result.success is False
        assert "Erro na API Tavily: 500" in result.error
