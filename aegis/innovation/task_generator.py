"""
aegis/innovation/task_generator.py

Motor que utiliza LLM para transformar o SystemHealthReport em InnovationProposals.
Inclui lógica de desduplicação e validação de formato.
"""
from __future__ import annotations

import json
import re
import difflib
import structlog
from typing import List, Dict, Any
from anthropic import AsyncAnthropic

from aegis.core.config import get_settings
from aegis.innovation.analyzer import SystemHealthReport
from aegis.agents.innovation import InnovationProposal, ProposedTask, InnovationPriority
from aegis.personality.prompts import TASK_GENERATOR_PROMPT

logger = structlog.get_logger(__name__)

class TaskGenerator:
    """
    Gera propostas de inovação a partir de relatórios de saúde do sistema.
    """

    def __init__(self, anthropic_client: AsyncAnthropic | None = None):
        self.settings = get_settings()
        self.anthropic_client = anthropic_client or AsyncAnthropic(
            api_key=self.settings.ANTHROPIC_API_KEY.get_secret_value()
        )

    async def generate(self, report: SystemHealthReport, existing_tasks: List[Dict[str, Any]]) -> List[InnovationProposal]:
        """
        Gera uma lista de propostas validadas e desduplicadas.
        """
        logger.info("task_generator.generating", 
                    bottlenecks=len(report.bottlenecks), 
                    opportunities=len(report.opportunities))
        
        # 1. Preparar o prompt
        report_data = {
            "bottlenecks": report.bottlenecks,
            "gaps": report.gaps,
            "opportunities": report.opportunities,
            "recurring_errors": [
                {
                    "pattern": e.pattern,
                    "occurrences": e.occurrences,
                    "severity": e.severity,
                    "impact": e.impact
                } for e in report.recurring_errors
            ]
        }
        
        prompt = TASK_GENERATOR_PROMPT.format(report=json.dumps(report_data, indent=2))
        
        # 2. Chamada ao LLM
        try:
            # Modo de demonstração para chaves dummy
            if self.settings.ANTHROPIC_API_KEY.get_secret_value() == "dummy_key":
                logger.info("task_generator.demo_mode_active")
                return [
                    InnovationProposal(
                        title="Otimizacao de Pulsos de Dados",
                        rationale="Melhorar a visualizacao da rede neural para maior clareza operacional.",
                        priority=InnovationPriority.MEDIUM,
                        risk_level=1,
                        tasks=[
                            ProposedTask(
                                id="AUTO.8.1",
                                phase=8,
                                title="Data Pulse Trail Effect",
                                description="Adicionar rastro de luz aos pulsos de dados na interface.",
                                deliverables=["Shader de rastro", "Configuracao de duracao"],
                                acceptance_criteria="Rastro visivel e suave a 60fps",
                                estimated_complexity=2
                            )
                        ]
                    )
                ]

            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                system="Você é um arquiteto de sistemas especializado em evolução autônoma.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error("task_generator.invalid_response", content=content)
                return []
                
            data = json.loads(json_match.group(0))
            raw_proposals = data.get("proposals", [])
            
            # 3. Validação e Desduplicação
            final_proposals = []
            import unicodedata
            
            def normalize(s: str) -> str:
                return "".join(
                    c for c in unicodedata.normalize("NFD", s.lower())
                    if unicodedata.category(c) != "Mn"
                )

            for p_data in raw_proposals:
                proposal = self._parse_proposal(p_data)
                if not proposal:
                    continue
                
                # Desduplicação
                is_duplicate = False
                norm_title = normalize(proposal.title)
                for existing in existing_tasks:
                    norm_existing = normalize(existing.get("title", ""))
                    similarity = difflib.SequenceMatcher(None, norm_title, norm_existing).ratio()
                    if similarity > 0.85:
                        logger.info("task_generator.duplicate_detected", title=proposal.title, similarity=similarity)
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    final_proposals.append(proposal)
            
            logger.info("task_generator.finished", generated=len(raw_proposals), accepted=len(final_proposals))
            return final_proposals

        except Exception as e:
            logger.error("task_generator.failed", error=str(e))
            return []

    def _parse_proposal(self, data: Dict[str, Any]) -> InnovationProposal | None:
        """Valida e converte dicionário em InnovationProposal."""
        try:
            tasks = []
            for t in data.get("tasks", []):
                # Validação básica de campos obrigatórios
                if not all(k in t for k in ["title", "description", "deliverables", "acceptance_criteria"]):
                    continue
                    
                tasks.append(ProposedTask(
                    id=t.get("id", "AUTO.X.Y"),
                    phase=t.get("phase", 7),
                    title=t.get("title"),
                    description=t.get("description"),
                    deliverables=t.get("deliverables"),
                    acceptance_criteria=t.get("acceptance_criteria"),
                    estimated_complexity=t.get("estimated_complexity", 3)
                ))
            
            if not tasks:
                return None
                
            # Mapeamento seguro para o Enum InnovationPriority
            priority_str = data.get("priority", "medium").upper()
            try:
                priority = InnovationPriority[priority_str]
            except KeyError:
                priority = InnovationPriority.MEDIUM

            return InnovationProposal(
                title=data.get("title", "Sem Título"),
                rationale=data.get("rationale", ""),
                priority=priority,
                risk_level=data.get("risk_level", 3),
                tasks=tasks
            )
        except Exception as e:
            logger.warning("task_generator.parse_failed", error=str(e))
            return None
