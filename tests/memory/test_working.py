"""
tests/memory/test_working.py

Testes unitários para a WorkingMemory com Redis mockado.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch
from aegis.memory.working import WorkingMemory

@pytest.fixture
def mock_settings():
    with patch("aegis.memory.working.get_settings") as mock:
        mock_settings = AsyncMock()
        mock_settings.REDIS_URL = "redis://localhost:6379"
        mock_settings.REDIS_SESSION_TTL = 86400
        mock.return_value = mock_settings
        yield mock_settings

@pytest.fixture
def session_id():
    return "test-session-123"

@pytest.fixture
def working_memory(session_id, mock_settings):
    return WorkingMemory(session_id=session_id)

@pytest.mark.asyncio
class TestWorkingMemory:
    async def test_save_message_calls_redis(self, working_memory, session_id):
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client
            
            await working_memory.save_message("user", "Olá AEGIS")
            
            key = f"aegis:session:{session_id}:history"
            # Verifica rpush
            mock_client.rpush.assert_called_once()
            args, _ = mock_client.rpush.call_args
            assert args[0] == key
            message = json.loads(args[1])
            assert message["role"] == "user"
            assert message["content"] == "Olá AEGIS"
            
            # Verifica expire
            mock_client.expire.assert_called_once_with(key, working_memory.ttl)

    async def test_get_history_returns_parsed_messages(self, working_memory, session_id):
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client
            
            mock_data = [
                json.dumps({"role": "user", "content": "Oi"}),
                json.dumps({"role": "assistant", "content": "Olá!"})
            ]
            mock_client.lrange.return_value = mock_data
            
            history = await working_memory.get_history(n=5)
            
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert history[1]["content"] == "Olá!"
            mock_client.lrange.assert_called_once_with(f"aegis:session:{session_id}:history", -5, -1)

    async def test_clear_session_deletes_key(self, working_memory, session_id):
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client
            
            await working_memory.clear_session()
            
            mock_client.delete.assert_called_once_with(f"aegis:session:{session_id}:history")

    async def test_close_closes_connection(self, working_memory):
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client
            
            # Trigger lazy client creation
            await working_memory._get_client()
            await working_memory.close()
            
            mock_client.close.assert_called_once()
            assert working_memory.redis is None
