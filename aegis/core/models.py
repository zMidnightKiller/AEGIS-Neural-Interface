"""
aegis/core/models.py

Modelos de dados fundamentais do sistema AEGIS.
Contém definições de contratos imutáveis para entrada e saída.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class OperatingMode(str, Enum):
    """Modos de operação do AEGIS que afetam verbosidade e comportamento."""
    STANDARD = "STANDARD"
    BRIEFING = "BRIEFING"
    ANALYSIS = "ANALYSIS"
    SILENT = "SILENT"
    VERBOSE = "VERBOSE"


@dataclass
class UserInput:
    """Dados de entrada do usuário."""
    text: str
    session_id: str
    mode: OperatingMode = OperatingMode.STANDARD
    attachments: list[str] = field(default_factory=list)


@dataclass
class AgentResponse:
    """Resposta estruturada do AEGIS."""
    text: str
    agent_used: str
    tools_used: list[str]
    memory_injected: bool
    latency_ms: int


@dataclass
class ToolResult:
    """Resultado da execução de uma ferramenta."""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentResult:
    """Resultado da execução de um agente."""
    success: bool
    output: str
    steps_taken: int
    tools_used: list[str]
    error: Optional[str] = None


@dataclass
class Message:
    """Uma única mensagem no histórico de conversação."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: float = field(default_factory=lambda: 0.0)  # Simplificado para o MVP
    metadata: dict = field(default_factory=dict)
