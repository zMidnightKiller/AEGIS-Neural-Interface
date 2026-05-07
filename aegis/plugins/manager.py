"""
aegis/plugins/manager.py

Gerenciador de plugins do AEGIS.
Responsǭvel por carregar, descarregar e gerenciar o ciclo de vida dos plugins.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Dict, Type

import structlog

from aegis.plugins.base import BasePlugin, PluginManifest

logger = structlog.get_logger(__name__)


class PluginManager:
    """
    Sistema de gestǜo de extenses do AEGIS.
    """

    def __init__(self, plugins_dir: str = "data/plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self._module_cache: Dict[str, Any] = {}

    async def load_all(self) -> None:
        """Carrega todos os plugins encontrados no diretrio."""
        logger.info("plugin_manager.loading_all", directory=str(self.plugins_dir))
        
        for plugin_folder in self.plugins_dir.iterdir():
            if plugin_folder.is_dir():
                await self.load_plugin(plugin_folder)

    async def load_plugin(self, plugin_path: Path) -> bool:
        """
        Carrega um plugin individual.
        
        O plugin deve conter um arquivo manifest.json e um entry point Python.
        """
        manifest_path = plugin_path / "manifest.json"
        if not manifest_path.exists():
            logger.warning("plugin_manager.manifest_missing", path=str(plugin_path))
            return False

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
                manifest = PluginManifest(**manifest_data)

            # Importa o mdulo dinamicamente
            module_name = f"aegis_plugins.{manifest.id}"
            entry_file = plugin_path / "plugin.py"
            
            if not entry_file.exists():
                logger.error("plugin_manager.entry_point_missing", path=str(entry_file))
                return False

            spec = importlib.util.spec_from_file_location(module_name, str(entry_file))
            if spec is None or spec.loader is None:
                return False
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Instancia a classe do plugin
            plugin_class: Type[BasePlugin] = getattr(module, manifest.entry_point)
            plugin_instance = plugin_class(manifest)
            
            # Inicializa
            await plugin_instance.on_load()
            
            self.loaded_plugins[manifest.id] = plugin_instance
            logger.info("plugin_manager.loaded", plugin_id=manifest.id, version=manifest.version)
            return True

        except Exception as e:
            logger.error("plugin_manager.load_failed", path=str(plugin_path), error=str(e))
            return False

    async def unload_plugin(self, plugin_id: str) -> bool:
        """Descarrega um plugin."""
        if plugin_id not in self.loaded_plugins:
            return False

        try:
            plugin = self.loaded_plugins[plugin_id]
            await plugin.on_unload()
            del self.loaded_plugins[plugin_id]
            
            # Remove do sys.modules para permitir recarregamento limpo
            module_name = f"aegis_plugins.{plugin_id}"
            if module_name in sys.modules:
                del sys.modules[module_name]
                
            logger.info("plugin_manager.unloaded", plugin_id=plugin_id)
            return True
        except Exception as e:
            logger.error("plugin_manager.unload_failed", plugin_id=plugin_id, error=str(e))
            return False

    async def reload_plugin(self, plugin_id: str) -> bool:
        """Executa hot-reload de um plugin."""
        logger.info("plugin_manager.reloading", plugin_id=plugin_id)
        
        # Encontra o caminho do plugin (pode ser melhorado salvando no init)
        plugin_path = self.plugins_dir / plugin_id
        
        await self.unload_plugin(plugin_id)
        return await self.load_plugin(plugin_path)
