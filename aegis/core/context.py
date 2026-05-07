"""
aegis/core/context.py

Gestǜo do contexto de conversaǜo (janela de mensagens).
"""
from __future__ import annotations

import structlog
from typing import Any
from aegis.core.models import Message
from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)


class Context:
    """
    MantǸm e gerencia a janela de mensagens da sessǜo.
    Garante que o limite de tokens seja respeitado atravǸs de truncamento.
    """

    def __init__(self, session_id: str, max_tokens: int | None = None):
        self.session_id = session_id
        self.messages: list[Message] = []
        self.metadata: dict[str, Any] = {}
        self.settings = get_settings()
        self.max_tokens = max_tokens or self.settings.CONTEXT_MAX_TOKENS

    @property
    def total_tokens(self) -> int:
        """Retorna o total estimado de tokens no contexto atual."""
        return sum(self._estimate_tokens(m.content) for m in self.messages)

    def add_message(self, role: str, content: str, metadata: dict | None = None) -> None:
        """Adiciona uma nova mensagem ao contexto."""
        msg = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        logger.debug("context.message_added", session_id=self.session_id, role=role)
        
        # O truncamento de segurana deve sempre ocorrer se exceder o limite crtico.
        self._truncate_if_needed()

    def compress(self, summary: str, num_messages: int) -> None:
        """
        Substitui as primeiras N mensagens por um resumo consolidado.
        
        Args:
            summary: O resumo das mensagens comprimidas.
            num_messages: Quantidade de mensagens a serem removidas (do incio).
        """
        if num_messages <= 0 or not self.messages:
            return

        # Preserva a mensagem de sistema se for a primeira
        system_msg = None
        if self.messages[0].role == "system":
            system_msg = self.messages.pop(0)
            num_messages -= 1

        # Remove as mensagens
        for _ in range(min(num_messages, len(self.messages))):
            self.messages.pop(0)

        # Insere o resumo como uma nota de sistema
        summary_msg = Message(
            role="system",
            content=f"[RESUMO DO CONTEXTO ANTERIOR]: {summary}",
            metadata={"compressed": True}
        )
        
        if system_msg:
            self.messages.insert(0, summary_msg)
            self.messages.insert(0, system_msg)
        else:
            self.messages.insert(0, summary_msg)
            
        logger.info(
            "context.compressed", 
            session_id=self.session_id, 
            messages_removed=num_messages,
            new_total_tokens=self.total_tokens
        )

    @property
    def attachments(self) -> list[str]:
        """Retorna os anexos da ǧltima mensagem do usuǭrio."""
        for msg in reversed(self.messages):
            if msg.role == "user" and "attachments" in msg.metadata:
                return msg.metadata["attachments"]
        return []

    def get_window(self) -> list[Message]:
        """Retorna a lista atual de mensagens na janela."""
        return self.messages

    def _estimate_tokens(self, text: str) -> int:
        """Estimativa simples de tokens: 4 caracteres por token."""
        return len(text) // 4

    def _truncate_if_needed(self) -> None:
        """Remove mensagens antigas se exceder o limite de tokens (fallback)."""
        if self.max_tokens is None:
            return

        current_tokens = self.total_tokens
        while current_tokens > self.max_tokens and len(self.messages) > 1:
            removed = self.messages.pop(0)
            current_tokens -= self._estimate_tokens(removed.content)
            logger.info(
                "context.message_truncated",
                session_id=self.session_id,
                removed_role=removed.role,
                current_total_tokens=current_tokens,
            )

    def serialize(self) -> dict[str, Any]:
        """Serializa o contexto para armazenamento."""
        return {
            "session_id": self.session_id,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "metadata": m.metadata,
                }
                for m in self.messages
            ],
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Context:
        """Cria uma instǽncia de Context a partir de dados serializados."""
        ctx = cls(session_id=data["session_id"], max_tokens=data.get("max_tokens"))
        for msg_data in data.get("messages", []):
            msg = Message(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=msg_data.get("timestamp", 0.0),
                metadata=msg_data.get("metadata", {}),
            )
            ctx.messages.append(msg)
        return ctx
