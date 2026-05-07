"""
aegis/tools/git.py

Ferramenta para operacoes de Git (clone, commit, push, pull, status).
"""
from __future__ import annotations

import asyncio
import os
import structlog
from typing import Any, Literal

from aegis.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)


class GitTool(BaseTool):
    """Executa comandos Git no sistema de arquivos local."""

    name: str = "git"
    description: str = (
        "Executa comandos Git (status, add, commit, push, pull, clone). "
        "Requer que o git esteja instalado no host."
    )
    parameters: dict[str, Any] = {
        "action": "Acao Git: 'status', 'add', 'commit', 'push', 'pull', 'clone'.",
        "repo_path": "Caminho do repositorio local.",
        "params": "Dicionario de parametros extras (ex: {'message': '...', 'url': '...'})."
    }

    async def _run_git(self, args: list[str], cwd: str) -> tuple[int, str, str]:
        """Executa um comando git e retorna code, stdout, stderr."""
        process = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode or 0, stdout.decode().strip(), stderr.decode().strip()

    async def execute(
        self, 
        action: Literal["status", "add", "commit", "push", "pull", "clone"], 
        repo_path: str, 
        params: dict[str, Any] | None = None
    ) -> ToolResult:
        """
        Executa a acao Git.
        """
        logger.info("git.executing", action=action, repo_path=repo_path)
        params = params or {}

        try:
            if action == "status":
                code, out, err = await self._run_git(["status"], repo_path)
                return ToolResult(success=code == 0, data=out, error=err if code != 0 else None)

            elif action == "add":
                files = params.get("files", ".")
                if isinstance(files, str):
                    files = [files]
                code, out, err = await self._run_git(["add"] + files, repo_path)
                return ToolResult(success=code == 0, data=out, error=err if code != 0 else None)

            elif action == "commit":
                message = params.get("message", "Auto-commit from AEGIS")
                code, out, err = await self._run_git(["commit", "-m", message], repo_path)
                return ToolResult(success=code == 0, data=out, error=err if code != 0 else None)

            elif action == "push":
                remote = params.get("remote", "origin")
                branch = params.get("branch", "main")
                code, out, err = await self._run_git(["push", remote, branch], repo_path)
                return ToolResult(success=code == 0, data=out, error=err if code != 0 else None)

            elif action == "pull":
                remote = params.get("remote", "origin")
                branch = params.get("branch", "main")
                code, out, err = await self._run_git(["pull", remote, branch], repo_path)
                return ToolResult(success=code == 0, data=out, error=err if code != 0 else None)

            elif action == "clone":
                url = params.get("url")
                if not url:
                    return ToolResult(success=False, error="URL eh obrigatoria para clone.")
                
                # Clone precisa do diretorio pai
                parent_dir = os.path.dirname(os.path.abspath(repo_path))
                target_name = os.path.basename(repo_path)
                
                code, out, err = await self._run_git(["clone", url, target_name], parent_dir)
                return ToolResult(success=code == 0, data=out, error=err if code != 0 else None)

            else:
                return ToolResult(success=False, error=f"Acao Git desconhecida: {action}")

        except Exception as e:
            logger.error("git.error", error=str(e))
            return ToolResult(success=False, error=f"Erro ao executar Git: {str(e)}")
