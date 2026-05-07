"""
aegis/tools/calendar.py

Ferramenta para gerenciamento de calendario (Google Calendar).
Permite listar eventos, criar agendamentos e remover compromissos.
"""
from __future__ import annotations

import structlog
from typing import Any, Optional

from aegis.core.config import get_settings
from aegis.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)


class CalendarTool(BaseTool):
    """Gerencia eventos no Google Calendar."""

    name: str = "calendar"
    description: str = (
        "Gerencia eventos no calendario. Pode listar compromissos, criar novos eventos ou deleta-los. "
        "Use para organizar a agenda do usuario."
    )
    parameters: dict[str, Any] = {
        "action": "Acao a realizar: 'list', 'create', 'delete'.",
        "summary": "Titulo do evento (para 'create').",
        "start_time": "Data/hora de inicio em formato ISO (para 'create').",
        "end_time": "Data/hora de termino em formato ISO (para 'create').",
        "event_id": "ID do evento (para 'delete').",
        "time_min": "Inicio do periodo de busca (para 'list'). Opcional.",
        "time_max": "Fim do periodo de busca (para 'list'). Opcional."
    }

    async def execute(self, action: str, **kwargs) -> ToolResult:
        """
        Executa uma acao no calendario.
        """
        logger.info("calendar.executing", action=action, params=kwargs)

        if action == "list":
            return await self._list_events(kwargs.get("time_min"), kwargs.get("time_max"))
        elif action == "create":
            return await self._create_event(
                kwargs.get("summary"), 
                kwargs.get("start_time"), 
                kwargs.get("end_time")
            )
        elif action == "delete":
            return await self._delete_event(kwargs.get("event_id"))
        else:
            return ToolResult(success=False, error=f"Acao desconhecida: {action}", metadata={})

    async def _list_events(self, time_min: Optional[str] = None, time_max: Optional[str] = None) -> ToolResult:
        # Placeholder: Retorna lista vazia ou mock se em teste
        logger.info("calendar.listing_events")
        # Mock de evento para demonstracao
        mock_events = [
            {
                "id": "mock_1",
                "summary": "Reuniao de Alinhamento AEGIS",
                "start": {"dateTime": "2026-05-06T10:00:00Z"},
                "end": {"dateTime": "2026-05-06T11:00:00Z"}
            }
        ]
        return ToolResult(
            success=True, 
            data=mock_events, 
            metadata={"count": len(mock_events), "action": "list"}
        )

    async def _create_event(self, summary: str | None, start: str | None, end: str | None) -> ToolResult:
        if not summary or not start:
            return ToolResult(success=False, error="Summary e start_time sao obrigatorios.", metadata={})
        
        logger.info("calendar.creating_event", summary=summary, start=start)
        # Mock de criacao
        return ToolResult(
            success=True, 
            data={"id": "new_event_id", "summary": summary, "status": "confirmed"},
            metadata={"action": "create"}
        )

    async def _delete_event(self, event_id: str | None) -> ToolResult:
        if not event_id:
            return ToolResult(success=False, error="event_id eh obrigatorio para deletar.", metadata={})
            
        logger.info("calendar.deleting_event", event_id=event_id)
        return ToolResult(success=True, data={"status": "deleted"}, metadata={"id": event_id, "action": "delete"})
