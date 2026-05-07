"""
tests/core/test_tasks.py

Testes unitarios para as tarefas do Celery.
Moca a infraestrutura do Celery e o motor para testar a logica das tarefas.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os

import sys
from unittest.mock import MagicMock

# Moca o modulo celery antes de importar qualquer coisa do projeto
mock_celery = MagicMock()
def mock_task_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper
mock_celery.Celery.return_value.task = mock_task_decorator
sys.modules["celery"] = mock_celery
sys.modules["celery.result"] = MagicMock()

# Define fake env vars antes de qualquer import do projeto
os.environ["ANTHROPIC_API_KEY"] = "fake-key"

from aegis.core.tasks import process_agent_task, health_check_task
from aegis.core.models import AgentResponse

@pytest.fixture
def mock_engine():
    with patch("aegis.core.tasks.Engine") as mock:
        engine_instance = mock.return_value
        engine_instance.process = AsyncMock()
        yield engine_instance

class TestCeleryTasks:
    def test_health_check_task(self):
        """Testa se a tarefa de health check retorna a string correta."""
        result = health_check_task()
        assert result == "Celery is working!"

    def test_process_agent_task_success(self, mock_engine):
        """Testa o processamento bem-sucedido de uma tarefa de agente."""
        # Configura o mock do motor para retornar uma resposta de sucesso
        mock_engine.process.return_value = AgentResponse(
            text="Resposta do AEGIS",
            agent_used="research",
            tools_used=["web_search"],
            memory_injected=True,
            latency_ms=100
        )
        
        # Executa a tarefa (chamando diretamente, sem .delay() para testar a logica)
        result = process_agent_task(
            text="Qual a temperatura em Marte?",
            session_id="test-session",
            mode="STANDARD"
        )
        
        assert result["success"] is True
        assert result["text"] == "Resposta do AEGIS"
        assert result["agent_used"] == "research"
        assert "web_search" in result["tools_used"]

    def test_process_agent_task_failure(self, mock_engine):
        """Testa o comportamento da tarefa quando o motor falha."""
        # Configura o mock para levantar uma excecao
        mock_engine.process.side_effect = Exception("Erro simulado no motor")
        
        result = process_agent_task(
            text="falha",
            session_id="test-session",
            mode="STANDARD"
        )
        
        assert result["success"] is False
        assert "Erro simulado no motor" in result["error"]
