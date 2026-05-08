"""
aegis/core/resource_guard.py

Monitor de recursos (VRAM, CPU, RAM) para o AEGIS.
Versão inicial (Stub) para suporte às tarefas da Fase 0.
A implementação completa será realizada na Tarefa 1.2.
"""
import asyncio
from dataclasses import dataclass
from typing import List, Optional

import structlog

logger = structlog.get_logger(__name__)

class ResourceUnsafeError(Exception):
    """Lançada quando uma operação é considerada insegura pelo ResourceGuard."""
    pass

@dataclass
class ResourceStatus:
    vram_used_gb: float
    vram_total_gb: float
    vram_pct: float
    gpu_temp_c: float
    cpu_pct: float
    ram_used_gb: float
    ram_total_gb: float
    level: str  # SAFE | WARN | PAUSE | STOP | EMERGENCY
    paused_ops: List[str]

class ResourceGuard:
    _instance: Optional['ResourceGuard'] = None

    @classmethod
    def get_instance(cls) -> 'ResourceGuard':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.level = "SAFE"

    async def assert_safe(self, op: str) -> None:
        """
        Verifica se a operação é segura. 
        Nesta versão stub, sempre retorna SAFE a menos que configurado o contrário.
        """
        logger.debug("resource_guard.check", op=op, level=self.level)
        if self.level == "STOP":
            raise ResourceUnsafeError(f"Operação {op} recusada: Nível STOP atingido.")

    async def wait_for_safe(self, op: str, timeout_s: int = 300) -> None:
        """Aguarda até que o sistema esteja em nível SAFE ou WARN."""
        logger.debug("resource_guard.wait", op=op)
        # Stub: retorna imediatamente
        return

    def is_safe_for(self, op: str) -> bool:
        """Check síncrono sem bloqueio."""
        return self.level != "STOP"

    async def check(self) -> ResourceStatus:
        """Snapshot simulado dos recursos."""
        return ResourceStatus(
            vram_used_gb=4.5,
            vram_total_gb=12.0,
            vram_pct=37.5,
            gpu_temp_c=55.0,
            cpu_pct=15.0,
            ram_used_gb=8.0,
            ram_total_gb=32.0,
            level=self.level,
            paused_ops=[]
        )
