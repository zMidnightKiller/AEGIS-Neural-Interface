import sys
import os
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path
root_dir = Path(__file__).parent.parent.absolute()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
from functools import lru_cache
from unittest.mock import MagicMock

# Define variaveis de ambiente para testes ANTES de qualquer import do aegis
os.environ["ANTHROPIC_API_KEY"] = "fake-key"
os.environ["OPENAI_API_KEY"] = "fake-key"
os.environ["ELEVENLABS_API_KEY"] = "fake-key"
os.environ["TAVILY_API_KEY"] = "fake-key"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["CHROMA_PERSIST_DIR"] = "./.tmp/chroma_test"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_PASSWORD"] = "fake-password"

# Moca o modulo celery globalmente para os testes
mock_celery = MagicMock()
def mock_task_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper
mock_celery.Celery.return_value.task = mock_task_decorator
sys.modules["celery"] = mock_celery
sys.modules["celery.result"] = MagicMock()
sys.modules["langfuse"] = MagicMock()
sys.modules["prometheus_fastapi_instrumentator"] = MagicMock()

from aegis.core.config import get_settings

@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Limpa o cache do lru_cache de get_settings antes de cada teste."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
