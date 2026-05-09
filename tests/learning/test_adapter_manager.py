import pytest
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from aegis.learning.adapter_manager import AdapterManager

@pytest.fixture
def temp_checkpoints_dir(tmp_path):
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    return checkpoint_dir

@pytest.fixture
def mock_settings(temp_checkpoints_dir):
    from aegis.core.config import get_settings
    get_settings.cache_clear()
    with patch("aegis.core.config.get_settings") as mock:
        settings = MagicMock()
        settings.AEGIS_CHECKPOINTS_DIR = str(temp_checkpoints_dir)
        settings.AEGIS_DATA_DIR = str(temp_checkpoints_dir.parent) # dummy
        mock.return_value = settings
        yield settings
    get_settings.cache_clear()

class TestAdapterManager:
    @pytest.mark.asyncio
    async def test_list_adapters_empty(self, mock_settings):
        manager = AdapterManager()
        await manager.initialize()
        assert manager.list_adapters() == []

    @pytest.mark.asyncio
    async def test_register_and_list(self, mock_settings, temp_checkpoints_dir):
        manager = AdapterManager()
        await manager.initialize()
        adapter_path = temp_checkpoints_dir / "adapter_1"
        adapter_path.mkdir()
        
        metadata = {
            "date": "2026-05-09",
            "samples": 30,
            "metrics": {"quality": 0.8},
            "base_model": "mistral-7b"
        }
        
        await manager.register_adapter("adapter_1", metadata)
        
        adapters = manager.list_adapters()
        assert len(adapters) == 1
        assert adapters[0]["id"] == "adapter_1"
        assert adapters[0]["metadata"]["samples"] == 30

    @pytest.mark.asyncio
    async def test_rollback(self, mock_settings, temp_checkpoints_dir):
        manager = AdapterManager()
        await manager.initialize()
        
        # Create two adapters
        (temp_checkpoints_dir / "adapter_1").mkdir()
        await manager.register_adapter("adapter_1", {"date": "2026-01-01"})
        
        (temp_checkpoints_dir / "adapter_2").mkdir()
        await manager.register_adapter("adapter_2", {"date": "2026-01-02"})
        
        # Set active (simulated by the fact that adapter_2 is the latest)
        assert manager.get_active_id() == "adapter_2"
        
        # Rollback
        await manager.rollback(n=1)
        assert manager.get_active_id() == "adapter_1"

    @pytest.mark.asyncio
    async def test_retention_policy(self, mock_settings, temp_checkpoints_dir):
        manager = AdapterManager()
        await manager.initialize()
        # Max 5 adapters in PRD
        for i in range(7):
            adapter_id = f"adapter_{i}"
            (temp_checkpoints_dir / adapter_id).mkdir()
            await manager.register_adapter(adapter_id, {"date": f"2026-01-0{i}"})
            
        adapters = manager.list_adapters()
        assert len(adapters) == 5
        # The oldest (0 and 1) should be gone
        assert "adapter_0" not in [a["id"] for a in adapters]
        assert "adapter_1" not in [a["id"] for a in adapters]
        assert "adapter_6" in [a["id"] for a in adapters]
