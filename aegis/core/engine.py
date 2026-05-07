"""
aegis/core/engine.py

Orquestrador principal do sistema AEGIS.
Responsavel por processar UserInput e coordenar agentes e ferramentas.
"""
from __future__ import annotations

import time
import structlog
from aegis.core.models import UserInput, AgentResponse, OperatingMode, Message
from aegis.core.config import get_settings
from aegis.core.context import Context
from aegis.core.observability import obs_manager
from aegis.memory.working import WorkingMemory
from aegis.tools.web_search import WebSearchTool
from aegis.tools.web_fetch import WebFetchTool
from aegis.agents.research import ResearchAgent
from aegis.agents.memory import MemoryAgent
from aegis.agents.media import MediaAgent
from aegis.agents.task import TaskAgent
from aegis.agents.code import CodeAgent
from aegis.core.orchestrator import MultiAgentOrchestrator
from aegis.tools.vision import VisionTool
from aegis.tools.image_generation import ImageGenerationTool
from aegis.core.cache import SemanticCache
from aegis.plugins.manager import PluginManager
from aegis.core.events import event_bus
from aegis.personality.prompts import (
    build_system_prompt, 
    CLASSIFIER_PROMPT, 
    DECOMPOSITION_PROMPT,
    COMPRESSION_PROMPT
)
from aegis.core.llm import LLMClient
import json

logger = structlog.get_logger(__name__)


class Engine:
    """
    O motor central do AEGIS.
    Gerencia o pipeline de processamento: Entrada -> Roteamento -> Execucao -> Resposta.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.tools = {
            "web_search": WebSearchTool(),
            "web_fetch": WebFetchTool(),
            "vision": VisionTool(),
            "image_generation": ImageGenerationTool(),
        }
        self.agents = {
            "research": ResearchAgent(),
            "memory": MemoryAgent(),
            "media": MediaAgent(),
            "task": TaskAgent(),
            "code": CodeAgent(),
        }
        self.orchestrator = MultiAgentOrchestrator()
        self.llm_client = LLMClient()
        self.cache = SemanticCache()
        self.plugin_manager = PluginManager()
        self._initialized = False
        logger.info("engine.initialized", project=self.settings.PROJECT_NAME, version=self.settings.VERSION)

    async def initialize(self) -> None:
        """Inicializa componentes assncronos (como plugins)."""
        if self._initialized:
            return
        
        logger.info("engine.initializing_plugins")
        await self.plugin_manager.load_all()
        self._initialized = True
        logger.info("engine.initialization_complete")

    async def process(self, user_input: UserInput) -> AgentResponse:
        """
        Processa uma entrada do usuario e retorna uma resposta do agente.

        Args:
            user_input: Objeto contendo o texto, session_id e modo de operacao.

        Returns:
            AgentResponse estruturado.
        """
        start_time = time.perf_counter()
        
        # 0. Verificar Cache Semantico
        if self.settings.ENABLE_SEMANTIC_CACHE:
            cached_response = await self.cache.get(user_input.text)
            if cached_response:
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                return AgentResponse(
                    text=cached_response,
                    agent_used="semantic_cache",
                    tools_used=[],
                    memory_injected=False,
                    latency_ms=latency_ms
                )

        # 1. Inicializar Memoria e Contexto
        memory = WorkingMemory(user_input.session_id)
        
        # Registro no Langfuse (Observability)
        obs_manager.trace_event(
            name="engine_process",
            user_id=user_input.session_id,
            input_data=user_input.text,
            metadata={"mode": user_input.mode.value}
        )

        from aegis.core.security import audit_logger
        audit_logger.log_action(user_input.session_id, "engine.process_started", {"input": user_input.text})

        history = await memory.get_history(n=10)
        
        context = Context(user_input.session_id)
        # Reconstruir contexto a partir do historico
        for msg in history:
            context.add_message(msg["role"], msg["content"], msg.get("metadata"))
        
        # Adicionar mensagem atual do usuario
        context.add_message("user", user_input.text, metadata={"attachments": user_input.attachments})
        
        # --- NOVO: COMPRESSÃO DE CONTEXTO ---
        if self.settings.ENABLE_CONTEXT_COMPRESSION and context.total_tokens > self.settings.CONTEXT_COMPRESSION_TOKEN_LIMIT:
            await self._compress_context(context)

        await memory.save_message("user", user_input.text)

        # Log de Entrada
        logger.info(
            "engine.process_started",
            session_id=user_input.session_id,
            text=user_input.text[:50],
            mode=user_input.mode.value
        )
        
        await event_bus.emit("thinking", {"session_id": user_input.session_id})

        try:
            # 2. Pipeline de Memoria: Pre-processamento (MemoryAgent)
            memory_agent = self.agents["memory"]
            await event_bus.emit("agent_started", {"agent": "memory", "session_id": user_input.session_id})
            memory_context = await memory_agent.pre_process(user_input.text, context)
            await event_bus.emit("memory_retrieved", {"count": len(memory_context) if memory_context else 0, "session_id": user_input.session_id})
            await event_bus.emit("agent_finished", {"agent": "memory", "success": True, "session_id": user_input.session_id})
            
            # 3. Roteamento: Classificar Intencao
            intent = await self._classify_intent(user_input.text)
            logger.info("engine.intent_identified", intent=intent)

            # 4. Pipeline de Execucao de Agentes
            # Define a sequencia de agentes com base na intencao
            # Por enquanto, mantemos simples, mas preparado para expansao
            pipeline = self._build_pipeline(intent)
            
            response_text = ""
            tools_used = []
            final_agent = intent

            for agent_name in pipeline:
                if agent_name == "core_engine":
                    # Geracao de resposta padrao via LLM
                    response_text = await self._generate_core_response(user_input, context, memory_context)
                elif agent_name == "multi":
                    # Orquestracao paralela/sequencial complexa
                    response_text, multi_tools = await self._handle_multi_agent_request(user_input, context)
                    tools_used.extend(multi_tools)
                else:
                    logger.info("engine.executing_agent", agent=agent_name)
                    agent = self.agents.get(agent_name)
                    if agent:
                        # Protecao via circuit breaker ate para chamadas individuais
                        breaker = self.orchestrator._get_breaker(agent_name)
                        try:
                            await event_bus.emit("agent_started", {"agent": agent_name, "session_id": user_input.session_id})
                            agent_result = await breaker.call(agent.run, user_input.text, context)
                            
                            for tool_name in agent_result.tools_used:
                                await event_bus.emit("tool_called", {"tool": tool_name, "agent": agent_name, "session_id": user_input.session_id})

                            tools_used.extend(agent_result.tools_used)
                            if agent_result.success:
                                response_text = agent_result.output
                                # Injeta output no contexto para o proximo agente se houver
                                context.add_message("assistant", response_text, {"internal": True})
                                await event_bus.emit("agent_finished", {"agent": agent_name, "success": True, "session_id": user_input.session_id})
                            else:
                                response_text = f"Houve um erro no processamento pelo agente {agent_name}: {agent_result.error}"
                                await event_bus.emit("agent_finished", {"agent": agent_name, "success": False, "error": agent_result.error, "session_id": user_input.session_id})
                                break
                        except Exception as e:
                            response_text = f"Falha critica no agente {agent_name} (Circuit Breaker): {str(e)}"
                            await event_bus.emit("error", {"agent": agent_name, "error": str(e), "session_id": user_input.session_id})
                            break
                    else:
                        logger.warning("engine.agent_not_found", agent=agent_name)

            # 5. Salvar Resposta na Memoria de Trabalho
            await memory.save_message("assistant", response_text)
            context.add_message("assistant", response_text)

            # --- NOVO: ATUALIZAR CACHE ---
            if self.settings.ENABLE_SEMANTIC_CACHE and intent != "multi" and intent != "semantic_cache": 
                await self.cache.set(user_input.text, response_text)

            # 6. Pipeline de Memoria: Pos-processamento (MemoryAgent)
            # Extrai fatos e salva episodio
            full_interaction = f"User: {user_input.text}\nAssistant: {response_text}"
            await memory_agent.post_process(full_interaction)

            # 7. Finalizacao
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            response = AgentResponse(
                text=response_text,
                agent_used=final_agent,
                tools_used=list(set(tools_used)), # Remove duplicatas
                memory_injected=bool(memory_context),
                latency_ms=latency_ms
            )

            logger.info(
                "engine.process_completed",
                latency_ms=latency_ms,
                agent=final_agent,
                tools=tools_used
            )
            
            return response

        except Exception as e:
            logger.error("engine.process_failed", error=str(e), exc_info=True)
            raise
        finally:
            await memory.close()

    def _build_pipeline(self, intent: str) -> list[str]:
        """Define a sequencia de agentes a serem executados."""
        if intent == "research":
            return ["research"]
        if intent == "media":
            return ["media"]
        if intent == "task":
            return ["task"]
        if intent == "code":
            return ["code"]
        if intent == "multi":
            return ["multi"]
        return ["core_engine"]

    async def _handle_multi_agent_request(self, user_input: UserInput, context: Context) -> tuple[str, list[str]]:
        """Decompoe a tarefa e executa múltiplos agentes em paralelo onde possivel."""
        logger.info("engine.multi_agent_start", text=user_input.text)
        
        # 1. Decomposicao
        try:
            decomposition_text = await self.llm_client.create_message(
                model="claude-3-haiku-20240307", # Ignorado se provider for Ollama
                max_tokens=500,
                system=DECOMPOSITION_PROMPT,
                messages=[{"role": "user", "content": user_input.text}]
            )
            subtasks = json.loads(decomposition_text)
        except Exception as e:
            logger.error("engine.decomposition_failed", error=str(e))
            return f"Erro ao decompor tarefa: {str(e)}", []

        # 2. Execucao
        # Simplificacao: rodamos tudo em paralelo usando o orquestrador
        agent_tasks = []
        for st in subtasks:
            agent = self.agents.get(st["agent"])
            if agent:
                agent_tasks.append((agent, st["task"], context))
            else:
                logger.warning("engine.multi_agent_not_found", agent=st["agent"])

        if not agent_tasks:
            return "Nenhum agente especializado identificado para as sub-tarefas.", []

        results = await self.orchestrator.run_parallel(agent_tasks)
        
        # 3. Consolidacao
        final_outputs = []
        all_tools = []
        for i, res in enumerate(results):
            agent_name = agent_tasks[i][0].name
            if isinstance(res, Exception):
                final_outputs.append(f"Agente {agent_name} falhou: {str(res)}")
            else:
                all_tools.extend(res.tools_used)
                if res.success:
                    final_outputs.append(f"[{agent_name}]: {res.output}")
                else:
                    final_outputs.append(f"[{agent_name}] erro: {res.error}")

        return "\n\n".join(final_outputs), all_tools

    async def _generate_core_response(self, user_input: UserInput, context: Context, memory_context: str | None) -> str:
        """Gera uma resposta usando o LLM base quando nenhum agente especializado e necessario."""
        system_prompt = build_system_prompt(
            mode=user_input.mode,
            tools_list=[{"name": t.name, "description": t.description} for t in self.tools.values()],
            memory_context=memory_context
        )
        
        response_text = await self.llm_client.create_message(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {"role": m.role, "content": m.content}
                for m in context.messages if m.role != "system"
            ]
        )
        return response_text

    async def _classify_intent(self, text: str) -> str:
        """
        Classifica a intencao do usuario usando LLM.
        """
        try:
            intent_text = await self.llm_client.create_message(
                model="claude-3-haiku-20240307",
                max_tokens=20,
                system=CLASSIFIER_PROMPT,
                messages=[{"role": "user", "content": text}]
            )
            intent = intent_text.strip().lower()
            
            # Limpeza basica (caso o LLM retorne algo extra)
            for valid_intent in ["research", "media", "task", "code", "multi", "core_engine"]:
                if valid_intent in intent:
                    return valid_intent
                    
            logger.warning("engine.invalid_intent_returned", intent=intent)
            return "core_engine"
                
        except Exception as e:
            logger.error("engine.classification_failed", error=str(e))
            return "core_engine" # Fallback seguro

    async def _compress_context(self, context: Context) -> None:
        """Comprime o contexto atual usando LLM."""
        logger.info("engine.compressing_context", current_tokens=context.total_tokens)
        
        # Selecionamos as primeiras mensagens (exceto a de sistema) para comprimir
        # Deixamos as últimas 4 mensagens intactas para manter a fluidez imediata
        messages_to_compress = context.messages[:-4]
        if len(messages_to_compress) < 2:
            return

        text_to_summarize = "\n".join([f"{m.role}: {m.content}" for m in messages_to_compress])
        
        try:
            summary = await self.llm_client.create_message(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                system=COMPRESSION_PROMPT,
                messages=[{"role": "user", "content": text_to_summarize}]
            )
            context.compress(summary, len(messages_to_compress))
        except Exception as e:
            logger.error("engine.compression_failed", error=str(e))
