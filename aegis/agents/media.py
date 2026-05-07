"""
aegis/agents/media.py

Agente especializado em mídia (visão e geração de imagens).
Utiliza VisionTool e ImageGenerationTool para processar e criar conteúdo visual.
"""
from __future__ import annotations

import structlog
from typing import List, Optional

from aegis.agents.base import BaseAgent, AgentResult
from aegis.core.context import Context
from aegis.tools.base import BaseTool
from aegis.tools.vision import VisionTool
from aegis.tools.image_generation import ImageGenerationTool

logger = structlog.get_logger(__name__)


class MediaAgent(BaseAgent):
    """
    Agente que processa e gera conteúdo visual.
    Consegue descrever imagens existentes ou criar novas a partir de texto.
    """

    name: str = "media"
    description: str = (
        "Especialista em visão computacional e geração de imagens. "
        "Use para analisar fotos, descrever imagens ou criar novas ilustrações e artes."
    )
    max_steps: int = 3

    def get_tools(self) -> list[BaseTool]:
        """Retorna as ferramentas de visão e geração."""
        return [VisionTool(), ImageGenerationTool()]

    async def run(self, task: str, context: Context) -> AgentResult:
        """
        Executa a tarefa de mídia.
        Decide entre visão ou geração com base na tarefa.
        """
        logger.info("media_agent.started", task=task)
        
        tools_used = []
        
        # Lógica simples de decisão: se tiver 'gere', 'crie', 'faça uma imagem' -> Geração
        # Se tiver 'analise', 'descreva', 'o que tem na imagem' -> Visão
        
        task_lower = task.lower()
        is_generation = any(kw in task_lower for kw in ["gere", "gerar", "crie", "criar", "desenhe", "imagem de", "ilustre"])
        is_vision = any(kw in task_lower for kw in ["analise", "descreva", "o que", "identifique", "veja", "leia"])
        
        # Prioridade para visão se houver anexo/url detectado no contexto ou task
        has_image_ref = ".jpg" in task_lower or ".png" in task_lower or "http" in task_lower or "c:/" in task_lower or "C:/" in task_lower
        
        try:
            if is_vision or (has_image_ref and not is_generation):
                # Executa Visão
                vision_tool = VisionTool()
                logger.info("media_agent.routing_to_vision")
                
                # Tenta extrair a fonte da imagem
                # Simplificado: se houver URL ou caminho na task, usa. 
                # Em um sistema real, pegaríamos dos attachments do Context.
                image_source = self._extract_source(task)
                if not image_source:
                    # Se não achou na task, tenta no último anexo da sessão
                    if context.attachments:
                        image_source = context.attachments[-1]
                
                if not image_source:
                    return AgentResult(
                        success=False,
                        output="Não consegui identificar uma fonte de imagem para analisar. Forneça uma URL ou caminho de arquivo.",
                        steps_taken=0,
                        tools_used=[]
                    )
                
                result = await vision_tool.execute(image_source=image_source, prompt=task)
                tools_used.append(vision_tool.name)
                
                if result.success:
                    return AgentResult(
                        success=True,
                        output=f"Análise da Imagem:\n\n{result.data}",
                        steps_taken=1,
                        tools_used=tools_used
                    )
                else:
                    return AgentResult(
                        success=False,
                        output=f"Falha na análise: {result.error}",
                        steps_taken=1,
                        tools_used=tools_used,
                        error=result.error
                    )

            else:
                # Executa Geração
                gen_tool = ImageGenerationTool()
                logger.info("media_agent.routing_to_generation")
                
                result = await gen_tool.execute(prompt=task)
                tools_used.append(gen_tool.name)
                
                if result.success:
                    return AgentResult(
                        success=True,
                        output=f"Imagem gerada com sucesso! Você pode visualizá-la aqui: {result.data}",
                        steps_taken=1,
                        tools_used=tools_used
                    )
                else:
                    return AgentResult(
                        success=False,
                        output=f"Falha na geração: {result.error}",
                        steps_taken=1,
                        tools_used=tools_used,
                        error=result.error
                    )

        except Exception as e:
            logger.error("media_agent.error", error=str(e))
            return AgentResult(
                success=False,
                output="Ocorreu um erro inesperado no processamento de mídia.",
                steps_taken=len(tools_used),
                tools_used=tools_used,
                error=str(e)
            )

    def _extract_source(self, task: str) -> Optional[str]:
        """Tenta extrair uma URL ou caminho de arquivo da string da tarefa."""
        import re
        # Regex para URL
        url_match = re.search(r'https?://[^\s]+', task)
        if url_match:
            return url_match.group(0)
        
        # Regex para caminho de arquivo comum (Windows/Linux)
        path_match = re.search(r'[A-Za-z]:\\[^\s]+|\/[^\s]+\.(jpg|png|jpeg|webp)', task)
        if path_match:
            return path_match.group(0)
            
        return None
