"""
aegis/learning/adapter_manager.py

Gestão de LoRA Adapters & Versionamento.
Gerencia o registro, rollback e retenção de adapters treinados localmente na RTX 3060.
"""
from __future__ import annotations

import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import structlog

from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)

class AdapterManager:
    """
    Registry de adapters com metadata e controle de versão.
    Mantém os últimos N adapters para economizar espaço em disco na 3060.
    """

    def __init__(self):
        from aegis.core.config import get_settings
        self.settings = get_settings()
        self.checkpoints_dir = Path(self.settings.AEGIS_CHECKPOINTS_DIR)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.checkpoints_dir / "registry.json"
        self.adapters: List[Dict[str, Any]] = []
        self.active_id: Optional[str] = None
        self._initialized = False

    async def initialize(self):
        """Inicializa o manager carregando o registro."""
        if not self._initialized:
            await self._load_registry()
            self._initialized = True

    async def _load_registry(self):
        """Carrega o registro de adapters do disco."""
        if not self.registry_path.exists():
            self.adapters = []
            self.active_id = None
            return

        def _read():
            with open(self.registry_path, "r", encoding="utf-8") as f:
                return json.load(f)

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, _read)
            self.adapters = data.get("adapters", [])
            self.active_id = data.get("active_id")
        except Exception as e:
            logger.error("adapter_manager.load_failed", error=str(e))
            self.adapters = []
            self.active_id = None

    async def _save_registry(self):
        """Salva o registro de adapters no disco."""
        def _write():
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump({
                    "adapters": self.adapters,
                    "active_id": self.active_id,
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _write)
        except Exception as e:
            logger.error("adapter_manager.save_failed", error=str(e))

    async def register_adapter(self, adapter_id: str, metadata: Dict[str, Any]):
        """
        Registra um novo adapter e aplica a política de retenção.
        """
        adapter_path = self.checkpoints_dir / adapter_id
        
        entry = {
            "id": adapter_id,
            "path": str(adapter_path),
            "metadata": metadata,
            "registered_at": datetime.now().isoformat()
        }
        
        self.adapters = [a for a in self.adapters if a["id"] != adapter_id]
        self.adapters.append(entry)
        self.active_id = adapter_id
        
        await self._apply_retention()
        await self._save_registry()
        logger.info("adapter_manager.registered", adapter_id=adapter_id)

    async def _apply_retention(self, max_adapters: int = 5):
        """Remove adapters antigos para economizar espaço na RTX 3060."""
        if len(self.adapters) <= max_adapters:
            return

        to_remove = self.adapters[:-max_adapters]
        self.adapters = self.adapters[-max_adapters:]
        
        loop = asyncio.get_event_loop()
        for adapter in to_remove:
            path = Path(adapter["path"])
            if path.exists() and path.is_dir():
                try:
                    await loop.run_in_executor(None, shutil.rmtree, path)
                    logger.info("adapter_manager.retention.removed_files", adapter_id=adapter["id"])
                except Exception as e:
                    logger.error("adapter_manager.retention.error", adapter_id=adapter["id"], error=str(e))
            
            if self.active_id == adapter["id"]:
                self.active_id = self.adapters[-1]["id"] if self.adapters else None

    async def rollback(self, n: int = 1):
        """
        Reverte para o n-ésimo adapter anterior.
        """
        if not self.adapters or len(self.adapters) <= n:
            logger.warning("adapter_manager.rollback.failed.not_enough_history")
            return

        current_idx = -1
        for i, a in enumerate(self.adapters):
            if a["id"] == self.active_id:
                current_idx = i
                break
        
        if current_idx == -1:
            current_idx = len(self.adapters) - 1

        new_idx = max(0, current_idx - n)
        self.active_id = self.adapters[new_idx]["id"]
        await self._save_registry()
        logger.info("adapter_manager.rollback.success", new_active=self.active_id)

    def list_adapters(self) -> List[Dict[str, Any]]:
        """Retorna a lista de adapters registrados."""
        return self.adapters

    def get_active_id(self) -> Optional[str]:
        """Retorna o ID do adapter ativo."""
        return self.active_id

    def get_adapter_path(self, adapter_id: str) -> Optional[str]:
        """Retorna o path de um adapter específico."""
        for a in self.adapters:
            if a["id"] == adapter_id:
                return a["path"]
        return None

    def compare(self, id_a: str, id_b: str) -> Dict[str, Any]:
        """
        Compara métricas de dois adapters.
        (Heurística simples para o MVP)
        """
        meta_a = next((a["metadata"] for a in self.adapters if a["id"] == id_a), {})
        meta_b = next((a["metadata"] for a in self.adapters if a["id"] == id_b), {})
        
        return {
            "adapter_a": {"id": id_a, "metadata": meta_a},
            "adapter_b": {"id": id_b, "metadata": meta_b},
            "diff": "Comparação de métricas via Evaluator recomendada."
        }

    def export_merged(self, adapter_id: str, output_path: str):
        """
        Prepara o merge do adapter (implementação real dependeria de Unsloth/Transformers).
        No MVP, apenas loga a intenção.
        """
        path = self.get_adapter_path(adapter_id)
        if not path:
            raise ValueError(f"Adapter {adapter_id} não encontrado.")
        
        logger.info("adapter_manager.export_merged.started", adapter=adapter_id, output=output_path)
        # Aqui chamaria model.save_pretrained_merged(...)
