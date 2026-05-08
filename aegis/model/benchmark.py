"""
aegis/model/benchmark.py

Suite de benchmark para modelos locais no AEGIS.
Mede latência, tokens/s, pico de VRAM e qualidade básica.
"""
import time
import json
import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, List, Dict, Any

import structlog
import torch
from aegis.core.resource_guard import ResourceGuard

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

# Tenta importar as configurações do AEGIS
try:
    from aegis.core.config import get_settings
except ImportError:
    # Fallback para execução isolada se necessário
    def get_settings():
        class MockSettings:
            AEGIS_GPU_LAYERS = 28
            AEGIS_CONTEXT_LENGTH = 4096
            AEGIS_MODEL_PATH = "./models/mistral-7b-instruct-v0.3-q4_k_m.gguf"
        return MockSettings()

logger = structlog.get_logger(__name__)

@dataclass
class BenchmarkResult:
    model_name: str
    timestamp: str
    tokens_per_second: float
    time_to_first_token_ms: float
    total_tokens: int
    vram_peak_gb: float
    config: Dict[str, Any]

class ModelBenchmark:
    """Ferramenta para medir performance de modelos locais na RTX 3060."""

    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model_name = self.model_path.name
        if Llama is None:
            logger.warning("benchmark.dependency_missing", dependency="llama-cpp-python")

    def _get_vram_usage(self) -> float:
        """Retorna uso de VRAM em GB via torch."""
        if torch.cuda.is_available():
            # Resetamos o pico antes para pegar apenas o desta operação
            return torch.cuda.max_memory_allocated() / (1024**3)
        return 0.0

    async def run_inference_test(self, prompt: str = "Explique o que é uma RTX 3060 em um parágrafo.") -> BenchmarkResult:
        """Executa um teste de inferência e mede performance."""
        if Llama is None:
            raise ImportError("llama-cpp-python não instalado.")

        guard = ResourceGuard.get_instance()
        await guard.assert_safe("benchmark")

        settings = get_settings()
        logger.info("benchmark.start", model=self.model_name)
        
        # Tenta resetar estatísticas do torch se disponível
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
        
        inference_start = time.time()
        
        # Inicializa modelo
        # Nota: O carregamento do modelo consome VRAM que queremos medir
        try:
            model = Llama(
                model_path=str(self.model_path),
                n_gpu_layers=getattr(settings, "AEGIS_GPU_LAYERS", 28),
                n_ctx=getattr(settings, "AEGIS_CONTEXT_LENGTH", 4096),
                verbose=False
            )
        except Exception as e:
            logger.error("benchmark.load_error", model=self.model_name, error=str(e))
            raise

        first_token_time = None
        token_count = 0
        
        # Gera tokens
        # model() é síncrono no llama-cpp-python, mas usamos stream=True
        output = model(
            prompt,
            max_tokens=512,
            temperature=0.7,
            stream=True
        )
        
        generation_start = time.time()
        for chunk in output:
            if first_token_time is None:
                first_token_time = time.time()
            token_count += 1
            
        end_time = time.time()
        
        duration = end_time - generation_start
        # Evita divisão por zero e garante tps > 0 se tokens foram gerados (útil em testes)
        safe_duration = max(duration, 0.001) if token_count > 0 else duration
        
        ttft = (first_token_time - generation_start) * 1000 if first_token_time else 0
        tps = token_count / safe_duration if safe_duration > 0 else 0
        vram_peak = self._get_vram_usage()
        
        result = BenchmarkResult(
            model_name=self.model_name,
            timestamp=datetime.now().isoformat(),
            tokens_per_second=round(tps, 2),
            time_to_first_token_ms=round(ttft, 2),
            total_tokens=token_count,
            vram_peak_gb=round(vram_peak, 2),
            config={
                "gpu_layers": getattr(settings, "AEGIS_GPU_LAYERS", 28),
                "ctx_length": getattr(settings, "AEGIS_CONTEXT_LENGTH", 4096)
            }
        )
        
        logger.info("benchmark.complete", **asdict(result))
        return result

    def save_report(self, result: BenchmarkResult):
        """Salva o resultado em ./benchmarks/."""
        report_dir = Path("./benchmarks")
        report_dir.mkdir(exist_ok=True)
        
        report_path = report_dir / f"baseline_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)
        
        logger.info("benchmark.report_saved", path=str(report_path))

if __name__ == "__main__":
    async def main():
        import sys
        settings = get_settings()
        path = sys.argv[1] if len(sys.argv) > 1 else getattr(settings, "AEGIS_MODEL_PATH", None)
        
        if not path or not Path(path).exists():
            print(f"Modelo não encontrado: {path}")
            return
            
        benchmark = ModelBenchmark(path)
        try:
            result = await benchmark.run_inference_test()
            benchmark.save_report(result)
            print(f"Benchmark concluído para {result.model_name}: {result.tokens_per_second} tok/s")
        except Exception as e:
            print(f"Erro no benchmark: {e}")

    asyncio.run(main())
