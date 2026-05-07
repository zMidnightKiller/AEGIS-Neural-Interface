"""
tests/innovation/test_analyzer.py

Testes unitários para o UsageAnalyzer.
"""
import pytest
from unittest.mock import AsyncMock, patch

from aegis.innovation.analyzer import UsageAnalyzer, SystemHealthReport
from aegis.tools.base import ToolResult

@pytest.fixture
def analyzer():
    return UsageAnalyzer()

class TestUsageAnalyzer:
    @pytest.mark.asyncio
    async def test_run_produces_report(self, analyzer):
        """Garante que o run() retorna um SystemHealthReport válido com todas as fontes."""
        with patch("aegis.tools.innovation.ReadMetricsTool.execute", new_callable=AsyncMock) as mock_metrics, \
             patch("aegis.tools.innovation.ReadFrictionLogTool.execute", new_callable=AsyncMock) as mock_friction, \
             patch("aegis.tools.innovation.ReadProgressTool.execute", new_callable=AsyncMock) as mock_progress, \
             patch("aegis.tools.innovation.ReadMemoryStatsTool.execute", new_callable=AsyncMock) as mock_memory:
            
            mock_metrics.return_value = ToolResult(
                success=True, 
                data={"latency_p99": "4.5s", "error_rate": "3.5%"},
                metadata={}
            )
            mock_friction.return_value = ToolResult(
                success=True,
                data="## [2026-05-06] TAREFA 7.1 — Timeout de API\n## [2026-05-06] TAREFA 7.2 — Timeout de API",
                metadata={}
            )
            mock_progress.return_value = ToolResult(
                success=True,
                data="[2026-05-01] Task 1\n[2026-05-06] Task 2",
                metadata={}
            )
            mock_memory.return_value = ToolResult(
                success=True,
                data={
                    "episodic": {"count": 120},
                    "semantic": {"nodes": 10, "relationships": 2}
                },
                metadata={}
            )
            
            report = await analyzer.run()
            
            assert isinstance(report, SystemHealthReport)
            assert len(report.bottlenecks) >= 2 # Latência, Taxa de erro, Velocidade (lenta)
            assert any("Latência" in b for b in report.bottlenecks)
            assert any("Taxa de erro" in b for b in report.bottlenecks)
            assert any("Velocidade" in b for b in report.bottlenecks)
            assert report.development_velocity.startswith("Lenta")
            assert any("densidade" in o for o in report.opportunities)
            assert any("episódica robusta" in s for s in report.strengths)

    @pytest.mark.asyncio
    async def test_identify_weakest_component(self, analyzer):
        """Garante que identifica o componente problemático prioritário."""
        with patch("aegis.innovation.analyzer.UsageAnalyzer.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = SystemHealthReport(
                bottlenecks=["Taxa de erro elevada no componente research_agent: 5%"]
            )
            
            component = await analyzer.identify_weakest_component()
            assert component == "research_agent"

    @pytest.mark.asyncio
    async def test_detect_recurring_errors_logic(self, analyzer):
        """Testa a lógica de detecção baseada em títulos e padrões de encoding."""
        content = """
        ## [2026-05-06] T-1 — Problema de Conexão
        ## [2026-05-06] T-2 — Problema de Conexão
        Erro de encoding detectado ao ler arquivo.
        """
        errors = await analyzer.detect_recurring_errors(content)
        
        patterns = [e.pattern for e in errors]
        assert "Problema de Conexão" in patterns
        assert "File System Encoding/MIME Issues" in patterns
        
        # Verifica contagem
        conn_err = next(e for e in errors if e.pattern == "Problema de Conexão")
        assert conn_err.occurrences == 2

    def test_calculate_velocity(self, analyzer):
        """Testa o cálculo de velocidade de desenvolvimento."""
        content = "[2026-05-01] T1\n[2026-05-01] T2\n[2026-05-02] T3"
        velocity = analyzer._calculate_velocity(content)
        assert "Alta" in velocity or "Normal" in velocity
        
        content_slow = "[2026-05-01] T1\n[2026-05-10] T2"
        velocity_slow = analyzer._calculate_velocity(content_slow)
        assert "Lenta" in velocity_slow
