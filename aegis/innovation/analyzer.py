"""
aegis/innovation/analyzer.py

Agregador de métricas e identificador de gargalos e oportunidades.
Analisa Langfuse, Prometheus, friction-log e codebase para gerar o SystemHealthReport.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional

import structlog
from aegis.tools.innovation import (
    ReadMetricsTool, 
    ReadFrictionLogTool, 
    ReadProgressTool, 
    ReadMemoryStatsTool
)

logger = structlog.get_logger(__name__)

@dataclass
class ErrorPattern:
    """Representa um padrão de erro recorrente identificado no friction-log."""
    pattern: str
    occurrences: int
    severity: str
    impact: str

@dataclass
class SystemHealthReport:
    """Relatório consolidado de saúde e oportunidades do sistema."""
    bottlenecks: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    recurring_errors: List[ErrorPattern] = field(default_factory=list)
    development_velocity: str = "unknown"

class UsageAnalyzer:
    """Analisa dados de uso e saúde do sistema para disparar inovações."""

    def __init__(self):
        self.metrics_tool = ReadMetricsTool()
        self.friction_tool = ReadFrictionLogTool()
        self.progress_tool = ReadProgressTool()
        self.memory_tool = ReadMemoryStatsTool()

    async def run(self) -> SystemHealthReport:
        """
        Executa a análise completa e retorna um SystemHealthReport.
        """
        logger.info("usage_analyzer.started")
        
        # 1. Coleta dados em paralelo
        import asyncio
        metrics_task = self.metrics_tool.execute()
        friction_task = self.friction_tool.execute()
        progress_task = self.progress_tool.execute()
        memory_task = self.memory_tool.execute()
        
        results = await asyncio.gather(metrics_task, friction_task, progress_task, memory_task)
        metrics_res, friction_res, progress_res, memory_res = results
        
        report = SystemHealthReport()
        
        # 2. Processa Métricas (Langfuse/Prometheus)
        if metrics_res.success:
            report.metrics_summary["core"] = metrics_res.data
            latency_p99 = metrics_res.data.get("latency_p99", "0s")
            if float(latency_p99.replace("s", "")) > 3.0:
                report.bottlenecks.append(f"Latência P99 crítica detectada: {latency_p99}")
            
            error_rate = metrics_res.data.get("error_rate", "0%")
            if float(error_rate.replace("%", "")) > 2.0:
                report.bottlenecks.append(f"Taxa de erro elevada: {error_rate}")

        # 3. Processa Memória (ChromaDB/Neo4j)
        if memory_res.success:
            report.metrics_summary["memory"] = memory_res.data
            s_stats = memory_res.data.get("semantic", {})
            if s_stats.get("nodes", 0) > 0 and s_stats.get("relationships", 0) / s_stats.get("nodes", 1) < 0.5:
                report.opportunities.append("Baixa densidade de relações no grafo semântico. Sugerir exploração de conexões.")

        # 4. Processa Friction Log
        if friction_res.success:
            report.recurring_errors = await self.detect_recurring_errors(friction_res.data)
            for err in report.recurring_errors:
                if err.occurrences >= 2:
                    report.opportunities.append(f"Problema recorrente: {err.pattern} ({err.occurrences}x). Rationale: {err.impact}")

        # 5. Processa Progresso (Velocidade)
        if progress_res.success:
            report.development_velocity = self._calculate_velocity(progress_res.data)
            if "lenta" in report.development_velocity.lower():
                report.bottlenecks.append("Velocidade de desenvolvimento abaixo da média esperada.")

        # 6. Identifica Gaps e Pontos Fortes
        report.gaps = await self.find_capability_gaps()
        
        if not report.bottlenecks:
            report.strengths.append("Performance e estabilidade dentro dos SLAs.")
        
        if report.metrics_summary.get("memory", {}).get("episodic", {}).get("count", 0) > 100:
            report.strengths.append("Base de conhecimento episódica robusta (>100 episódios).")

        logger.info("usage_analyzer.finished", 
                    bottlenecks=len(report.bottlenecks), 
                    opportunities=len(report.opportunities))
        
        return report

    async def identify_weakest_component(self) -> str:
        """Retorna o nome do componente com pior desempenho ou mais erros."""
        report = await self.run()
        if report.bottlenecks:
            # Lógica simples: prioriza erros sobre latência
            for b in report.bottlenecks:
                if "erro" in b.lower():
                    match = re.search(r"componente (\w+)", b)
                    return match.group(1) if match else "core.engine"
            return "core.orchestrator"
        return "system.stable"

    async def find_capability_gaps(self) -> List[str]:
        """Analisa pedidos do usuário não atendidos (simulado)."""
        # Em produção, isso usaria o SemanticMemory para ver queries sem tools
        return ["Suporte a documentos multimodais (PDF + Imagem)", "Integração nativa com calendários externos"]

    async def detect_recurring_errors(self, friction_content: str) -> List[ErrorPattern]:
        """Agrupa entradas do friction-log por similaridade usando Regex."""
        patterns = []
        
        # Busca por títulos repetidos no formato ## [DATA] TAREFA-ID — Título
        titles = re.findall(r"## \[\d{4}-\d{2}-\d{2}\] .*? — (.*)", friction_content)
        unique_titles = {}
        for t in titles:
            unique_titles[t] = unique_titles.get(t, 0) + 1
            
        for title, count in unique_titles.items():
            if count >= 1: # No friction-log, até 1 entrada relevante pode ser considerada
                patterns.append(ErrorPattern(
                    pattern=title,
                    occurrences=count,
                    severity="MEDIUM" if count < 3 else "HIGH",
                    impact="Dívida técnica ou fricção de ambiente"
                ))
        
        # Busca específica por problemas de encoding conhecidos
        if "encoding" in friction_content.lower() or "mime type" in friction_content.lower():
            patterns.append(ErrorPattern(
                pattern="File System Encoding/MIME Issues",
                occurrences=len(re.findall(r"encoding|mime", friction_content.lower())),
                severity="HIGH",
                impact="Falha em ferramentas de leitura de arquivo no Windows"
            ))

        return patterns

    def _calculate_velocity(self, progress_content: str) -> str:
        """Calcula a média de tarefas concluídas por dia."""
        dates = re.findall(r"\[(\d{4}-\d{2}-\d{2})", progress_content)
        if not dates:
            return "Indeterminada"
            
        from datetime import datetime
        unique_dates = sorted(list(set(dates)))
        if len(unique_dates) < 2:
            return "Fase inicial"
            
        first = datetime.strptime(unique_dates[0], "%Y-%m-%d")
        last = datetime.strptime(unique_dates[-1], "%Y-%m-%d")
        days = (last - first).days or 1
        tasks_per_day = len(dates) / days
        
        if tasks_per_day > 3:
            return f"Alta ({tasks_per_day:.1f} tasks/dia)"
        elif tasks_per_day > 1:
            return f"Normal ({tasks_per_day:.1f} tasks/dia)"
        else:
            return f"Lenta ({tasks_per_day:.1f} tasks/dia)"
