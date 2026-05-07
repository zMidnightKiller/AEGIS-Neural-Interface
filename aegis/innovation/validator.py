"""
aegis/innovation/validator.py

Sistema de validação e aprovação de tarefas geradas pelo Innovation Loop.
Suporta modos SUPERVISED (manual) e AUTONOMOUS (automático com base em risco).
"""
from __future__ import annotations

import structlog
from typing import List, Dict, Any
from aegis.core.config import get_settings
from aegis.agents.innovation import InnovationProposal
from aegis.tools.innovation import WritePRDTasksTool

logger = structlog.get_logger(__name__)

class TaskValidator:
    """
    Valida e aprova propostas de inovação geradas pelo TaskGenerator.
    """

    def __init__(self):
        self.settings = get_settings()
        self.writer = WritePRDTasksTool()

    async def validate(self, proposals: List[InnovationProposal]) -> Dict[str, Any]:
        """
        Valida as propostas e decide entre aprovação automática ou manual.
        
        Args:
            proposals: Lista de propostas geradas.
            
        Returns:
            Dicionário com contagem de aprovadas, pendentes e rejeitadas.
        """
        # Tenta ler o modo do settings, fallback para SUPERVISED
        mode = "SUPERVISED"
        try:
            mode = self.settings.AEGIS_MODE.value if hasattr(self.settings.AEGIS_MODE, "value") else str(self.settings.AEGIS_MODE)
            # Se for STANDARD/ANALYSIS etc, mapeamos para SUPERVISED por segurança
            if mode not in ["AUTONOMOUS", "SUPERVISED"]:
                mode = "SUPERVISED"
        except Exception:
            mode = "SUPERVISED"

        logger.info("task_validator.validating", count=len(proposals), mode=mode)

        approved = []
        pending = []

        for proposal in proposals:
            # Validação baseada em risco e complexidade
            is_low_risk = self._check_risk(proposal)
            
            if is_low_risk and mode == "AUTONOMOUS":
                approved.append(proposal)
            else:
                # Propostas de alto risco ou em modo SUPERVISED ficam pendentes
                pending.append(proposal)

        # Executar ações de persistência
        if approved:
            await self._apply_approvals(approved)
        
        if pending:
            await self._persist_proposals(pending)

        results = {
            "approved": len(approved),
            "pending": len(pending),
            "total": len(proposals)
        }
        
        logger.info("task_validator.finished", **results)
        return results

    def _check_risk(self, proposal: InnovationProposal) -> bool:
        """
        Verifica se a proposta atende aos critérios de baixo risco para execução autônoma.
        """
        # 1. Risco declarado pelo agente (1-5)
        if proposal.risk_level >= 3:
            return False
            
        for task in proposal.tasks:
            # 2. Complexidade estimada (1-5)
            if task.estimated_complexity >= 3:
                return False
            
            # 3. Blacklist de termos perigosos
            dangerous_terms = ["delete", "drop", "overwrite", "schema", "database", "flush", "rm -rf"]
            desc_lower = task.description.lower()
            if any(term in desc_lower for term in dangerous_terms):
                return False
                
            # 4. Fases críticas (apenas fase 7 ou superior são permitidas autonomamente por agora)
            if task.phase < 7:
                return False

        return True

    async def _apply_approvals(self, proposals: List[InnovationProposal]):
        """
        Persiste propostas aprovadas diretamente no fluxo de execução (PRD.md).
        """
        logger.info("task_validator.applying_approvals", count=len(proposals))
        tasks_to_write = []
        for p in proposals:
            for t in p.tasks:
                tasks_to_write.append({
                    "id": t.id,
                    "phase": t.phase,
                    "title": f"AUTO: {t.title}",
                    "description": t.description,
                    "deliverables": t.deliverables,
                    "acceptance_criteria": t.acceptance_criteria,
                    "estimated_complexity": t.estimated_complexity
                })
        
        # Em modo real, isso anexaria ao PRD.md. 
        # Seguindo a regra de não editar o PRD.md diretamente como sub-agente de DEV,
        # vamos usar um arquivo auxiliar que a Engine pode ler ou o próximo loop processar.
        await self.writer.execute(tasks=tasks_to_write, target="prd_approved.md")

    async def _persist_proposals(self, proposals: List[InnovationProposal]):
        """
        Escreve propostas que requerem revisão humana em prd_proposals.md.
        """
        logger.info("task_validator.persisting_proposals", count=len(proposals))
        tasks_to_write = []
        for p in proposals:
            for t in p.tasks:
                tasks_to_write.append({
                    "id": t.id,
                    "phase": t.phase,
                    "title": t.title,
                    "description": f"RATIONALE: {p.rationale}\n\nRISK: {p.risk_level}\n\n{t.description}",
                    "deliverables": t.deliverables,
                    "acceptance_criteria": t.acceptance_criteria,
                    "estimated_complexity": t.estimated_complexity
                })
        
        await self.writer.execute(tasks=tasks_to_write, target="prd_proposals.md")
