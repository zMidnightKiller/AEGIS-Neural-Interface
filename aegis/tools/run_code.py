"""
aegis/tools/run_code.py

Ferramenta para execução segura de código Python em ambiente isolado (Docker).
"""
from __future__ import annotations

import asyncio
import structlog
from typing import Any

try:
    import docker
except ImportError:
    docker = None

from aegis.core.config import get_settings
from aegis.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)


class RunCodeTool(BaseTool):
    """Executa código Python em um container Docker isolado."""

    name: str = "run_code"
    description: str = (
        "Executa código Python em um ambiente seguro e isolado. "
        "Não tem acesso à rede ou ao sistema de arquivos do host."
    )
    parameters: dict[str, Any] = {
        "code": "O código Python a ser executado.",
        "timeout": "Tempo máximo de execução em segundos (padrão: 30)."
    }

    async def execute(self, code: str, timeout: int | None = None) -> ToolResult:
        """
        Executa o código em um container.

        Args:
            code: Código Python.
            timeout: Timeout em segundos.

        Returns:
            ToolResult com stdout/stderr ou erro.
        """
        settings = get_settings()
        timeout = timeout or settings.RUNCODE_TIMEOUT
        
        logger.info("run_code.executing", timeout=timeout)

        if not docker:
            logger.error("run_code.docker_not_installed")
            return ToolResult(
                success=False, 
                error="Biblioteca 'docker' não instalada. Não é possível executar código."
            )

        try:
            client = docker.from_env()
            
            # Comando para executar o código via python -c
            # Usamos base64 ou heredoc para passar o código com segurança se necessário,
            # mas para simplicidade aqui usaremos a API de container.run
            
            container = client.containers.run(
                image=settings.RUNCODE_DOCKER_IMAGE,
                command=["python", "-c", code],
                detach=True,
                network_disabled=True,
                mem_limit="128m",
                cpu_quota=50000,  # 50% de um núcleo
                stderr=True,
                stdout=True,
            )

            # Aguarda a conclusão ou timeout
            start_time = asyncio.get_event_loop().time()
            while container.status != 'exited':
                await asyncio.sleep(0.5)
                container.reload()
                if asyncio.get_event_loop().time() - start_time > timeout:
                    container.kill()
                    return ToolResult(success=False, error=f"Execução excedeu o tempo limite de {timeout}s")

            result = container.logs().decode("utf-8")
            exit_code = container.wait()['StatusCode']
            container.remove()

            if exit_code != 0:
                logger.warning("run_code.failed", exit_code=exit_code)
                return ToolResult(
                    success=False, 
                    data=result, 
                    error=f"Código finalizado com erro (exit code {exit_code})",
                    metadata={"exit_code": exit_code}
                )

            logger.info("run_code.success")
            return ToolResult(success=True, data=result)

        except Exception as e:
            logger.error("run_code.error", error=str(e))
            return ToolResult(success=False, error=f"Falha ao executar container Docker: {str(e)}")
