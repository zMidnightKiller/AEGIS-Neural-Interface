"""
aegis/core/tasks.py

Definicao de tarefas assincronas para o Celery.
"""
from __future__ import annotations

import asyncio
import structlog
from typing import Any

from aegis.core.celery_app import celery_app
from aegis.core.engine import Engine
from aegis.core.models import UserInput, OperatingMode

logger = structlog.get_logger(__name__)

@celery_app.task(name="aegis.core.tasks.process_agent_task")
def process_agent_task(text: str, session_id: str, mode: str) -> dict[str, Any]:
    """
    Tarefa para processar uma solicitacao do usuario de forma assincrona.
    Util para processos longos disparados via API.
    """
    logger.info("tasks.process_agent_task.started", session_id=session_id)
    
    # Como o motor e async, precisamos rodar o loop de eventos
    try:
        engine = Engine()
        user_input = UserInput(
            text=text,
            session_id=session_id,
            mode=OperatingMode(mode)
        )
        
        # Executa o processamento sincronicamente dentro da tarefa Celery
        # Nota: Celery por padrao e sincrono, mas estamos chamando codigo async
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(engine.process(user_input))
        
        logger.info("tasks.process_agent_task.completed", session_id=session_id)
        
        return {
            "success": True,
            "text": response.text,
            "agent_used": response.agent_used,
            "tools_used": response.tools_used,
            "latency_ms": response.latency_ms
        }
    except Exception as e:
        logger.error("tasks.process_agent_task.failed", error=str(e), session_id=session_id)
        return {
            "success": False,
            "error": str(e)
        }

@celery_app.task(name="aegis.core.tasks.health_check_task")
def health_check_task() -> str:
    """Tarefa simples de integridade para testar a fila."""
    return "Celery is working!"
