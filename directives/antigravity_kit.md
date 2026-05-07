# Directive: Antigravity Kit 2.0 Management
> Protocolo para gestão de performance e telemetria avançada da Helen AI.

## Overview
O **Antigravity Kit 2.0** é a camada de otimização de hardware e inteligência que garante a estabilidade do sistema Helen mesmo em condições de alta carga computacional.

## Layer 3 Tools (Execution)
- `execution/antigravity_monitor.py`: Monitor de recursos e telemetria.
- `execution/system_optimizer.py`: Otimizador de sistema e limpeza.

## Kit 2.0 Premium Skills (Capacidades)
As skills estão localizadas em `execution/skills/` e fornecem superpoderes à Helen:
1. **Media Intelligence**: Visão computacional e audição de alta fidelidade.
2. **Deep Research**: Pesquisa autônoma iterativa para síntese de fatos.
3. **Neural Memory Mapping**: Gerenciamento do Gráfico de Conhecimento Espacial (Estrelas, Planetas e Galáxias).

## Standard Operating Procedures (SOPs)

### 1. Inicialização do Sistema
Sempre que o motor principal (`core/engine.py`) for iniciado, ele deve instanciar o `AntigravityMonitor`.
- **Ação**: Chamar `monitor.optimize_performance()` no setup.
- **Frequência**: Uma vez por sessão.

### 2. Validação de Carga (Check Health)
Antes de executar qualquer ciclo de aprendizado ou processamento de mídia pesado.
- **Script**: `execution/antigravity_monitor.py` -> `check_health()`
- **Lógica**: Se `healthy` for `False`, adiar a tarefa em 30 segundos e tentar novamente. Não ignorar o throttling.

### 3. Log de Telemetria
Manter registro constante do impacto da Helen no sistema.
- **Frequência**: Logar a cada 5 minutos ou após tarefas críticas.
- **Arquivo**: `.tmp/telemetry.log`

## Throttling Levels
| Nível | CPU % | RAM % | Ação |
|-------|-------|-------|------|
| **Normal** | < 40% | < 60% | Execução total |
| **Warning** | 40-70% | 60-80% | Reduzir threads, aumentar sleep |
| **Critical** | > 70% | > 80% | Pausar tarefas não essenciais |

## Self-Annealing Loop
Se o monitor detectar falhas recorrentes de memória, ele deve disparar o `system_optimizer.py` para limpar buffers e arquivos temporários antigos.
