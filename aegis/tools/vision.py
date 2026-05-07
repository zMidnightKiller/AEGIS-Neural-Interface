"""
aegis/tools/vision.py

Ferramenta de visão computacional para análise e descrição de imagens.
Utiliza a API Anthropic (Claude 3 Vision) como motor principal.
"""
from __future__ import annotations

import base64
import os
from typing import Any

import httpx
import structlog
from anthropic import AsyncAnthropic

from aegis.core.config import get_settings
from aegis.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)


class VisionTool(BaseTool):
    """Analisa e descreve o conteúdo de imagens."""

    name: str = "vision"
    description: str = (
        "Analisa imagens e responde perguntas sobre seu conteúdo. "
        "Recebe o caminho do arquivo ou URL da imagem e uma pergunta/instrução."
    )

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncAnthropic(api_key=self.settings.ANTHROPIC_API_KEY.get_secret_value())

    async def execute(self, image_source: str, prompt: str = "Descreva esta imagem em detalhes.") -> ToolResult:
        """
        Executa a análise de visão.

        Args:
            image_source: Caminho local ou URL da imagem.
            prompt: O que analisar na imagem.

        Returns:
            ToolResult com a descrição ou erro.
        """
        logger.info("vision.executing", source=image_source, prompt=prompt)

        try:
            image_data = await self._get_image_data(image_source)
            media_type = self._get_media_type(image_source)

            message = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )

            description = message.content[0].text
            return ToolResult(success=True, data=description)

        except Exception as e:
            logger.error("vision.error", error=str(e))
            return ToolResult(success=False, error=f"Erro ao analisar imagem: {str(e)}")

    async def _get_image_data(self, source: str) -> str:
        """Obtém dados da imagem em base64."""
        if source.startswith(("http://", "https://")):
            async with httpx.AsyncClient() as client:
                response = await client.get(source)
                response.raise_for_status()
                return base64.b64encode(response.content).decode("utf-8")
        else:
            if not os.path.exists(source):
                raise FileNotFoundError(f"Arquivo não encontrado: {source}")
            with open(source, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

    def _get_media_type(self, source: str) -> str:
        """Identifica o mime type da imagem."""
        ext = source.split(".")[-1].lower()
        if ext in ["jpg", "jpeg"]:
            return "image/jpeg"
        if ext == "png":
            return "image/png"
        if ext == "gif":
            return "image/gif"
        if ext == "webp":
            return "image/webp"
        return "image/jpeg"  # Default
