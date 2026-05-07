"""
aegis/agents/base.py

Classe base abstrata para agentes especializados no sistema AEGIS.
Define o contrato e o loop de execucao principal.
"""
from __future__ import annotations

import structlog
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from aegis.tools.base import BaseTool
from aegis.core.context import Context

logger = structlog.get_logger(__name__)


@dataclass
class AgentResult:
    """Resultado da execucao de um agente."""

    success: bool
    output: str
    steps_taken: int
    tools_used: list[str]
    error: str | None = None


class BaseAgent(ABC):
    """
    Classe base para todos os agentes especializados.
    Define a interface obrigatoria e o limite de passos.
    """

    name: str
    description: str
    max_steps: int = 5

    @abstractmethod
    def get_tools(self) -> list[BaseTool]:
        """
        Retorna a lista de ferramentas que o agente pode utilizar.

        Returns:
            Lista de instancias de BaseTool.
        """
        ...

    @abstractmethod
    async def run(self, task: str, context: Context) -> AgentResult:
        """
        Executa a tarefa designada ao agente.

        Args:
            task: Descricao da tarefa em linguagem natural.
            context: Contexto da sessao atual.

        Returns:
            AgentResult contendo o resultado da execucao.
        """
        ...
