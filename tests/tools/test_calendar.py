import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aegis.tools.calendar import CalendarTool

@pytest.fixture
def tool():
    return CalendarTool()

@pytest.mark.asyncio
async def test_calendar_list(tool):
    result = await tool.execute(action="list")
    assert result.success is True
    assert len(result.data) > 0
    assert result.data[0]["summary"] == "Reuniao de Alinhamento AEGIS"

@pytest.mark.asyncio
async def test_calendar_create(tool):
    result = await tool.execute(
        action="create", 
        summary="Nova Tarefa", 
        start_time="2026-05-06T15:00:00Z"
    )
    assert result.success is True
    assert result.data["summary"] == "Nova Tarefa"

@pytest.mark.asyncio
async def test_calendar_delete(tool):
    result = await tool.execute(action="delete", event_id="mock_1")
    assert result.success is True
    assert result.data["status"] == "deleted"

@pytest.mark.asyncio
async def test_calendar_invalid_action(tool):
    result = await tool.execute(action="invalid")
    assert result.success is False
    assert "desconhecida" in result.error
