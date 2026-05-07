"""
tests/plugins/test_manager.py

Testes unitários para o PluginManager.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from aegis.plugins.manager import PluginManager
from aegis.plugins.base import PluginManifest


@pytest.fixture
def manager(tmp_path) -> PluginManager:
    # Criamos um diretorio temporario para os plugins
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    return PluginManager(plugins_dir=str(plugins_dir))


@pytest.mark.asyncio
class TestPluginManager:
    async def test_initialization(self, manager):
        assert manager.plugins_dir.exists()
        assert manager.loaded_plugins == {}

    async def test_load_plugin_success(self, manager, tmp_path):
        # Criar estrutura de plugin fake
        plugin_id = "test-plugin"
        plugin_dir = Path(manager.plugins_dir) / plugin_id
        plugin_dir.mkdir()
        
        manifest_content = {
            "id": plugin_id,
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "Test",
            "author": "Tester",
            "entry_point": "TestPlugin"
        }
        
        with open(plugin_dir / "manifest.json", "w") as f:
            import json
            json.dump(manifest_content, f)
            
        with open(plugin_dir / "plugin.py", "w") as f:
            f.write("""
from aegis.plugins.base import BasePlugin
import structlog
logger = structlog.get_logger()

class TestPlugin(BasePlugin):
    async def on_load(self):
        logger.info("loaded")
    async def on_unload(self):
        logger.info("unloaded")
""")

        success = await manager.load_plugin(plugin_dir)
        assert success is True
        assert plugin_id in manager.loaded_plugins
        assert manager.loaded_plugins[plugin_id].manifest.name == "Test Plugin"

    async def test_unload_plugin(self, manager):
        # Mock de um plugin carregado
        mock_plugin = MagicMock()
        mock_plugin.on_unload = AsyncMock()
        plugin_id = "mock-plugin"
        manager.loaded_plugins[plugin_id] = mock_plugin
        
        success = await manager.unload_plugin(plugin_id)
        assert success is True
        assert plugin_id not in manager.loaded_plugins

    async def test_load_plugin_missing_manifest(self, manager):
        plugin_dir = Path(manager.plugins_dir) / "no-manifest"
        plugin_dir.mkdir()
        
        success = await manager.load_plugin(plugin_dir)
        assert success is False
