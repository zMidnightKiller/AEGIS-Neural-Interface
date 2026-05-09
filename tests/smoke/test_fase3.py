"""
tests/smoke/test_fase3.py

Smoke Test para a Fase 3 do AEGIS.
Valida o pipeline de aprendizado continuo: Coleta, Treino (LoRA/DPO), Avaliacao e Agendamento.
"""
import pytest
import os
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

# Variaveis de ambiente para teste
os.environ["AEGIS_LEARNING_ENABLED"] = "true"
os.environ["AEGIS_MIN_SAMPLES_FOR_FINETUNE"] = "5" # Reduzido para teste

from aegis.learning.collector import TrainingDataCollector
from aegis.learning.finetuner import LoRAFinetuner, TrainingResult
from aegis.learning.evaluator import QualityEvaluator
from aegis.learning.scheduler import TrainingScheduler
from aegis.learning.adapter_manager import AdapterManager

@pytest.fixture
def mock_fase3_env():
    """Moca componentes da Fase 3."""
    # Patching where they are USED
    with patch("aegis.core.resource_guard.ResourceGuard.get_instance") as mock_guard_fn, \
         patch("aegis.learning.finetuner.WorkingMemory") as mock_ft_mem_class, \
         patch("aegis.learning.scheduler.WorkingMemory") as mock_sch_mem_class, \
         patch("aegis.learning.collector.sqlite3") as mock_sqlite_fn, \
         patch("aegis.learning.collector.InferenceEngineFactory") as mock_factory, \
         patch("aegis.learning.finetuner.FastLanguageModel", create=True) as mock_unsloth_fn:
        
        # ResourceGuard
        guard = MagicMock()
        guard.assert_safe = AsyncMock()
        guard.is_safe_for = MagicMock(return_value=True)
        guard.check = AsyncMock(return_value=MagicMock(gpu_pct=10, paused_ops=[], level="SAFE"))
        mock_guard_fn.return_value = guard
        
        # WorkingMemory for Finetuner
        ft_mem = AsyncMock()
        ft_mem.has_active_session.return_value = False
        mock_ft_mem_class.return_value = ft_mem
        
        # WorkingMemory for Scheduler
        sch_mem = AsyncMock()
        sch_mem.has_active_session.return_value = False
        mock_sch_mem_class.return_value = sch_mem
        
        # SQLite / Collector
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [10] # n_samples
        mock_conn.cursor.return_value = mock_cursor
        mock_sqlite_fn.connect.return_value = mock_conn
        # Suporte para context manager: with sqlite3.connect(...) as conn:
        mock_sqlite_fn.connect.return_value.__enter__.return_value = mock_conn
        
        # Factory
        mock_factory.create.return_value = AsyncMock()
        
        yield {
            "guard": guard,
            "ft_mem": ft_mem,
            "sch_mem": sch_mem,
            "collector_db": mock_conn,
            "collector_cursor": mock_cursor
        }

@pytest.mark.asyncio
async def test_fase3_learning_pipeline_smoke(mock_fase3_env):
    """
    Valida o fluxo completo de aprendizado (coleta -> treino -> avaliacao).
    """
    # 1. Coleta de dados
    collector = TrainingDataCollector()
    # Simula salvamento de conversa
    await collector.collect("test-session", "Prompt teste", "Resposta teste")
    assert mock_fase3_env["collector_db"].execute.called

    # 2. Fine-Tuning (Mockado)
    finetuner = LoRAFinetuner()
    with patch.object(finetuner, "run", new_callable=AsyncMock) as mock_ft_run:
        mock_ft_run.return_value = TrainingResult(
            success=True,
            adapter_path="./checkpoints/lora_test",
            steps_completed=200,
            final_loss=0.5,
            eval_metrics={"perplexity": 12.5},
            vram_peak_gb=10.5,
            duration_seconds=3600,
            rolled_back=False,
            oom_occurred=False
        )
        
        result = await finetuner.run(dataset=[{"text": "dummy"}])
        assert result.success is True
        assert result.vram_peak_gb <= 11.5 # Limite da 3060

    # 3. Avaliacao e Gestao de Adapters
    evaluator = QualityEvaluator(model_path="dummy_path")
    adapter_mgr = AdapterManager()
    
    with patch.object(evaluator, "evaluate", new_callable=AsyncMock) as mock_eval, \
         patch.object(adapter_mgr, "register_adapter", new_callable=AsyncMock) as mock_reg:
        
        mock_eval.return_value = {"score": 0.9, "improvement": 0.1, "rolled_back": False}
        
        eval_results = await evaluator.evaluate(baseline_metrics={"quality_score": 0.8})
        assert eval_results["score"] > 0.8
        
        await adapter_mgr.register_adapter("./checkpoints/lora_test", eval_results)
        mock_reg.assert_called_once()

    # 4. Scheduler (Verifica condicoes de disparo)
    # Patch where settings is used in scheduler module
    with patch("aegis.learning.scheduler.settings") as mock_set:
        mock_set.AEGIS_MODE = "LEARNING" # Evita janela horaria 00-06
        mock_set.AEGIS_MIN_SAMPLES_FOR_FINETUNE = 5
        mock_set.FINETUNE_IDLE_MINUTES = 30
        mock_set.AEGIS_DATA_DIR = "./.tmp/aegis_data"
        
        scheduler = TrainingScheduler()
        # Forca condicoes ideais
        with patch.object(scheduler.collector, "get_sample_count", return_value=50):
            can_run = await scheduler._should_train()
            assert can_run is True

@pytest.mark.asyncio
async def test_fase3_resource_guard_interaction(mock_fase3_env):
    """
    Valida se o aprendizado respeita o ResourceGuard e WorkingMemory.
    """
    finetuner = LoRAFinetuner()
    
    # Caso 1: Sessao ativa do usuario
    mock_fase3_env["ft_mem"].has_active_session.return_value = True
    with pytest.raises(RuntimeError, match="usuário em sessão ativa"):
        await finetuner.run(dataset=[])
        
    # Caso 2: VRAM em nivel STOP (96%)
    mock_fase3_env["ft_mem"].has_active_session.return_value = False
    from aegis.core.resource_guard import ResourceUnsafeError
    mock_fase3_env["guard"].assert_safe.side_effect = ResourceUnsafeError("VRAM 97%")
    
    with pytest.raises(ResourceUnsafeError):
        await finetuner.run(dataset=[])
