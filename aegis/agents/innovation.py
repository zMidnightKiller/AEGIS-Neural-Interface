"""
aegis/agents/innovation.py

Agente de meta-nivel responsavel por observar o sistema AEGIS, 
identificar falhas e propor melhorias evolutivas autonomamente.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from aegis.agents.base import BaseAgent, AgentResult
from aegis.core.context import Context
from aegis.tools.base import BaseTool
from aegis.core.config import get_settings
from anthropic import AsyncAnthropic
import json
import re

logger = structlog.get_logger(__name__)


class InnovationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ProposedTask:
    """Representa uma tarefa proposta para evolucao do sistema."""
    id: str
    phase: int
    title: str
    description: str
    deliverables: list[str]
    acceptance_criteria: list[str]
    estimated_complexity: int  # Escala 1-5


@dataclass
class InnovationProposal:
    """Proposta completa de inovacao gerada pelo agente."""
    title: str
    rationale: str
    tasks: list[ProposedTask]
    priority: InnovationPriority
    risk_level: int  # Escala 1-5


INNOVATION_PROMPT = """
Você é o InnovationAgent do sistema AEGIS. Sua função é analisar o estado atual do sistema (métricas, erros, código) e propor melhorias evolutivas.

DADOS DO SISTEMA:
- Métricas: {metrics}
- Friction Log (Erros): {friction_log}
- Codebase: {codebase}

TAREFA:
{task}

INSTRUÇÕES:
1. Identifique o gargalo ou lacuna mais crítico com base nos dados.
2. Proponha uma ou mais tarefas (ProposedTask) para resolver o problema.
3. Garanta que a proposta seja tecnicamente viável e siga os padrões do AEGIS.
4. Retorne APENAS um JSON válido seguindo o formato abaixo.

FORMATO DE SAÍDA:
{{
  "title": "Título da Proposta",
  "rationale": "Justificativa detalhada baseada nos dados analisados.",
  "priority": "high", 
  "risk_level": 2,
  "tasks": [
    {{
      "id": "7.X.Y",
      "phase": 7,
      "title": "Nome da Tarefa",
      "description": "Descrição clara do que deve ser feito.",
      "deliverables": ["Entregável 1", "Entregável 2"],
      "acceptance_criteria": ["Critério 1", "Critério 2"],
      "estimated_complexity": 3
    }}
  ]
}}

Prioridades válidas: low, medium, high, critical.
"""


class InnovationAgent(BaseAgent):
    """
    Agente que analisa metricas de uso, logs de erro e codigo-fonte
    para gerar propostas de melhoria autonoma (Innovation Loop).
    """

    name: str = "innovation"
    description: str = (
        "Analisa o sistema AEGIS para identificar gargalos e propor melhorias. "
        "Opera em modo de meta-nivel, nao respondendo diretamente a usuarios."
    )
    max_steps: int = 10

    def __init__(self, anthropic_client: AsyncAnthropic | None = None):
        self.settings = get_settings()
        self.anthropic_client = anthropic_client or AsyncAnthropic(
            api_key=self.settings.ANTHROPIC_API_KEY.get_secret_value()
        )

    def get_tools(self) -> list[BaseTool]:
        """Retorna ferramentas exclusivas de analise e escrita de governanca."""
        from aegis.tools.innovation import (
            ReadMetricsTool,
            ReadFrictionLogTool,
            ReadCodebaseTool,
            WritePRDTasksTool,
            WriteDirectiveTool,
            RunBenchmarkTool
        )
        return [
            ReadMetricsTool(),
            ReadFrictionLogTool(),
            ReadCodebaseTool(),
            WritePRDTasksTool(),
            WriteDirectiveTool(),
            RunBenchmarkTool()
        ]

    async def run(self, task: str, context: Context) -> AgentResult:
        """
        Executa o loop de inovacao.
        """
        logger.info("innovation_agent.started", trigger=task)
        
        tools = {t.name: t for t in self.get_tools()}
        tools_used = []
        
        try:
            # 1. Coleta de dados
            logger.info("innovation_agent.collecting_data")
            
            metrics_res = await tools["read_metrics"].execute()
            friction_res = await tools["read_friction_log"].execute()
            code_res = await tools["read_codebase"].execute()
            
            tools_used.extend(["read_metrics", "read_friction_log", "read_codebase"])
            
            # 2. Geração da Proposta via LLM
            logger.info("innovation_agent.generating_proposal")
            
            prompt = INNOVATION_PROMPT.format(
                metrics=json.dumps(metrics_res.data),
                friction_log=friction_res.data[:2000] if friction_res.success else "N/A",
                codebase=json.dumps(code_res.data),
                task=task
            )
            
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                system=prompt,
                messages=[{"role": "user", "content": f"Analise o sistema e gere propostas para: {task}"}]
            )
            
            content_text = response.content[0].text
            json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
            if json_match:
                content_text = json_match.group(0)
            
            proposal_data = json.loads(content_text)
            
            # 3. Escrita da proposta (Opcional, mas útil para o Loop)
            write_res = await tools["write_prd_tasks"].execute(tasks=proposal_data.get("tasks", []))
            tools_used.append("write_prd_tasks")
            
            output = f"Inovação proposta: {proposal_data.get('title')}\n\n{proposal_data.get('rationale')}"
            
            return AgentResult(
                success=True,
                output=output,
                steps_taken=len(tools_used),
                tools_used=tools_used
            )
            
        except Exception as e:
            logger.error("innovation_agent.failed", error=str(e))
            return AgentResult(
                success=False,
                output=f"Erro ao executar loop de inovacao: {str(e)}",
                steps_taken=len(tools_used),
                tools_used=tools_used,
                error=str(e)
            )
