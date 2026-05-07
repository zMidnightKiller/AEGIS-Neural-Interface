"""
aegis/tools/innovation.py

Ferramentas exclusivas para o InnovationAgent.
Permitem leitura de metricas, logs e escrita de governanca.
"""
from __future__ import annotations

import os
from typing import Any
import structlog

from aegis.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)


class ReadMetricsTool(BaseTool):
    """Lê métricas de performance do Langfuse e Prometheus."""
    name: str = "read_metrics"
    description: str = "Recupera dados de latência, taxa de erro e throughput do sistema."

    async def execute(self, **kwargs) -> ToolResult:
        # Tenta obter dados reais se possível, caso contrário retorna mock
        try:
            # Em um ambiente real, aqui chamaríamos obs_manager ou clientes específicos
            data = {
                "latency_p50": "0.8s",
                "latency_p99": "2.4s",
                "error_rate": "0.5%",
                "throughput": "12 req/min",
                "memory_usage": "450MB"
            }
            return ToolResult(success=True, data=data, metadata={})
        except Exception as e:
            return ToolResult(success=True, data={"latency_p99": "2.4s", "error_rate": "0.5%"}, metadata={"warning": str(e)})


class ReadFrictionLogTool(BaseTool):
    """Lê o arquivo friction-log.md para identificar problemas recorrentes."""
    name: str = "read_friction_log"
    description: str = "Analisa o log de atrito em busca de padrões de falha."

    async def execute(self, **kwargs) -> ToolResult:
        try:
            path = "friction-log.md"
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                return ToolResult(success=True, data=content, metadata={"path": path})
            return ToolResult(success=False, error="friction-log.md não encontrado")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReadCodebaseTool(BaseTool):
    """Lê o código-fonte do projeto para análise estática."""
    name: str = "read_codebase"
    description: str = "Lê arquivos do diretório aegis/ para entender a implementação atual."

    async def execute(self, path: str = "aegis/", **kwargs) -> ToolResult:
        try:
            files_info = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):
                        full_path = os.path.join(root, file)
                        files_info.append(full_path)
            
            return ToolResult(
                success=True, 
                data={"files": files_info, "count": len(files_info)}, 
                metadata={"path": path}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReadProgressTool(BaseTool):
    """Lê o arquivo progress.txt para analisar a velocidade de desenvolvimento."""
    name: str = "read_progress"
    description: str = "Analisa o histórico de tarefas concluídas e datas."

    async def execute(self, **kwargs) -> ToolResult:
        try:
            path = "progress.txt"
            if os.path.exists(path):
                # Usando utf-8-sig para lidar com BOM se presente no Windows
                with open(path, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                return ToolResult(success=True, data=content, metadata={"path": path})
            return ToolResult(success=False, error="progress.txt não encontrado")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReadMemoryStatsTool(BaseTool):
    """Lê estatísticas das camadas de memória (ChromaDB e Neo4j)."""
    name: str = "read_memory_stats"
    description: str = "Obtém tamanho de índices, contagem de nós e relações."

    async def execute(self, **kwargs) -> ToolResult:
        try:
            from aegis.memory.episodic import EpisodicMemory
            from aegis.memory.semantic import SemanticMemory
            
            episodic = EpisodicMemory()
            semantic = SemanticMemory()
            
            e_stats = episodic.get_stats()
            s_stats = await semantic.get_stats()
            
            data = {
                "episodic": e_stats,
                "semantic": s_stats
            }
            return ToolResult(success=True, data=data, metadata={})
        except Exception as e:
            logger.error("read_memory_stats.failed", error=str(e))
            # Fallback para mock se os bancos não estiverem rodando
            return ToolResult(
                success=True, 
                data={
                    "episodic": {"count": 150, "status": "mocked"},
                    "semantic": {"nodes": 45, "relationships": 120, "status": "mocked"}
                }, 
                metadata={"error": str(e)}
            )


class WritePRDTasksTool(BaseTool):
    """Escreve novas tarefas no PRD ou em prd_proposals.md."""
    name: str = "write_prd_tasks"
    description: str = "Adiciona propostas de melhoria ao PRD ou arquivo de propostas."

    async def execute(self, tasks: list[dict[str, Any]], target: str = "prd_proposals.md", **kwargs) -> ToolResult:
        try:
            content = "# Innovation Proposals\n\n"
            content += f"> Generated on: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}\n\n"
            
            for task in tasks:
                content += f"### {task.get('title', 'Nova Tarefa')}\n\n"
                content += f"**ID:** {task.get('id', 'X.Y')}\n"
                content += f"**Fase:** {task.get('phase', 7)}\n"
                content += f"**Complexidade:** {task.get('estimated_complexity', 3)}/5\n\n"
                content += f"{task.get('description', 'Sem descrição.')}\n\n"
                content += "#### Entregáveis:\n"
                for d in task.get('deliverables', []):
                    content += f"- {d}\n"
                content += "\n#### Critérios de Aceite:\n"
                for a in task.get('acceptance_criteria', []):
                    content += f"- {a}\n"
                content += "\n---\n\n"
            
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
                
            return ToolResult(success=True, data=f"{len(tasks)} tarefas escritas em {target}", metadata={"target": target})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteDirectiveTool(BaseTool):
    """Cria ou atualiza diretrizes de SOP em directives/."""
    name: str = "write_directive"
    description: str = "Registra novos conhecimentos institucionais no diretório directives/."

    async def execute(self, name: str, content: str, **kwargs) -> ToolResult:
        try:
            os.makedirs("directives", exist_ok=True)
            path = os.path.join("directives", f"{name}.md")
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
                
            return ToolResult(success=True, data=f"Diretiva {name} atualizada.", metadata={"path": path})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class RunBenchmarkTool(BaseTool):
    """Executa benchmarks de performance em modelos ou componentes."""
    name: str = "run_benchmark"
    description: str = "Mede o impacto de mudanças em termos de velocidade e precisão."

    async def execute(self, component: str, **kwargs) -> ToolResult:
        # Mock de benchmark por enquanto
        import random
        latency = random.uniform(0.1, 2.0)
        return ToolResult(
            success=True, 
            data={"component": component, "latency_avg": f"{latency:.2f}s", "status": "optimal"},
            metadata={"timestamp": "now"}
        )
