"""
aegis/core/events.py

Sistema de eventos assincronos para comunicacao em tempo real entre componentes.
Utilizado principalmente para alimentar a Interface Galactica.
"""
from __future__ import annotations

import asyncio
import structlog
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Set

logger = structlog.get_logger(__name__)

@dataclass
class AegisEvent:
    """Representa um evento disparado pelo sistema."""
    type: str
    data: Dict[str, Any]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class EventBus:
    """
    Bus de eventos assincrono (Pub/Sub).
    Permite que multiplos componentes se inscrevam para receber eventos.
    """

    def __init__(self):
        self._subscribers: Set[Callable[[AegisEvent], asyncio.Task | Any]] = set()

    def subscribe(self, callback: Callable[[AegisEvent], asyncio.Task | Any]):
        """Inscreve um callback para receber eventos."""
        self._subscribers.add(callback)
        logger.debug("event_bus.subscribed", total_subscribers=len(self._subscribers))

    def unsubscribe(self, callback: Callable[[AegisEvent], asyncio.Task | Any]):
        """Remove a inscricao de um callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.debug("event_bus.unsubscribed", total_subscribers=len(self._subscribers))

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Dispara um evento para todos os inscritos."""
        import time
        event = AegisEvent(type=event_type, data=data, timestamp=time.time())
        
        if not self._subscribers:
            return

        tasks = []
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(event))
                else:
                    callback(event)
            except Exception as e:
                logger.error("event_bus.emit_error", error=str(e), subscriber=str(callback))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Singleton Global
event_bus = EventBus()
