"""
aegis/agents/research.py

Agente especializado em pesquisa profunda na web.
Utiliza WebSearchTool e WebFetchTool para encontrar e sintetizar informacoes.
"""
from __future__ import annotations

import json
import re
import structlog
from dataclasses import dataclass, field
from typing import Any, List, Optional
from anthropic import AsyncAnthropic

from aegis.agents.base import BaseAgent, AgentResult
from aegis.core.context import Context
from aegis.core.config import get_settings
from aegis.tools.base import BaseTool
from aegis.tools.web_search import WebSearchTool
from aegis.tools.web_fetch import WebFetchTool

logger = structlog.get_logger(__name__)


@dataclass
class ResearchReport:
    """Relatorio final gerado pelo ResearchAgent."""
    summary: str
    sources: List[dict]
    confidence_score: float
    key_findings: List[str]

    def to_str(self) -> str:
        """Formata o relatorio para exibicao."""
        lines = [
            "# Relatório de Pesquisa",
            f"\n{self.summary}",
            "\n## Principais Descobertas:",
        ]
        for finding in self.key_findings:
            lines.append(f"- {finding}")
        
        lines.append("\n## Fontes:")
        for source in self.sources:
            lines.append(f"- [{source.get('title', 'Fonte')}]({source.get('url')})")
        
        lines.append(f"\n**Nível de Confiança:** {self.confidence_score*100:.0f}%")
        return "\n".join(lines)


RESEARCH_PROMPT = """
Você é um Analista de Pesquisa do sistema AEGIS. Sua tarefa é sintetizar as informações coletadas da web em um relatório estruturado e imparcial.

Informações Coletadas:
{collected_data}

Tarefa do Usuário:
{task}

Instruções:
1. Analise cuidadosamente todos os fragmentos de texto coletados.
2. Identifique contradições entre fontes, se houver.
3. Resuma os fatos principais de forma concisa.
4. Extraia as descobertas mais importantes (key findings).
5. Atribua um score de confiança (0.0 a 1.0) com base na qualidade e consistência das fontes.
6. Retorne APENAS um JSON válido seguindo o formato abaixo.

Formato de Saída:
{{
  "summary": "Resumo executivo da pesquisa...",
  "confidence_score": 0.85,
  "key_findings": [
    "Fato relevante 1",
    "Fato relevante 2"
  ]
}}
"""


class ResearchAgent(BaseAgent):
    """
    Agente que realiza pesquisas iterativas na web.
    Busca, seleciona, le e sintetiza informacoes.
    """

    name: str = "research"
    description: str = "Realiza pesquisas profundas na web para responder perguntas complexas ou factuais."
    max_steps: int = 5

    def __init__(self, anthropic_client: Optional[AsyncAnthropic] = None):
        self.settings = get_settings()
        self.anthropic_client = anthropic_client or AsyncAnthropic(
            api_key=self.settings.ANTHROPIC_API_KEY.get_secret_value()
        )

    def get_tools(self) -> list[BaseTool]:
        """Retorna as ferramentas de busca e extração."""
        return [WebSearchTool(), WebFetchTool()]

    async def run(self, task: str, context: Context) -> AgentResult:
        """
        Executa o loop de pesquisa.
        """
        logger.info("research_agent.started", task=task)
        
        search_tool = WebSearchTool()
        fetch_tool = WebFetchTool()
        
        tools_used = []
        
        # 1. Busca Web
        logger.info("research_agent.searching", query=task)
        search_result = await search_tool.execute(query=task, num_results=5)
        tools_used.append(search_tool.name)
        
        if not search_result.success:
            return AgentResult(
                success=False,
                output="Falha ao realizar busca inicial.",
                steps_taken=1,
                tools_used=tools_used,
                error=search_result.error
            )
            
        sources = search_result.data or []
        if not sources:
            return AgentResult(
                success=True,
                output="Nenhum resultado encontrado para a pesquisa.",
                steps_taken=1,
                tools_used=tools_used
            )
            
        # 2. Seleciona e extrai conteudo (limitado a top 3 para evitar estouro de contexto)
        collected_data = []
        top_sources = sources[:3]
        
        for i, source in enumerate(top_sources):
            url = source.get("url")
            if not url:
                continue
                
            logger.info("research_agent.fetching", url=url)
            fetch_result = await fetch_tool.execute(url=url)
            tools_used.append(fetch_tool.name)
            
            if fetch_result.success:
                collected_data.append({
                    "title": source.get("title"),
                    "url": url,
                    "content": fetch_result.data
                })
            else:
                logger.warning("research_agent.fetch_failed", url=url, error=fetch_result.error)
                # Mesmo se falhar o fetch, podemos tentar usar o snippet da busca se houver
                collected_data.append({
                    "title": source.get("title"),
                    "url": url,
                    "content": f"Snippet: {source.get('content', 'Indisponível')}"
                })

        # 3. Sintese via LLM
        logger.info("research_agent.synthesizing", source_count=len(collected_data))
        
        formatted_data = ""
        for i, item in enumerate(collected_data):
            formatted_data += f"--- FONTE {i+1}: {item['title']} ({item['url']}) ---\n"
            formatted_data += f"{item['content']}\n\n"

        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                system=RESEARCH_PROMPT.format(collected_data=formatted_data, task=task),
                messages=[{"role": "user", "content": f"Gere o relatório para: {task}"}]
            )
            
            # Extrair JSON da resposta
            content_text = response.content[0].text
            # Tenta encontrar o JSON se houver conversa em volta
            json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
            if json_match:
                content_text = json_match.group(0)
            
            report_data = json.loads(content_text)
            
            report = ResearchReport(
                summary=report_data.get("summary", "Sem resumo."),
                sources=top_sources,
                confidence_score=report_data.get("confidence_score", 0.5),
                key_findings=report_data.get("key_findings", [])
            )
            
            return AgentResult(
                success=True,
                output=report.to_str(),
                steps_taken=len(tools_used) + 1,
                tools_used=list(set(tools_used))
            )

        except Exception as e:
            logger.error("research_agent.synthesis_failed", error=str(e))
            return AgentResult(
                success=False,
                output="Erro ao sintetizar informações coletadas.",
                steps_taken=len(tools_used),
                tools_used=list(set(tools_used)),
                error=str(e)
            )

