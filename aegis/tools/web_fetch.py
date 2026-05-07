"""
aegis/tools/web_fetch.py

Ferramenta para extrair conteudo de URLs.
Implementa limpeza basica de HTML e respeita robots.txt.
"""
from __future__ import annotations

import re
import structlog
import httpx
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

from aegis.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)


class WebFetchTool(BaseTool):
    """Extrai o conteudo de texto de uma URL especifica."""

    name: str = "web_fetch"
    description: str = (
        "Extrai o conteudo de uma URL. "
        "Use apos encontrar links relevantes via web_search."
    )
    parameters: dict[str, Any] = {
        "url": "A URL completa para extrair o conteudo.",
        "ignore_robots": "Se True, ignora o robots.txt (padrao: False)."
    }

    async def _can_fetch(self, url: str) -> bool:
        """Verifica se a URL pode ser acessada conforme robots.txt."""
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(robots_url)
                if response.status_code == 200:
                    rp = RobotFileParser()
                    rp.parse(response.text.splitlines())
                    return rp.can_fetch("*", url)
        except Exception as e:
            logger.warning("web_fetch.robots_check_failed", url=url, error=str(e))
            # Se falhar ao ler robots.txt, assumimos que podemos ler (degradacao graciosa)
            return True
        
        return True

    def _clean_html(self, html: str) -> str:
        """Remocao basica de tags HTML e excesso de espacos."""
        # Remove scripts e estilos
        html = re.sub(r'<(script|style|header|footer|nav)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove tags HTML
        text = re.sub(r'<[^>]+>', ' ', html)
        # Normaliza espacos
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    async def execute(self, url: str, ignore_robots: bool = False) -> ToolResult:
        """
        Executa o fetch da URL.

        Args:
            url: URL para acessar.
            ignore_robots: Se deve ignorar a verificacao de robots.txt.

        Returns:
            ToolResult com o texto extraido.
        """
        logger.info("web_fetch.executing", url=url)

        if not ignore_robots:
            allowed = await self._can_fetch(url)
            if not allowed:
                logger.warning("web_fetch.blocked_by_robots", url=url)
                return ToolResult(
                    success=False,
                    error=f"Acesso a {url} bloqueado pelo robots.txt do site.",
                    metadata={"url": url}
                )

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "AEGIS-AI/1.0 (Research Agent; +https://github.com/luan/aegis)"
                }
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                raw_html = response.text
                clean_text = self._clean_html(raw_html)
                
                # Limita o tamanho do texto retornado para evitar estourar contexto
                if len(clean_text) > 10000:
                    clean_text = clean_text[:10000] + "... [truncado]"

                logger.info("web_fetch.success", url=url, length=len(clean_text))
                return ToolResult(
                    success=True,
                    data=clean_text,
                    metadata={"url": url, "content_type": response.headers.get("content-type")}
                )

        except httpx.HTTPStatusError as e:
            logger.error("web_fetch.http_error", url=url, status=e.response.status_code)
            return ToolResult(success=False, error=f"Erro HTTP {e.response.status_code}", metadata={"url": url})
        except Exception as e:
            logger.error("web_fetch.unexpected_error", url=url, error=str(e))
            return ToolResult(success=False, error=f"Erro ao acessar URL: {str(e)}", metadata={"url": url})
