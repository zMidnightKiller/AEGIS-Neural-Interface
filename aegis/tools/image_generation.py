"""
aegis/tools/image_generation.py

Ferramenta para geração de imagens via IA.
Utiliza a API OpenAI (DALL-E 3) como motor principal.
"""
from __future__ import annotations

from typing import Any

import httpx
import structlog
from openai import AsyncOpenAI

from aegis.core.config import get_settings
from aegis.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)


class ImageGenerationTool(BaseTool):
    """Gera imagens a partir de descrições textuais."""

    name: str = "image_generation"
    description: str = (
        "Gera uma imagem baseada em uma descrição detalhada (prompt). "
        "Retorna a URL da imagem gerada."
    )

    def __init__(self):
        self.settings = get_settings()
        api_key = self.settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=api_key.get_secret_value()) if api_key else None

    async def execute(self, prompt: str, size: str = "1024x1024", quality: str = "standard") -> ToolResult:
        """
        Executa a geração da imagem.

        Args:
            prompt: Descrição da imagem a ser gerada.
            size: Dimensões da imagem (ex: 1024x1024).
            quality: Qualidade da imagem (standard ou hd).

        Returns:
            ToolResult com a URL da imagem ou erro.
        """
        logger.info("image_generation.executing", prompt=prompt, size=size)

        if not self.client:
            return ToolResult(
                success=False, 
                error="OPENAI_API_KEY não configurada. A geração de imagem requer uma chave da OpenAI."
            )

        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )

            image_url = response.data[0].url
            return ToolResult(
                success=True, 
                data=image_url,
                metadata={"revised_prompt": response.data[0].revised_prompt}
            )

        except Exception as e:
            logger.error("image_generation.error", error=str(e))
            return ToolResult(success=False, error=f"Erro ao gerar imagem: {str(e)}")
