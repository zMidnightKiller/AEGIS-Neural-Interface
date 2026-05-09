import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from aegis.interfaces.api import app
from aegis.core.resource_guard import ResourceStatus

@pytest.fixture
def mock_guard():
    with patch("aegis.core.resource_guard.ResourceGuard.get_instance") as mock:
        guard = MagicMock()
        status = ResourceStatus(
            vram_used_gb=5.0,
            vram_total_gb=12.0,
            vram_pct=41.6,
            gpu_pct=15.0,
            gpu_temp_c=55.0,
            cpu_pct=20.0,
            ram_used_gb=10.0,
            ram_total_gb=32.0,
            level="SAFE",
            paused_ops=[]
        )
        guard.check = AsyncMock(return_value=status)
        mock.return_value = guard
        yield guard

@pytest.fixture
def mock_engine():
    with patch("aegis.interfaces.api.get_engine") as mock:
        engine = MagicMock()
        engine.process = AsyncMock()
        mock.return_value = engine
        yield engine

@pytest.mark.asyncio
async def test_get_mode():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/mode")
    assert response.status_code == 200
    assert "mode" in response.json()

@pytest.mark.asyncio
async def test_get_model_status(mock_guard):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/model/status")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "vram_status" in data
    assert data["vram_status"]["level"] == "SAFE"

@pytest.mark.asyncio
@patch("aegis.learning.collector.TrainingDataCollector.get_stats", new_callable=AsyncMock)
async def test_get_learning_status(mock_stats):
    mock_stats.return_value = {"count": 10, "avg_quality": 0.85}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/learning/status")
    assert response.status_code == 200
    data = response.json()
    assert data["samples_collected"] == 10
    assert data["average_quality"] == 0.85

@pytest.mark.asyncio
async def test_memory_search(mock_engine):
    mock_memory_agent = MagicMock()
    mock_memory_agent.episodic.search_similar = AsyncMock(return_value=[{"id": "1", "content": "test result"}])
    mock_engine.agents = {"memory": mock_memory_agent}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/memory/search?query=test")
    
    assert response.status_code == 200
    assert response.json()["query"] == "test"
    assert len(response.json()["results"]) == 1

@pytest.mark.asyncio
async def test_get_session_history():
    with patch("aegis.memory.working.WorkingMemory.get_history", new_callable=AsyncMock) as mock_hist:
        mock_hist.return_value = [{"role": "user", "content": "hello"}]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/sessions/test_session")
        assert response.status_code == 200
        assert response.json()["session_id"] == "test_session"
        assert len(response.json()["history"]) == 1
