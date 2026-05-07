"""
aegis/core/observability.py

Componente de observabilidade do AEGIS.
Integra Langfuse para rastreamento de LLM e Prometheus para métricas.
"""
from __future__ import annotations

import structlog
from langfuse import Langfuse
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI

from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

class ObservabilityManager:
    """Gerencia a integração com ferramentas de observabilidade."""

    def __init__(self):
        self.langfuse = None
        if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
            try:
                self.langfuse = Langfuse(
                    public_key=settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=settings.LANGFUSE_SECRET_KEY.get_secret_value(),
                    host=settings.LANGFUSE_HOST
                )
                logger.info("observability.langfuse_initialized")
            except Exception as e:
                logger.error("observability.langfuse_init_failed", error=str(e))
        else:
            logger.info("observability.langfuse_disabled", reason="Missing API keys")

    def setup_fastapi(self, app: FastAPI):
        """Configura instrumentação do Prometheus na FastAPI."""
        if settings.ENABLE_PROMETHEUS:
            try:
                Instrumentator().instrument(app).expose(app, endpoint=settings.PROMETHEUS_ENDPOINT)
                logger.info("observability.prometheus_initialized", endpoint=settings.PROMETHEUS_ENDPOINT)
            except Exception as e:
                logger.error("observability.prometheus_init_failed", error=str(e))

    def trace_event(self, name: str, user_id: str, input_data: any, output_data: any = None, metadata: dict = None):
        """Registra um traço manual no Langfuse."""
        if self.langfuse:
            try:
                self.langfuse.trace(
                    name=name,
                    user_id=user_id,
                    input=input_data,
                    output=output_data,
                    metadata=metadata or {}
                )
            except Exception as e:
                logger.warning("observability.trace_failed", error=str(e))

# Singleton
obs_manager = ObservabilityManager()
