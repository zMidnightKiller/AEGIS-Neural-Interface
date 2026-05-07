"""
aegis/memory/working.py

Memória de trabalho (Working Memory) utilizando Redis para armazenamento de curto prazo.
Mantém o histórico da sessão ativa e expira após um TTL configurado.
"""
from __future__ import annotations

import json
from typing import Any, List, Optional

import redis.asyncio as redis
import structlog

from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)


class WorkingMemory:
    """
    Gere o histórico de mensagens de uma sessão no Redis.
    """

    def __init__(self, session_id: str, redis_url: Optional[str] = None):
        self.session_id = session_id
        self.settings = get_settings()
        self.redis_url = redis_url or self.settings.REDIS_URL
        self.redis: Optional[redis.Redis] = None
        self.ttl = self.settings.REDIS_SESSION_TTL

    async def _get_client(self) -> redis.Redis:
        """Retorna o cliente Redis, inicializando-o se necessário."""
        if self.redis is None:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis

    async def save_message(self, role: str, content: str, metadata: Optional[dict] = None) -> None:
        """
        Salva uma nova mensagem no histórico da sessão.

        Args:
            role: O papel da mensagem (ex: "user", "assistant", "system").
            content: O conteúdo textual da mensagem.
            metadata: Metadados adicionais opcionais.
        """
        client = await self._get_client()
        message = {
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        key = f"aegis:session:{self.session_id}:history"
        
        try:
            await client.rpush(key, json.dumps(message))
            await client.expire(key, self.ttl)
            logger.info("working_memory.message_saved", session_id=self.session_id, role=role)
        except Exception as e:
            logger.error("working_memory.save_failed", session_id=self.session_id, error=str(e))
            raise

    async def get_history(self, n: int = 10) -> List[dict[str, Any]]:
        """
        Retorna as últimas n mensagens do histórico.

        Args:
            n: Número de mensagens a recuperar.

        Returns:
            Lista de dicionários representando as mensagens.
        """
        client = await self._get_client()
        key = f"aegis:session:{self.session_id}:history"
        
        try:
            raw_messages = await client.lrange(key, -n, -1)
            messages = [json.loads(m) for m in raw_messages]
            logger.info("working_memory.history_retrieved", session_id=self.session_id, count=len(messages))
            return messages
        except Exception as e:
            logger.error("working_memory.retrieval_failed", session_id=self.session_id, error=str(e))
            return []

    async def clear_session(self) -> None:
        """
        Remove todo o histórico da sessão atual.
        """
        client = await self._get_client()
        key = f"aegis:session:{self.session_id}:history"
        try:
            await client.delete(key)
            logger.info("working_memory.session_cleared", session_id=self.session_id)
        except Exception as e:
            logger.error("working_memory.clear_failed", session_id=self.session_id, error=str(e))

    def get_session_id(self) -> str:
        """Retorna o ID da sessão atual."""
        return self.session_id

    async def close(self) -> None:
        """Fecha a conexão com o Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
