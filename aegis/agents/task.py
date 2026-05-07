"""
aegis/agents/task.py

Agente especializado em automação de tarefas (Calendário, Email, Notificações).
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
from aegis.tools.calendar import CalendarTool
from aegis.tools.email import EmailTool

logger = structlog.get_logger(__name__)

TASK_AGENT_PROMPT = """
Você é o TaskAgent do sistema AEGIS. Sua função é gerenciar a agenda, e-mails e tarefas do usuário de forma autônoma e eficiente.

Ferramentas disponíveis:
{tools_description}

Instruções:
1. Analise a solicitação do usuário e o contexto.
2. Planeje os passos necessários.
3. Chame as ferramentas uma por uma.
4. Após cada chamada, você receberá a observação (resultado).
5. Se a tarefa exigir múltiplos passos (ex: verificar calendário antes de agendar), faça-os sequencialmente.
6. Quando concluir ou se encontrar um erro impossível de resolver, forneça uma resposta final clara.

Formato de Saída (JSON):
Para chamar uma ferramenta:
{{
    "thought": "Explicação do raciocínio atual.",
    "tool": "nome_da_ferramenta",
    "params": {{ "arg1": "val1" }}
}}

Para finalizar:
{{
    "thought": "Explicação final.",
    "finish": "Mensagem final para o usuário."
}}

Contexto atual:
{context_summary}

Solicitação do Usuário: {task}
"""

class TaskAgent(BaseAgent):
    """
    Agente que automatiza tarefas de produtividade.
    Gerencia calendário e e-mails.
    """

    name: str = "task"
    description: str = "Gerencia compromissos no calendário, envia e-mails e organiza tarefas do usuário."
    max_steps: int = 5

    def __init__(self, anthropic_client: Optional[AsyncAnthropic] = None):
        self.settings = get_settings()
        self.anthropic_client = anthropic_client or AsyncAnthropic(
            api_key=self.settings.ANTHROPIC_API_KEY.get_secret_value()
        )
        self._tools = {
            "calendar": CalendarTool(),
            "email": EmailTool()
        }

    def get_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    async def run(self, task: str, context: Context) -> AgentResult:
        """
        Executa o loop autônomo do TaskAgent.
        """
        logger.info("task_agent.started", task=task)
        
        tools_used = []
        observations = []
        
        tools_desc = "\n".join([f"- {t.name}: {t.description} (Params: {t.parameters})" for t in self.get_tools()])
        
        for step in range(self.max_steps):
            # Preparar o histórico de observações para o LLM
            history = "\n".join(observations)
            prompt = TASK_AGENT_PROMPT.format(
                tools_description=tools_desc,
                context_summary=f"Sessão: {context.session_id}",
                task=task
            )
            
            if history:
                prompt += f"\n\nObservações anteriores:\n{history}"

            try:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    system=prompt,
                    messages=[{"role": "user", "content": "Qual o próximo passo?"}]
                )
                
                content_text = response.content[0].text
                # Extrair JSON
                json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
                if not json_match:
                    logger.error("task_agent.invalid_response", response=content_text)
                    return AgentResult(success=False, output="Resposta inválida do agente.", steps_taken=step+1, tools_used=tools_used, error="Invalid JSON format from LLM")
                
                decision = json.loads(json_match.group(0))
                thought = decision.get("thought", "")
                logger.info("task_agent.step", step=step+1, thought=thought)

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
                    logger.info("task_agent.calling_tool", tool=tool_name, params=params)
                    
                    from aegis.core.security import security_manager
                    try:
                        result = await security_manager.verify_and_execute(
                            user_id=context.session_id,
                            action_name=tool_name,
                            params=params,
                            func=tool.execute
                        )
                        tools_used.append(tool_name)
                        obs = f"Step {step+1}: Chamou {tool_name}. Resultado: {'Sucesso' if result.success else 'Erro'}. Dados: {result.data or result.error}"
                    except PermissionError as pe:
                        obs = f"Step {step+1}: Chamada bloqueada pela segurança: {str(pe)}"
                        logger.warning("task_agent.tool_blocked", tool=tool_name, error=str(pe))
                    
                    observations.append(obs)
                else:
                    observations.append(f"Step {step+1}: Ferramenta '{tool_name}' não encontrada.")

            except Exception as e:
                logger.error("task_agent.loop_failed", error=str(e))
                return AgentResult(
                    success=False,
                    output="Erro interno durante a execução da tarefa.",
                    steps_taken=step + 1,
                    tools_used=list(set(tools_used)),
                    error=str(e)
                )

        return AgentResult(
            success=False,
            output="Limite de passos atingido sem conclusão.",
            steps_taken=self.max_steps,
            tools_used=list(set(tools_used))
        )
