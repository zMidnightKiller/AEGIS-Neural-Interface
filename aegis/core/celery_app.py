"""
aegis/core/celery_app.py

Configuracao central do Celery para processamento de tarefas em background.
Utiliza Redis como broker e backend de resultados.
"""
from __future__ import annotations

import structlog
from celery import Celery

from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Cria a instancia do Celery
celery_app = Celery(
    "aegis",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["aegis.core.tasks"]
)

# Configuracoes adicionais
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutos maximo
)

logger.info("celery.initialized", broker=settings.REDIS_URL)

if __name__ == "__main__":
    celery_app.start()
