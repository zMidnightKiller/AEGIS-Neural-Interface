import asyncio
import os
import sys
from datetime import datetime

# Adiciona o diretório raiz ao path para permitir imports do pacote aegis
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest.mock
# Mock apscheduler before it's imported by aegis.innovation.loop
sys.modules["apscheduler"] = unittest.mock.MagicMock()
sys.modules["apscheduler.schedulers"] = unittest.mock.MagicMock()
sys.modules["apscheduler.schedulers.asyncio"] = unittest.mock.MagicMock()

try:
    import structlog
    from aegis.innovation.loop import get_innovation_loop
except ImportError as e:
    print(f"Erro ao importar dependências: {e}")
    sys.exit(1)

async def main():
    loop = get_innovation_loop()
    
    # Mocking TaskGenerator to provide real proposals based on current system friction
    from aegis.innovation.task_generator import InnovationProposal, ProposedTask
    
    mock_proposals = [
        InnovationProposal(
            title="Saneamento de Encoding e Robustez de Infraestrutura",
            rationale="Detectados problemas recorrentes de encoding (UTF-16/BOM) que quebram ferramentas de visualização e inconsistências de dependências no ambiente local.",
            priority=1, # CRITICAL
            risk_level=1,
            tasks=[
                ProposedTask(
                    id="8.1",
                    phase="8",
                    title="Normalização de Encoding (UTF-8)",
                    description="Converter todos os arquivos .md, .txt e .py para UTF-8 sem BOM para garantir compatibilidade com as ferramentas do Antigravity e sub-agentes.",
                    deliverables=["Script de migração de encoding", "Arquivos normalizados"],
                    acceptance_criteria="view_file funciona em todos os arquivos sem erro de mime type",
                    estimated_complexity=1
                ),
                ProposedTask(
                    id="8.2",
                    phase="8",
                    title="Fix de Dependências Locais",
                    description="Resolver a ausência de apscheduler e garantir que o ambiente tenha as libs básicas do pyproject.toml.",
                    deliverables=["Ambiente local estabilizado"],
                    acceptance_criteria="Innovation Loop roda sem erros de importação",
                    estimated_complexity=1
                )
            ]
        )
    ]
    
    loop.generator.generate = unittest.mock.AsyncMock(return_value=mock_proposals)
    
    # Mock settings to avoid ANTHROPIC_API_KEY error
    loop.settings.ANTHROPIC_API_KEY = unittest.mock.MagicMock()
    loop.settings.ANTHROPIC_API_KEY.get_secret_value.return_value = "mock_key"

    print(f"[{datetime.now().isoformat()}] 🌀 AEGIS Innovation Loop Triggered (MOCKED GENERATOR)")
    print("Razão: all_phases_complete")
    print("-" * 50)
    
    result = await loop.trigger(reason="all_phases_complete")
    
    print("-" * 50)
    print(f"Status: {result.status}")
    print(f"Propostas Geradas: {result.proposals_generated}")
    print(f"Propostas Aprovadas: {result.proposals_approved}")
    
    if result.status == "success":
        if result.proposals_approved > 0:
            print("\n✅ Novas tarefas foram adicionadas ao ciclo de execução.")
            print("Verifique 'prd_approved.md' para tarefas autônomas.")
        elif result.proposals_generated > 0:
            print("\n⚠️ Propostas pendentes de aprovação.")
            print("Verifique 'prd_proposals.md' e use '/approve <id>' no CLI.")
        else:
            print("\nℹ️ Nenhuma melhoria identificada neste ciclo.")
    
    if result.error:
        print(f"\n❌ Erro durante a execução: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())
