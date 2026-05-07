"""
aegis/tools/file_system.py

Ferramenta para manipulação de arquivos e diretórios com restrições de segurança.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import structlog

from aegis.core.config import get_settings
from aegis.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)


class FileSystemTool(BaseTool):
    """Manipula arquivos e diretórios em locais autorizados."""

    name: str = "file_system"
    description: str = (
        "Lê, escreve e lista arquivos em diretórios autorizados. "
        "Ações disponíveis: read, write, list."
    )
    parameters: dict[str, Any] = {
        "action": "Ação a ser executada: 'read', 'write' ou 'list'.",
        "path": "Caminho relativo do arquivo ou diretório.",
        "content": "Conteúdo para escrever (apenas para ação 'write').",
    }

    def _is_path_allowed(self, path: str) -> bool:
        """Verifica se o caminho está dentro de um diretório autorizado."""
        settings = get_settings()
        target_path = Path(path).resolve()
        
        for allowed_str in settings.ALLOWED_FS_PATHS:
            allowed_path = Path(allowed_str).resolve()
            if target_path == allowed_path or allowed_path in target_path.parents:
                return True
        return False

    async def execute(
        self, 
        action: Literal["read", "write", "list"], 
        path: str, 
        content: str | None = None
    ) -> ToolResult:
        """
        Executa a operação de sistema de arquivos.

        Args:
            action: Ação (read, write, list).
            path: Caminho relativo.
            content: Conteúdo (para write).

        Returns:
            ToolResult com os dados ou erro.
        """
        logger.info("file_system.executing", action=action, path=path)

        # Validação de segurança
        if not self._is_path_allowed(path):
            logger.warning("file_system.path_blocked", path=path)
            return ToolResult(
                success=False,
                error=f"Acesso negado ao caminho: {path}. Fora dos diretórios autorizados.",
                metadata={"path": path}
            )

        try:
            target = Path(path).resolve()

            if action == "read":
                if not target.exists():
                    return ToolResult(success=False, error=f"Arquivo não encontrado: {path}")
                if not target.is_file():
                    return ToolResult(success=False, error=f"O caminho não é um arquivo: {path}")
                
                content = target.read_text(encoding="utf-8")
                return ToolResult(success=True, data=content)

            elif action == "write":
                if content is None:
                    return ToolResult(success=False, error="Conteúdo é obrigatório para escrita.")
                
                # Garante que o diretório pai existe
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                return ToolResult(success=True, data=f"Arquivo escrito com sucesso: {path}")

            elif action == "list":
                if not target.exists():
                    return ToolResult(success=False, error=f"Diretório não encontrado: {path}")
                if not target.is_dir():
                    return ToolResult(success=False, error=f"O caminho não é um diretório: {path}")
                
                items = [p.name for p in target.iterdir()]
                return ToolResult(success=True, data=items)

            else:
                return ToolResult(success=False, error=f"Ação inválida: {action}")

        except Exception as e:
            logger.error("file_system.error", action=action, path=path, error=str(e))
            return ToolResult(success=False, error=f"Erro na operação de arquivo: {str(e)}")
