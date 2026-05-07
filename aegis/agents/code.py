"""
aegis/agents/code.py

Agente especializado em codificacao, execucao de scripts e controle de versao.
Implementa o loop plan -> execute -> observe -> iterate.
"""
from __future__ import annotations

import json
import re
import structlog
from typing import Any, List, Optional
from anthropic import AsyncAnthropic

from aegis.agents.base import BaseAgent, AgentResult
from aegis.core.context import Context
from aegis.core.config import get_settings
from aegis.tools.base import BaseTool
from aegis.tools.run_code import RunCodeTool
from aegis.tools.file_system import FileSystemTool
from aegis.tools.git import GitTool

logger = structlog.get_logger(__name__)

CODE_AGENT_PROMPT = """
Voce eh o CodeAgent do sistema AEGIS. Sua funcao eh auxiliar o usuario em tarefas de programacao, depuracao, manipulacao de arquivos e controle de versao.

Ferramentas disponiveis:
{tools_description}

Instrucoes:
1. Analise a solicitacao do usuario e o contexto tecnico.
2. Planeje os passos necessarios para resolver o problema (ex: ler arquivo -> corrigir -> testar -> commitar).
3. Chame as ferramentas uma por uma.
4. Apos cada chamada, voce recebera a observacao (resultado).
5. Use 'run_code' para testar logic de Python de forma isolada.
6. Use 'file_system' para ler ou escrever arquivos no projeto.
7. Use 'git' para gerenciar versoes se solicitado.
8. Quando concluir ou se encontrar um erro insoluvel, forneca uma resposta final clara.

Formato de Saida (JSON):
Para chamar uma ferramenta:
{{
    "thought": "Explicacao do raciocinio atual.",
    "tool": "nome_da_ferramenta",
    "params": {{ "arg1": "val1" }}
}}

Para finalizar:
{{
    "thought": "Explicacao final do que foi feito.",
    "finish": "Mensagem final para o usuario."
}}

Contexto atual:
{context_summary}

Solicitacao do Usuario: {task}
"""

class CodeAgent(BaseAgent):
    """
    Agente que auxilia em tarefas de desenvolvimento de software.
    """

    name: str = "code"
    description: str = "Especialista em programacao, execucao de codigo e gestao de arquivos/repositorios."
    max_steps: int = 10  # Code tasks can be complex

    def __init__(self, anthropic_client: Optional[AsyncAnthropic] = None):
        self.settings = get_settings()
        self.anthropic_client = anthropic_client or AsyncAnthropic(
            api_key=self.settings.ANTHROPIC_API_KEY.get_secret_value()
        )
        self._tools = {
            "run_code": RunCodeTool(),
            "file_system": FileSystemTool(),
            "git": GitTool()
        }

    def get_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    async def run(self, task: str, context: Context) -> AgentResult:
        """
        Executa o loop autonomo do CodeAgent.
        """
        logger.info("code_agent.started", task=task)
        
        tools_used = []
        observations = []
        
        tools_desc = "\n".join([f"- {t.name}: {t.description} (Params: {t.parameters})" for t in self.get_tools()])
        
        for step in range(self.max_steps):
            history = "\n".join(observations)
            prompt = CODE_AGENT_PROMPT.format(
                tools_description=tools_desc,
                context_summary=f"Sessao: {context.session_id}",
                task=task
            )
            
            if history:
                prompt += f"\n\nObservacoes anteriores:\n{history}"

            try:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    system=prompt,
                    messages=[{"role": "user", "content": "Qual o proximo passo?"}]
                )
                
                content_text = response.content[0].text
                json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
                if not json_match:
                    logger.error("code_agent.invalid_response", response=content_text)
                    return AgentResult(success=False, output="Resposta invalida do agente.", steps_taken=step+1, tools_used=tools_used, error="Invalid JSON format from LLM")
                
                decision = json.loads(json_match.group(0))
                thought = decision.get("thought", "")
                logger.info("code_agent.step", step=step+1, thought=thought)

                if "finish" in decision:
                    return AgentResult(
                        success=True,
                        output=decision["finish"],
                        steps_taken=step + 1,
                        tools_used=list(set(tools_used))
                    )
                
                tool_name = decision.get("tool")
                params = decision.get("params", {})
                
                if tool_name in self._tools:
                    tool = self._tools[tool_name]
                    logger.info("code_agent.calling_tool", tool=tool_name, params=params)
                    result = await tool.execute(**params)
                    tools_used.append(tool_name)
                    
                    obs = f"Step {step+1}: Chamou {tool_name}. Resultado: {'Sucesso' if result.success else 'Erro'}. Dados: {result.data or result.error}"
                    observations.append(obs)
                else:
                    observations.append(f"Step {step+1}: Ferramenta '{tool_name}' nao encontrada.")

            except Exception as e:
                logger.error("code_agent.loop_failed", error=str(e))
                return AgentResult(
                    success=False,
                    output="Erro interno durante a execucao da tarefa de codigo.",
                    steps_taken=step + 1,
                    tools_used=list(set(tools_used)),
                    error=str(e)
                )

        return AgentResult(
            success=False,
            output="Limite de passos atingido sem conclusao.",
            steps_taken=self.max_steps,
            tools_used=list(set(tools_used))
        )
