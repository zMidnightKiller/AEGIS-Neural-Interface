"""
aegis/core/orchestrator.py

Componente de orquestracao avancada para o sistema AEGIS.
Implementa execucao paralela de agentes e o padrao Circuit Breaker para resiliencia.
"""
from __future__ import annotations

import asyncio
import time
import structlog
from enum import Enum
from typing import Any, Callable, Coroutine, TypeVar, Generic

from aegis.agents.base import BaseAgent, AgentResult
from aegis.core.context import Context

logger = structlog.get_logger(__name__)

T = TypeVar("T")

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    """
    Implementa o padrao Circuit Breaker para proteger chamadas a agentes ou ferramentas externas.
    """
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED

    async def call(self, func: Callable[..., Coroutine[Any, Any, T]], *args: Any, **kwargs: Any) -> T:
        """Executa a funcao protegida pelo circuit breaker."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info("circuit_breaker.transition", name=self.name, from_state="OPEN", to_state="HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
            else:
                logger.warning("circuit_breaker.blocked", name=self.name, state="OPEN")
                raise RuntimeError(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = await func(*args, **kwargs)
            
            # Se chegamos aqui, a chamada teve sucesso
            if self.state == CircuitState.HALF_OPEN:
                logger.info("circuit_breaker.transition", name=self.name, from_state="HALF_OPEN", to_state="CLOSED")
                self.state = CircuitState.CLOSED
                self.failures = 0
            
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.state != CircuitState.OPEN and self.failures >= self.failure_threshold:
                logger.error("circuit_breaker.transition", name=self.name, from_state=self.state.value, to_state="OPEN", error=str(e))
                self.state = CircuitState.OPEN
            
            raise e

class MultiAgentOrchestrator:
    """
    Orquestrador que gerencia a execucao paralela de múltiplos agentes.
    """
    def __init__(self, max_concurrency: int = 5):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.semaphore = asyncio.Semaphore(max_concurrency)

    def _get_breaker(self, agent_name: str) -> CircuitBreaker:
        if agent_name not in self.circuit_breakers:
            self.circuit_breakers[agent_name] = CircuitBreaker(name=agent_name)
        return self.circuit_breakers[agent_name]

    async def _run_with_semaphore(
        self, 
        breaker: CircuitBreaker, 
        func: Callable[..., Coroutine[Any, Any, T]], 
        *args: Any, 
        **kwargs: Any
    ) -> T:
        """
        Executa uma funcao protegida por semaforo e circuit breaker.
        """
        async with self.semaphore:
            return await breaker.call(func, *args, **kwargs)

    async def run_parallel(
        self, 
        agent_tasks: list[tuple[BaseAgent, str, Context]],
        timeout: float = 60.0
    ) -> list[AgentResult | Exception]:
        """
        Executa multiplos agentes em paralelo, cada um protegido por seu proprio circuit breaker.
        O numero de execucoes simultaneas e limitado pelo semaforo.
        
        Args:
            agent_tasks: Lista de tuplas contendo (Agente, Tarefa, Contexto).
            timeout: Tempo maximo em segundos para a conclusao do lote.
            
        Returns:
            Lista de AgentResult ou Exception.
        """
        tasks = []
        for agent, task, context in agent_tasks:
            breaker = self._get_breaker(agent.name)
            tasks.append(self._run_with_semaphore(breaker, agent.run, task, context))
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error("orchestrator.parallel_timeout", timeout=timeout)
            return [asyncio.TimeoutError(f"Timeout de {timeout}s atingido")] * len(agent_tasks)
        
        final_results: list[AgentResult | Exception] = []
        for i, res in enumerate(results):
            agent_name = agent_tasks[i][0].name
            if isinstance(res, Exception):
                logger.error("orchestrator.agent_failed", agent=agent_name, error=str(res))
                final_results.append(res)
            else:
                final_results.append(res)
        
        return final_results
