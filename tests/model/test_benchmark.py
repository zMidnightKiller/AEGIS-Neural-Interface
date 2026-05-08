import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from aegis.model.benchmark import ModelBenchmark, BenchmarkResult

@pytest.fixture
def mock_llama():
    """Mock do llama_cpp.Llama para não carregar modelos reais."""
    with patch("aegis.model.benchmark.Llama") as mock:
        model_instance = MagicMock()
        # Simula o retorno de um gerador (stream=True)
        model_instance.return_value = [
            {"choices": [{"text": "T"}]},
            {"choices": [{"text": "o"}]},
            {"choices": [{"text": "k"}]},
            {"choices": [{"text": "e"}]},
            {"choices": [{"text": "n"}]}
        ]
        mock.return_value = model_instance
        yield mock

@pytest.fixture
def mock_torch():
    """Mock do torch para simular uso de VRAM."""
    with patch("aegis.model.benchmark.torch") as mock:
        mock.cuda.is_available.return_value = True
        # Simula 5.5 GB de VRAM pico
        mock.cuda.max_memory_allocated.return_value = 5.5 * (1024**3)
        yield mock

@pytest.mark.asyncio
async def test_benchmark_measures_performance_correctly(mock_llama, mock_torch, tmp_path):
    # Cria um arquivo de modelo "fake" para o Path.exists() passar
    fake_model = tmp_path / "test_model.gguf"
    fake_model.write_text("placeholder")
    
    benchmark = ModelBenchmark(str(fake_model))
    result = await benchmark.run_inference_test(prompt="Diga algo.")
    
    assert isinstance(result, BenchmarkResult)
    assert result.model_name == "test_model.gguf"
    assert result.total_tokens == 5
    assert result.vram_peak_gb == 5.5
    assert result.tokens_per_second > 0
    mock_llama.assert_called_once()

def test_benchmark_saves_report_file(tmp_path, monkeypatch):
    # Alteramos o diretório de trabalho para o tmp_path para o teste
    monkeypatch.chdir(tmp_path)
    
    result = BenchmarkResult(
        model_name="test.gguf",
        timestamp="2026-05-08T18:00:00",
        tokens_per_second=15.5,
        time_to_first_token_ms=120.0,
        total_tokens=50,
        vram_peak_gb=4.2,
        config={"test": True}
    )
    
    benchmark = ModelBenchmark("test.gguf")
    benchmark.save_report(result)
    
    report_dir = tmp_path / "benchmarks"
    assert report_dir.exists()
    reports = list(report_dir.glob("baseline_*.json"))
    assert len(reports) == 1
    
    import json
    with open(reports[0], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["model_name"] == "test.gguf"
        assert data["tokens_per_second"] == 15.5

@pytest.mark.asyncio
async def test_benchmark_refuses_on_resource_guard_stop(mock_llama, tmp_path):
    from aegis.core.resource_guard import ResourceGuard, ResourceUnsafeError
    
    fake_model = tmp_path / "stop_test.gguf"
    fake_model.write_text("fake")
    
    guard = ResourceGuard.get_instance()
    guard.level = "STOP"
    
    benchmark = ModelBenchmark(str(fake_model))
    with pytest.raises(ResourceUnsafeError):
        await benchmark.run_inference_test()
    
    guard.level = "SAFE" # Reset para outros testes
