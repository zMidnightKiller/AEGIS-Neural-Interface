"""
aegis/tools/browser.py

Ferramenta de navegacao web automatizada via Playwright.
Permite acessar paginas, interagir com elementos e extrair conteudo ou screenshots.
"""
from __future__ import annotations

import asyncio
import structlog
from typing import Any, Literal, Optional

from aegis.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("browser.playwright_not_installed", message="Playwright nao esta instalado. BrowserTool operara em modo degradado.")


class BrowserTool(BaseTool):
    """Navega na web, interage com sites e extrai dados via Playwright."""

    name: str = "browser"
    description: str = (
        "Navega na web usando um navegador real. Pode clicar, preencher formularios, "
        "tirar screenshots e extrair conteudo de paginas complexas (SPA/JS)."
    )
    parameters: dict[str, Any] = {
        "action": "Acao: 'goto', 'click', 'fill', 'screenshot', 'content', 'evaluate'.",
        "url": "URL para navegar (para 'goto').",
        "selector": "Seletor CSS/XPath (para 'click', 'fill').",
        "value": "Texto para preencher (para 'fill').",
        "path": "Caminho para salvar o screenshot (para 'screenshot').",
        "wait_for": "Seletor para aguardar apos navegar (opcional)."
    }

    def __init__(self):
        super().__init__()
        self._browser: Optional[Browser] = None
        self._playwright = None

    async def _get_page(self) -> Page:
        """Inicializa o browser se necessario e retorna uma nova pagina."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright nao instalado. Execute 'pip install playwright' e 'playwright install'.")
        
        if not self._playwright:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
        
        # Usamos uma unica pagina por simplicidade neste MVP, ou criamos novas conforme demanda
        context = await self._browser.new_context()
        return await context.new_page()

    async def execute(self, action: str, **kwargs) -> ToolResult:
        """
        Executa uma acao no navegador.
        """
        logger.info("browser.executing", action=action, params=kwargs)
        
        if not PLAYWRIGHT_AVAILABLE:
            return ToolResult(
                success=False, 
                error="Playwright nao esta disponivel no ambiente. Instale as dependencias para usar o BrowserTool.",
                metadata={"action": action}
            )

        try:
            # Em uma implementacao de longo prazo, manteriamos o browser aberto entre chamadas
            # ou usariamos um gerenciador de contexto. Para este MVP, vamos abrir/fechar se necessario.
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                result = await self._perform_action(page, action, kwargs)
                
                await browser.close()
                return result

        except Exception as e:
            logger.error("browser.error", error=str(e), action=action)
            return ToolResult(success=False, error=f"Erro no navegador: {str(e)}", metadata={"action": action})

    async def _perform_action(self, page: Page, action: str, kwargs: dict[str, Any]) -> ToolResult:
        """Executa a acao especifica na pagina fornecida."""
        
        if action == "goto":
            url = kwargs.get("url")
            if not url:
                return ToolResult(success=False, error="URL eh obrigatoria para 'goto'.")
            
            response = await page.goto(url, wait_until="networkidle")
            if kwargs.get("wait_for"):
                await page.wait_for_selector(kwargs["wait_for"], timeout=10000)
            
            return ToolResult(
                success=True, 
                data={"url": page.url, "status": response.status if response else None},
                metadata={"action": "goto"}
            )

        elif action == "content":
            content = await page.content()
            return ToolResult(success=True, data=content, metadata={"url": page.url, "action": "content"})

        elif action == "screenshot":
            path = kwargs.get("path", ".tmp/screenshot.png")
            await page.screenshot(path=path)
            return ToolResult(success=True, data={"path": path}, metadata={"url": page.url, "action": "screenshot"})

        elif action == "click":
            selector = kwargs.get("selector")
            if not selector:
                return ToolResult(success=False, error="Seletor eh obrigatorio para 'click'.")
            await page.click(selector)
            return ToolResult(success=True, data={"selector": selector}, metadata={"url": page.url, "action": "click"})

        elif action == "fill":
            selector = kwargs.get("selector")
            value = kwargs.get("value", "")
            if not selector:
                return ToolResult(success=False, error="Seletor eh obrigatorio para 'fill'.")
            await page.fill(selector, value)
            return ToolResult(success=True, data={"selector": selector, "value": value}, metadata={"url": page.url, "action": "fill"})

        elif action == "evaluate":
            script = kwargs.get("script")
            if not script:
                return ToolResult(success=False, error="Script eh obrigatorio para 'evaluate'.")
            res = await page.evaluate(script)
            return ToolResult(success=True, data=res, metadata={"url": page.url, "action": "evaluate"})

        else:
            return ToolResult(success=False, error=f"Acao de navegador desconhecida: {action}")
