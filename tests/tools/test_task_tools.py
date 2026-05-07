"""
tests/tools/test_task_tools.py

Testes unitários para CalendarTool e EmailTool.
"""
import pytest
from unittest.mock import patch, MagicMock
from aegis.tools.calendar import CalendarTool
from aegis.tools.email import EmailTool

class TestCalendarTool:
    @pytest.mark.asyncio
    async def test_calendar_list(self):
        tool = CalendarTool()
        result = await tool.execute(action="list")
        assert result.success is True
        assert isinstance(result.data, list)
        assert result.metadata["action"] == "list"

    @pytest.mark.asyncio
    async def test_calendar_create(self):
        tool = CalendarTool()
        result = await tool.execute(
            action="create", 
            summary="Teste", 
            start_time="2026-05-06T10:00:00Z"
        )
        assert result.success is True
        assert result.data["summary"] == "Teste"

    @pytest.mark.asyncio
    async def test_calendar_delete(self):
        tool = CalendarTool()
        result = await tool.execute(action="delete", event_id="123")
        assert result.success is True
        assert result.data["status"] == "deleted"

class TestEmailTool:
    @pytest.mark.asyncio
    async def test_email_simulation(self):
        # Sem credenciais no config, deve simular
        with patch("aegis.tools.email.get_settings") as mock_settings:
            mock_settings.return_value.EMAIL_SENDER = None
            tool = EmailTool()
            result = await tool.execute(to="test@example.com", subject="Oi", body="Teste")
            assert result.success is True
            assert result.data["status"] == "simulated"

    @pytest.mark.asyncio
    async def test_email_send_success(self):
        # Mocking smtplib
        with patch("aegis.tools.email.get_settings") as mock_settings, \
             patch("smtplib.SMTP") as mock_smtp:
            
            mock_settings.return_value.EMAIL_SENDER = "sender@test.com"
            mock_settings.return_value.EMAIL_PASSWORD.get_secret_value.return_value = "pass"
            mock_settings.return_value.SMTP_SERVER = "smtp.test.com"
            mock_settings.return_value.SMTP_PORT = 587
            
            tool = EmailTool()
            result = await tool.execute(to="dest@test.com", subject="Sub", body="Body")
            
            assert result.success is True
            assert result.data["status"] == "sent"
            assert mock_smtp.called
