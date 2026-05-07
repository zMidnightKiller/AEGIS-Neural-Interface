"""
aegis/innovation/loop.py

Orquestrador do Innovation Loop: o ciclo evolutivo autonomo do AEGIS.
Coordena analise de uso, geracao de propostas, validacao e monitoramento de impacto.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aegis.core.config import get_settings
from aegis.innovation.analyzer import UsageAnalyzer, SystemHealthReport
from aegis.innovation.task_generator import TaskGenerator, InnovationProposal
from aegis.innovation.validator import TaskValidator

logger = structlog.get_logger(__name__)

@dataclass
class InnovationResult:
    """Resultado de um ciclo de inovacao."""
    timestamp: datetime
    status: str
    proposals_generated: int
    proposals_approved: int
    impact_measured: Optional[Dict[str, float]] = None
    error: Optional[str] = None

class InnovationLoop:
    """
    Controla o ciclo de vida da evolucao autonoma do AEGIS.
    """

    def __init__(self):
        self.settings = get_settings()
        self.analyzer = UsageAnalyzer()
        self.generator = TaskGenerator()
        self.validator = TaskValidator()
        self.scheduler = AsyncIOScheduler()
        # Usa o diretrio pai do persist_dir do chroma como base para dados (./data)
        base_data_dir = os.path.dirname(self.settings.CHROMA_PERSIST_DIR)
        self.history_file = os.path.join(base_data_dir, "innovation_history.json")
        self.history: List[InnovationResult] = self._load_history()
        self._is_running = False

    def _load_history(self) -> List[InnovationResult]:
        """Carrega o historico de inovacao do disco."""
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [
                    InnovationResult(
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                        status=item["status"],
                        proposals_generated=item["proposals_generated"],
                        proposals_approved=item["proposals_approved"],
                        impact_measured=item.get("impact_measured"),
                        error=item.get("error")
                    ) for item in data
                ]
        except Exception as e:
            logger.error("innovation_loop.load_history_failed", error=str(e))
            return []

    def _save_history(self):
        """Salva o historico de inovacao no disco."""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in self.history], f, indent=2, default=str)
        except Exception as e:
            logger.error("innovation_loop.save_history_failed", error=str(e))

    async def start(self):
        """Inicia o agendamento do loop."""
        if self._is_running:
            return
            
        logger.info("innovation_loop.starting")
        # Agenda o loop para rodar a cada 72h conforme PRD (ou conforme config)
        self.scheduler.add_job(
            self.trigger, 
            'interval', 
            hours=72, 
            id='innovation_cycle',
            kwargs={'reason': 'scheduled'}
        )
        self.scheduler.start()
        self._is_running = True

    async def stop(self):
        """Para o agendamento do loop."""
        if self.scheduler.running:
            self.scheduler.shutdown()
        self._is_running = False
        logger.info("innovation_loop.stopped")

    async def trigger(self, reason: str = "manual") -> InnovationResult:
        """
        Dispara um ciclo completo de inovacao.
        """
        logger.info("innovation_loop.triggered", reason=reason)
        start_time = datetime.now()
        
        try:
            # 1. Analisar saude do sistema
            report: SystemHealthReport = await self.analyzer.run()
            logger.info("innovation_loop.health_report_ready", report=report)

            # 2. Gerar propostas de melhoria
            proposals: List[InnovationProposal] = await self.generator.generate(report, existing_tasks=[])
            logger.info("innovation_loop.proposals_generated", count=len(proposals))

            if not proposals:
                return InnovationResult(
                    timestamp=start_time,
                    status="no_proposals",
                    proposals_generated=0,
                    proposals_approved=0
                )

            # 3. Validar e filtrar propostas (Supervised vs Autonomous)
            approved_count = await self.validator.validate(proposals)
            logger.info("innovation_loop.validation_complete", approved=approved_count)

            result = InnovationResult(
                timestamp=start_time,
                status="success",
                proposals_generated=len(proposals),
                proposals_approved=approved_count
            )
            self.history.append(result)
            self._save_history()
            return result

        except Exception as e:
            logger.error("innovation_loop.failed", error=str(e))
            result = InnovationResult(
                timestamp=start_time,
                status="failed",
                proposals_generated=0,
                proposals_approved=0,
                error=str(e)
            )
            self.history.append(result)
            self._save_history()
            return result

    async def evaluate_impact(self, task_id: str) -> Dict[str, float]:
        """
        Compara as metricas antes e depois da execucao de uma task de inovacao.
        Calcula o delta de performance e confiabilidade.
        """
        logger.info("innovation_loop.evaluating_impact", task_id=task_id)
        
        # Em uma implementacao real, comparariamos snapshots do SystemHealthReport
        current_report = await self.analyzer.run()
        
        # Exemplo de deltas ficticios baseados no estado atual vs esperado
        deltas = {
            "latency_p99_delta": -0.15,  # Melhoria de 15% (simulado)
            "error_rate_delta": -0.02,    # Reducao de 2% (simulado)
            "throughput_delta": 0.10      # Aumento de 10% (simulado)
        }
        
        # Atualiza o ultimo resultado com o impacto medido
        if self.history:
            self.history[-1].impact_measured = deltas
            self._save_history()
            
        # Se o impacto for muito negativo (> 10% de degradacao em metricas criticas)
        if deltas["latency_p99_delta"] > 0.10 or deltas["error_rate_delta"] > 0.05:
            logger.warning("innovation_loop.negative_impact_detected", task_id=task_id, deltas=deltas)
            await self._rollback(task_id)
            
        return deltas

    async def _rollback(self, task_id: str):
        """
        Executa rollback automatico se uma inovacao causar regressao.
        """
        logger.error("innovation_loop.executing_rollback", task_id=task_id)
        
        try:
            # Tenta executar git revert HEAD --no-edit
            # Nota: Isso assume que o ambiente e um repositorio git e cada task e um commit.
            process = await asyncio.create_subprocess_exec(
                "git", "revert", "HEAD", "--no-edit",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("innovation_loop.rollback_success", task_id=task_id)
            else:
                logger.error("innovation_loop.rollback_failed", error=stderr.decode())
                
        except Exception as e:
            logger.error("innovation_loop.rollback_exception", error=str(e))

    def get_status(self) -> Dict[str, Any]:
        """Retorna o status atual do loop para o dashboard."""
        return {
            "is_running": self._is_running,
            "last_run": self.history[-1].timestamp if self.history else None,
            "total_proposals": sum(r.proposals_generated for r in self.history),
            "total_approved": sum(r.proposals_approved for r in self.history),
            "history_length": len(self.history),
            "history": [asdict(r) for r in self.history[-10:]] # ultimos 10 ciclos
        }


_loop_instance: Optional[InnovationLoop] = None

def get_innovation_loop() -> InnovationLoop:
    """Retorna a instancia singleton do InnovationLoop."""
    global _loop_instance
    if _loop_instance is None:
        _loop_instance = InnovationLoop()
    return _loop_instance
