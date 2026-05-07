"""
tests/core/test_security.py

Testes unitarios para o sistema de seguranca do AEGIS.
"""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from aegis.core.security import AuditLogger, SecurityManager

@pytest.fixture
def temp_audit_log(tmp_path):
    log_file = tmp_path / "audit.log"
    return str(log_file)

@pytest.fixture
def audit_logger(temp_audit_log):
    return AuditLogger(log_path=temp_audit_log)

@pytest.fixture
def security_manager(audit_logger):
    return SecurityManager(audit_logger=audit_logger)

class TestAuditLogger:
    def test_log_action_creates_file(self, audit_logger, temp_audit_log):
        audit_logger.log_action("user123", "test_action", {"key": "value"})
        assert os.path.exists(temp_audit_log)
        
        with open(temp_audit_log, "r") as f:
            line = f.readline()
            entry = json.loads(line)
            assert entry["user_id"] == "user123"
            assert entry["action"] == "test_action"
            assert entry["details"] == {"key": "value"}

    def test_log_action_sanitizes_sensitive_data(self, audit_logger, temp_audit_log):
        audit_logger.log_action("user123", "login", {"password": "secret_password", "token": "abc-123"})
        
        with open(temp_audit_log, "r") as f:
            line = f.readline()
            entry = json.loads(line)
            assert entry["details"]["password"] == "********"
            assert entry["details"]["token"] == "********"

@pytest.mark.asyncio
class TestSecurityManager:
    async def test_verify_and_execute_normal_action(self, security_manager):
        mock_func = AsyncMock(return_value="success")
        result = await security_manager.verify_and_execute(
            "user1", "normal_action", {"param": 1}, mock_func
        )
        assert result == "success"
        mock_func.assert_called_once_with(param=1)

    async def test_verify_and_execute_irreversible_action_blocked(self, security_manager):
        mock_func = AsyncMock()
        with pytest.raises(PermissionError) as excinfo:
            await security_manager.verify_and_execute(
                "user1", "delete_file", {"path": "/tmp/test"}, mock_func
            )
        assert "bloqueada" in str(excinfo.value)
        mock_func.assert_not_called()

    async def test_verify_and_execute_irreversible_action_approved(self, security_manager):
        mock_func = AsyncMock(return_value="deleted")
        result = await security_manager.verify_and_execute(
            "user1", "delete_file", {"path": "/tmp/test", "approved": True}, mock_func
        )
        assert result == "deleted"
        mock_func.assert_called_once()
