"""
tests/innovation/test_validator.py

Testes unitários para o TaskValidator.
"""
import pytest
from unittest.mock import AsyncMock, patch
from aegis.innovation.validator import TaskValidator
from aegis.agents.innovation import InnovationProposal, ProposedTask, InnovationPriority

@pytest.fixture
def validator():
    with patch("aegis.core.config.get_settings"):
        return TaskValidator()

@pytest.fixture
def sample_proposals():
    return [
        InnovationProposal(
            title="Baixo Risco",
            rationale="Melhoria simples",
            priority=InnovationPriority.LOW,
            risk_level=1,
            tasks=[
                ProposedTask(
                    id="7.4.1",
                    phase=7,
                    title="Tarefa Simples",
                    description="Fazer algo simples",
                    deliverables=["D1"],
                    acceptance_criteria=["C1"],
                    estimated_complexity=2
                )
            ]
        ),
        InnovationProposal(
            title="Alto Risco",
            rationale="Mudança profunda",
            priority=InnovationPriority.CRITICAL,
            risk_level=4,
            tasks=[
                ProposedTask(
                    id="7.4.2",
                    phase=7,
                    title="Tarefa Complexa",
                    description="Fazer algo complexo",
                    deliverables=["D2"],
                    acceptance_criteria=["C2"],
                    estimated_complexity=5
                )
            ]
        )
    ]

@pytest.mark.asyncio
async def test_validate_supervised_mode(validator, sample_proposals):
    # Mockando explicitamente o atributo AEGIS_MODE no settings
    validator.settings.AEGIS_MODE = "SUPERVISED"
    
    with patch.object(validator.writer, "execute", new_callable=AsyncMock) as mock_write:
        results = await validator.validate(sample_proposals)
        
        assert results["pending"] == 2
        assert results["approved"] == 0
        # Deve escrever apenas no prd_proposals.md
        assert mock_write.call_count == 1
        assert mock_write.call_args[1]["target"] == "prd_proposals.md"

@pytest.mark.asyncio
async def test_validate_autonomous_mode(validator, sample_proposals):
    validator.settings.AEGIS_MODE = "AUTONOMOUS"
    
    with patch.object(validator.writer, "execute", new_callable=AsyncMock) as mock_write:
        results = await validator.validate(sample_proposals)
        
        assert results["approved"] == 1  # Apenas a de baixo risco
        assert results["pending"] == 1   # A de alto risco continua pendente
        
        # Deve escrever em ambos os arquivos
        assert mock_write.call_count == 2
        targets = [call[1]["target"] for call in mock_write.call_args_list]
        assert "prd_approved.md" in targets
        assert "prd_proposals.md" in targets

@pytest.mark.asyncio
async def test_risk_check_dangerous_terms(validator):
    proposal = InnovationProposal(
        title="Perigosa",
        rationale="Tentativa de drop",
        priority=InnovationPriority.HIGH,
        risk_level=1, # Baixo risco declarado, mas conteúdo perigoso
        tasks=[
            ProposedTask(
                id="7.4.3",
                phase=7,
                title="Drop database",
                description="DROP DATABASE prod",
                deliverables=[],
                acceptance_criteria=[],
                estimated_complexity=1
            )
        ]
    )
    
    assert validator._check_risk(proposal) is False

@pytest.mark.asyncio
async def test_risk_check_phase_restriction(validator):
    proposal = InnovationProposal(
        title="Fase Antiga",
        rationale="Modificando fase 1",
        priority=InnovationPriority.MEDIUM,
        risk_level=1,
        tasks=[
            ProposedTask(
                id="1.1.2",
                phase=1,
                title="Mudar algo na base",
                description="Alteração legada",
                deliverables=[],
                acceptance_criteria=[],
                estimated_complexity=1
            )
        ]
    )
    
    # Não deve permitir alterações em fases anteriores à 7 autonomamente
    assert validator._check_risk(proposal) is False
