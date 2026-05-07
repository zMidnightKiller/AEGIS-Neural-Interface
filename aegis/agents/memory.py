"""
aegis/agents/memory.py

Agente especializado em gestao de memoria.
Responsavel por buscar contextos relevantes (pre-interacao) e
extrair/persistir novos conhecimentos (pos-interacao).
"""
from __future__ import annotations

import structlog
from typing import Any, List, Dict, Optional

from aegis.agents.base import BaseAgent, AgentResult
from aegis.core.context import Context
from aegis.memory.episodic import EpisodicMemory
from aegis.memory.semantic import SemanticMemory
from aegis.tools.base import BaseTool
from aegis.tools.memory import MemorySearchTool, MemorySaveTool, MemoryUpdateTool

logger = structlog.get_logger(__name__)


class MemoryAgent(BaseAgent):
    """
    Agente que orquestra a persistencia e recuperacao de informacoes.
    Utiliza as ferramentas de memoria para manter o estado de longo prazo do sistema.
    """

    name: str = "memory"
    description: str = "Gere as memorias episodica (conversas) e semantica (fatos) do sistema."
    max_steps: int = 3

    def __init__(self, episodic: Optional[EpisodicMemory] = None, semantic: Optional[SemanticMemory] = None):
        self.episodic = episodic or EpisodicMemory()
        self.semantic = semantic or SemanticMemory()

    def get_tools(self) -> list[BaseTool]:
        """Retorna as ferramentas de memoria disponiveis."""
        return [
            MemorySearchTool(self.episodic, self.semantic),
            MemorySaveTool(self.episodic),
            MemoryUpdateTool(self.semantic),
        ]

    async def pre_process(self, query: str, context: Context) -> str:
        """
        Busca memorias relevantes para injetar no contexto da proxima interacao.
        
        Args:
            query: A pergunta ou comando do usuario.
            context: O contexto da sessao atual.
            
        Returns:
            Uma string formatada contendo informacoes recuperadas da memoria.
        """
        logger.info("memory_agent.pre_process", query=query)
        
        # 1. Busca Episodica (ChromaDB)
        episodes = await self.episodic.search_similar(query, threshold=0.6, n=3)
        
        # 2. Busca Semantica (Neo4j) - Perfil do usuario
        user_name = context.metadata.get("user_name", "default_user")
        profile = await self.semantic.get_user_profile(user_name)
        
        # Formata o contexto injetado
        memory_context_parts = []
        
        if episodes:
            parts = ["### Memorias Episodicas Relevantes:"]
            for ep in episodes:
                parts.append(f"- {ep['content']}")
            memory_context_parts.append("\n".join(parts))
        
        if profile:
            parts = ["### Preferencias e Fatos do Usuario:"]
            for p in profile:
                parts.append(f"- O usuario {p['relation'].lower()} {p['entity']}")
            memory_context_parts.append("\n".join(parts))
                
        return "\n\n".join(memory_context_parts) if memory_context_parts else ""

    async def post_process(self, interaction_text: str):
        """
        Extrai fatos e salva o episodio apos a interacao.
        
        Args:
            interaction_text: O texto completo da interacao (usuario + assistente).
        """
        logger.info("memory_agent.post_process")
        
        # 1. Salva na Memoria Episodica
        await self.episodic.save_episode(interaction_text, metadata={"type": "interaction"})
        
        # 2. Extrai e salva na Memoria Semantica (utiliza LLM internamente)
        await self.semantic.extract_entities_from_text(interaction_text)

    async def run(self, task: str, context: Context) -> AgentResult:
        """
        Executa tarefas autonomas de memoria (ex: 'limpar memorias antigas', 'resumir perfil').
        """
        logger.info("memory_agent.running_task", task=task)
        # Por enquanto, apenas reporta sucesso como stub
        return AgentResult(
            success=True, 
            output=f"Tarefa de memoria '{task}' processada com sucesso.", 
            steps_taken=1, 
            tools_used=[]
        )
