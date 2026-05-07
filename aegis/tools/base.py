"""
aegis/tools/base.py

Classes base para ferramentas do sistema AEGIS.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Representa o resultado da execucao de uma ferramenta."""

    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """Classe base abstrata para todas as ferramentas."""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Executa a lógica da ferramenta.

        Args:
            **kwargs: Argumentos nomeados para a execucao.

        Returns:
            ToolResult contendo o resultado da operacao.
        """
        ...
