"""
aegis/tools/memory.py

Ferramentas para interacao direta com as camadas de memoria do AEGIS.
"""
from __future__ import annotations

import structlog
from typing import Any, Dict, Optional

from aegis.tools.base import BaseTool, ToolResult
from aegis.memory.episodic import EpisodicMemory
from aegis.memory.semantic import SemanticMemory

logger = structlog.get_logger(__name__)

class MemorySearchTool(BaseTool):
    """Busca informacoes nas memorias episodica e semantica."""
    name: str = "memory_search"
    description: str = (
        "Busca fatos passados, conversas anteriores e preferencias do usuario. "
        "Use quando precisar lembrar de algo que o usuario disse anteriormente."
    )
    
    def __init__(self, episodic: Optional[EpisodicMemory] = None, semantic: Optional[SemanticMemory] = None):
        self.episodic = episodic or EpisodicMemory()
        self.semantic = semantic or SemanticMemory()

    async def execute(self, query: str, limit: int = 5) -> ToolResult:
        logger.info("tool.memory_search", query=query)
        try:
            # 1. Busca Episodica
            episodes = await self.episodic.search_similar(query, n=limit)
            
            # 2. Busca Semantica (Simplificada por query Cypher se query for complexa)
            # Por enquanto, busca apenas o perfil se query contiver "eu" ou "meu"
            semantic_data = []
            if any(word in query.lower() for word in ["eu", "meu", "minha", "preferencia"]):
                user_name = get_settings().AEGIS_USER_NAME
                semantic_data = await self.semantic.get_user_profile(user_name)

            return ToolResult(
                success=True, 
                data={
                    "episodes": episodes,
                    "semantic": semantic_data
                }, 
                error=None, 
                metadata={}
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e), metadata={})

class MemorySaveTool(BaseTool):
    """Salva informacoes na memoria episodica."""
    name: str = "memory_save"
    description: str = "Salva uma informacao importante ou resumo de conversa na memoria de longo prazo."
    
    def __init__(self, episodic: Optional[EpisodicMemory] = None):
        self.episodic = episodic or EpisodicMemory()

    async def execute(self, text: str, metadata: Optional[Dict] = None) -> ToolResult:
        logger.info("tool.memory_save", text_len=len(text))
        try:
            await self.episodic.save_episode(text, metadata or {})
            return ToolResult(success=True, data="Informacao salva com sucesso", error=None, metadata={})
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e), metadata={})

class MemoryUpdateTool(BaseTool):
    """Atualiza fatos ou preferencias na memoria semantica."""
    name: str = "memory_update"
    description: str = "Atualiza o perfil do usuario ou fatos conceituais no grafo de conhecimento."
    
    def __init__(self, semantic: Optional[SemanticMemory] = None):
        self.semantic = semantic or SemanticMemory()

    async def execute(self, fact_type: str, **kwargs) -> ToolResult:
        logger.info("tool.memory_update", fact_type=fact_type)
        try:
            if fact_type == "preference":
                await self.semantic.update_preference(
                    kwargs["user_name"], 
                    kwargs["entity"], 
                    kwargs.get("relation", "PREFERS")
                )
            elif fact_type == "fact":
                await self.semantic.save_fact(
                    kwargs["subject"], 
                    kwargs["relation"], 
                    kwargs["object"], 
                    kwargs.get("metadata")
                )
            return ToolResult(success=True, data="Memoria semantica atualizada", error=None, metadata={})
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e), metadata={})
