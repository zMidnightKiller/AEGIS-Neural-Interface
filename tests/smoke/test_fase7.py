"""
tests/smoke/test_fase7.py

Smoke test end-to-end para o Innovation Loop (Fase 7).
Valida o ciclo completo: Analise -> Geracao -> Validacao -> Execucao -> Impacto.
"""
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Mocking apscheduler if not present to avoid import errors
try:
    import apscheduler
except ImportError:
    mock_aps = MagicMock()
    sys.modules["apscheduler"] = mock_aps
    sys.modules["apscheduler.schedulers"] = MagicMock()
    sys.modules["apscheduler.schedulers.asyncio"] = MagicMock()

import pytest
import asyncio
import os
from aegis.innovation.loop import get_innovation_loop
from aegis.innovation.analyzer import SystemHealthReport
from aegis.innovation.task_generator import InnovationProposal

@pytest.mark.asyncio
async def test_innovation_loop_e2e_smoke(tmp_path):
    # Setup: Mock das dependencias para evitar chamadas reais de LLM ou metricas complexas
    mock_settings = MagicMock()
    mock_settings.CHROMA_PERSIST_DIR = str(tmp_path / "chroma")
    
    mock_report = SystemHealthReport(
        bottlenecks=["latency in research_agent"],
        gaps=["missing weather tool"],
        recurring_errors=[]
    )
    
    mock_proposal = InnovationProposal(
        title="Optimization Task",
        rationale="Improve performance",
        tasks=[],
        priority=MagicMock(),
        risk_level=1
    )

    with patch("aegis.innovation.loop.get_settings", return_value=mock_settings), \
         patch("aegis.innovation.analyzer.UsageAnalyzer.run", new_callable=AsyncMock) as mock_analyze, \
         patch("aegis.innovation.task_generator.TaskGenerator.generate", new_callable=AsyncMock) as mock_generate, \
         patch("aegis.innovation.validator.TaskValidator.validate", new_callable=AsyncMock) as mock_validate, \
         patch("aegis.innovation.loop.InnovationLoop.evaluate_impact", new_callable=AsyncMock) as mock_eval:
        
        mock_analyze.return_value = mock_report
        mock_generate.return_value = [mock_proposal]
        mock_validate.return_value = 1
        mock_eval.return_value = {"latency_delta": -0.2}

        loop = get_innovation_loop()
        # Reset history for test
        loop.history = []
        
        # 1. Trigger manual
        result = await loop.trigger(reason="smoke_test")
        
        # 2. Validacoes do ciclo
        assert result.status == "success"
        assert result.proposals_generated == 1
        assert result.proposals_approved == 1
        
        # 3. Validacao de persistencia
        assert os.path.exists(loop.history_file)
        
        # 4. Avaliacao de impacto (simulada)
        impact = await loop.evaluate_impact("task_test_123")
        assert impact["latency_delta"] == -0.2
        
        print("\n[SMOKE TEST] Fase 7: Innovation Loop funcionando corretamente!")

if __name__ == "__main__":
    asyncio.run(test_innovation_loop_e2e_smoke())
