"""
aegis/tools/web_search.py

Ferramenta de busca web via Tavily API.
Retorna resultados ranqueados com titulo, URL, snippet e score de relevancia.
"""
from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from aegis.core.config import get_settings
from aegis.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)


class WebSearchTool(BaseTool):
    """Busca informações em tempo real na web via Tavily API."""

    name: str = "web_search"
    description: str = (
        "Busca informações atuais na internet. "
        "Use para fatos recentes, notícias ou dados em tempo real."
    )
    parameters: dict[str, Any] = {
        "query": "Termos de busca em linguagem natural.",
        "num_results": "Número de resultados (1-10). Padrão: 5."
    }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=8))
    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        """
        Executa busca web via Tavily.

        Args:
            query: Termos de busca em linguagem natural.
            num_results: Número de resultados (1-10).

        Returns:
            ToolResult com lista de resultados ou mensagem de erro.
        """
        settings = get_settings()
        api_key = settings.TAVILY_API_KEY

        if not api_key:
            logger.error("web_search.missing_api_key")
            return ToolResult(
                success=False,
                error="TAVILY_API_KEY não configurada no ambiente.",
                metadata={"query": query},
            )

        api_key_str = api_key.get_secret_value()

        logger.info("web_search.executing", query=query, num_results=num_results)

        payload = {
            "api_key": api_key_str,
            "query": query,
            "search_depth": "smart",
            "max_results": num_results,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post("https://api.tavily.com/search", json=payload)

                if response.status_code == 429:
                    logger.warning("web_search.rate_limit")
                    return ToolResult(
                        success=False,
                        error="Rate limit atingido na API Tavily.",
                        metadata={"status_code": 429},
                    )

                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                logger.info("web_search.success", count=len(results))

                return ToolResult(
                    success=True,
                    data=results,
                    metadata={"query": query, "total_results": len(results)},
                )

            except httpx.HTTPStatusError as e:
                logger.error("web_search.http_error", status_code=e.response.status_code, error=str(e))
                return ToolResult(
                    success=False,
                    error=f"Erro na API Tavily: {e.response.status_code}",
                    metadata={"error_detail": str(e)},
                )
            except httpx.RequestError as e:
                logger.error("web_search.request_error", error=str(e))
                return ToolResult(
                    success=False,
                    error=f"Erro de conexão com Tavily: {str(e)}",
                    metadata={"error_type": type(e).__name__},
                )
            except Exception as e:
                logger.error("web_search.unexpected_error", error=str(e))
                return ToolResult(
                    success=False,
                    error=f"Erro inesperado na busca: {str(e)}",
                    metadata={"error_type": type(e).__name__},
                )
