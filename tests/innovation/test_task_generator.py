"""
tests/innovation/test_task_generator.py

Testes unitários para o TaskGenerator.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from aegis.innovation.task_generator import TaskGenerator
from aegis.innovation.analyzer import SystemHealthReport, ErrorPattern
from aegis.agents.innovation import InnovationPriority

@pytest.fixture
def mock_anthropic():
    return AsyncMock()

@pytest.fixture
def generator(mock_anthropic):
    return TaskGenerator(anthropic_client=mock_anthropic)

@pytest.fixture
def sample_report():
    return SystemHealthReport(
        bottlenecks=["Latência P99 crítica detectada: 4.5s"],
        opportunities=["Melhorar cache semântico"],
        recurring_errors=[ErrorPattern(pattern="Timeout API", occurrences=5, severity="HIGH", impact="Lentidão")]
    )

@pytest.mark.asyncio
async def test_generate_success(generator, mock_anthropic, sample_report):
    # Mock da resposta do Claude
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({
        "proposals": [
            {
                "title": "Otimização de Latência",
                "rationale": "Gargalo detectado no relatório.",
                "category": "PERFORMANCE",
                "priority": "high",
                "risk_level": 2,
                "tasks": [
                    {
                        "id": "AUTO.7.1",
                        "title": "Implementar Cache de Embeddings",
                        "description": "Reduzir latência",
                        "deliverables": ["Cache layer"],
                        "acceptance_criteria": ["Latência < 2s"],
                        "estimated_complexity": 3
                    }
                ]
            }
        ]
    }))]
    mock_anthropic.messages.create.return_value = mock_response

    proposals = await generator.generate(sample_report, existing_tasks=[])

    assert len(proposals) == 1
    assert proposals[0].title == "Otimização de Latência"
    assert proposals[0].priority == InnovationPriority.HIGH
    assert len(proposals[0].tasks) == 1
    assert proposals[0].tasks[0].title == "Implementar Cache de Embeddings"

@pytest.mark.asyncio
async def test_deduplication(generator, mock_anthropic, sample_report):
    # Mock da resposta do Claude
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({
        "proposals": [
            {
                "title": "Otimização de Latência",
                "rationale": "Gargalo detectado.",
                "priority": "high",
                "tasks": [{"title": "T1", "description": "D1", "deliverables": ["E1"], "acceptance_criteria": ["C1"]}]
            }
        ]
    }))]
    mock_anthropic.messages.create.return_value = mock_response

    # Já existe uma task com título similar
    existing = [{"title": "Otimizacao de Latencia (P99)"}]
    
    proposals = await generator.generate(sample_report, existing_tasks=existing)

    # Similaridade deve ser > 0.85, logo deve ser filtrado
    assert len(proposals) == 0

@pytest.mark.asyncio
async def test_invalid_json_handling(generator, mock_anthropic, sample_report):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Isso não é um JSON")]
    mock_anthropic.messages.create.return_value = mock_response

    proposals = await generator.generate(sample_report, existing_tasks=[])
    assert len(proposals) == 0
