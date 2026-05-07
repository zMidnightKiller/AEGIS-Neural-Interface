"""
aegis/plugins/base.py

Classes base para o sistema de plugins do AEGIS.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    """Manifesto que define metadados e comportamento do plugin."""
    id: str = Field(..., description="ID ǧnico do plugin (ex: aegis-weather)")
    name: str = Field(..., description="Nome legvel do plugin")
    version: str = Field(..., description="Versǜo (semver)")
    description: str = Field(..., description="Descriǜo breve")
    author: str = Field(..., description="Autor do plugin")
    entry_point: str = Field(..., description="Nome da classe principal no mdulo")


class BasePlugin(ABC):
    """
    Classe base que todos os plugins devem estender.
    """
    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest

    @abstractmethod
    async def on_load(self) -> None:
        """Chamado quando o plugin Ǹ carregado."""
        pass

    @abstractmethod
    async def on_unload(self) -> None:
        """Chamado quando o plugin Ǹ descarregado."""
        pass
