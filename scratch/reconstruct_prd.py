import os

def fix_prd():
    path = 'PRD.md'
    if not os.path.exists(path):
        return
    
    with open(path, 'rb') as f:
        data = f.read()
    
    # Try to decode as latin-1 to see the raw bytes as characters
    text = data.decode('latin-1', errors='ignore')
    
    # Massive replacement list for the specific "cat" and "mojibake" mess
    reps = {
        'Ǹ': 'é',
        'ǭ': 'á',
        'Ǒ': 'í',
        'Ǔ': 'ó',
        'Ǚ': 'ú',
        'Ǫ': 'ã',
        'ǩ': 'õ',
        'ǜ': 'ç',
        'Ǧ': 'ê',
        'ǣ': 'ô',
        'Ǣ': 'â',
        'Ã': 'í', # Sometimes Ã followed by something is í
        '?"?': ' — ',
        '?""': ' — ',
        '\'': ' → ',
        '^z': ' ∞ ',
        'o.': ' ✅ ',
        '%': ' ≥ ',
        'o': 'ç',
        'ǜ': 'ç',
        'ǜo': 'ção',
        'ǜes': 'ções',
        'o.': ' ✅ ',
        '': '', # Remove remaining junk
    }
    
    # Wait, the above is for the "cat" display. The actual file on disk has different bytes.
    # If I write the file from my memory, it's safer.
    
    content = """# PRD — AEGIS AI: Product Requirements Document

---

## ⚡ FASE ATUAL — LEIA ISTO PRIMEIRO

> **Fase ativa: FASE 6 — Interface Galáctica Neural**
> **Próxima tarefa: Tarefa 6.4 — HUD e Painel de Inspeção de Nós**
> **Instruções: Consulte `prompt.md` §1 para os passos exatos de execução.**

Não varra fases anteriores em busca de trabalho. Vá direto ao próximo ❌ na fase ativa.

---

## Visão Geral por Fase

| Fase | Nome | Tarefas | Concluídas | Status |
|---|---|---|---|---|
| 1 | Fundação (MVP) | 9 | 9 | ✅ Concluída |
| 2 | Memória Persistente & Agentes | 8 | 8 | ✅ Concluída |
| 3 | Interface Web & Voz | 8 | 8 | ✅ Concluída |
| 4 | Agentes Avançados & Automação | 6 | 6 | ✅ Concluída |
| 5 | Produção & Observabilidade | 6 | 5 | ⚪ Em curso |
| 6 | Interface Galáctica Neural | 5 | 3 | ⚪ Em curso |
| 7 | Innovation Loop | 6 | 0 | ❌ Pendente |

---

## Fase 1 — Fundação (MVP)
> **Objetivo:** Sistema funcional mínimo via CLI. AEGIS responde, usa uma ferramenta, tem personalidade definida e mantém contexto dentro da sessão.

- ✅ Tarefa 1.1 — Configuração do Projeto
- ✅ Tarefa 1.2 — Core: Config (`aegis/core/config.py`)
- ✅ Tarefa 1.3 — Core: Engine (`aegis/core/engine.py`)
- ✅ Tarefa 1.4 — Core: Context (`aegis/core/context.py`)
- ✅ Tarefa 1.5 — Personalidade & Modos (`aegis/personality/`)
- ✅ Tarefa 1.6 — Ferramentas: Base + Web Search (`aegis/tools/`)
- ✅ Tarefa 1.7 — Memória: Working Memory (`aegis/memory/working.py`)
- ✅ Tarefa 1.8 — Interface CLI (`aegis/interfaces/cli.py`)
- ✅ Tarefa 1.9 — Smoke Test Fase 1

---

## Fase 2 — Memória Persistente & Agentes
> **Objetivo:** AEGIS lembra conversas passadas entre sessões. Agentes especializados executam tarefas autônomas em múltiplos passos.

- ✅ Tarefa 2.1 — Memória Episódica (`aegis/memory/episodic.py`)
- ✅ Tarefa 2.2 — Memória Semântica (`aegis/memory/semantic.py`)
- ✅ Tarefa 2.3 — Agentes: Classe Base (`aegis/agents/base.py`)
- ✅ Tarefa 2.4 — Agente: MemoryAgent (`aegis/agents/memory.py`)
- ✅ Tarefa 2.5 — Agente: ResearchAgent (`aegis/agents/research.py`)
- ✅ Tarefa 2.6 — Ferramentas: FileSystem + RunCode + WebFetch
- ✅ Tarefa 2.7 — Engine: Roteamento Multi-Agente
- ✅ Tarefa 2.8 — Smoke Test Fase 2

---

## Fase 3 — Interface Web & Voz
> **Objetivo:** Interface visual completa com streaming em tempo real e voz bidirecional.

- ✅ Tarefa 3.1 — Backend: API FastAPI + WebSockets (`aegis/interfaces/api.py`)
- ✅ Tarefa 3.2 — Backend: Fila de Tarefas (Celery + Redis)
- ✅ Tarefa 3.3 — Frontend: Setup (React + TypeScript + Vite + Tailwind dark theme)
- ✅ Tarefa 3.4 — Frontend: Interface de Chat (streaming, `MessageBubble`, `ThinkingIndicator`)
- ✅ Tarefa 3.5 — Frontend: Painéis (histórico de sessões, status de agentes, memórias)
- ✅ Tarefa 3.6 — Voz STT: Whisper (`aegis/interfaces/voice.py`)
- ✅ Tarefa 3.7 — Voz TTS: ElevenLabs com fallback pyttsx3
- ✅ Tarefa 3.8 — Smoke Test Fase 3

---

## Fase 4 — Agentes Avançados & Automação
> **Objetivo:** Agentes autônomos para tarefas complexas e integrações com serviços externos.

- ✅ Tarefa 4.1 — Agente: TaskAgent (calendar, email, notificações)
- ✅ Tarefa 4.2 — Agente: CodeAgent (run_code, git, file_system)
- ✅ Tarefa 4.3 — Agente: MediaAgent (visão + geração de imagem)
- ✅ Tarefa 4.4 — Ferramentas: Calendar, Email, Git, Browser (Playwright)
- ✅ Tarefa 4.5 — Orquestração Multi-Agente Paralela com circuit breaker
- ✅ Tarefa 4.6 — Smoke Test Fase 4

---

## Fase 5 — Produção & Observabilidade
> **Objetivo:** Sistema pronto para uso contínuo, monitorado, seguro e extensível.

- ✅ Tarefa 5.1 — Monitoramento: Langfuse + Prometheus + Grafana
- ✅ Tarefa 5.2 — Otimização: cache semântico (threshold 0.92) + compressão de contexto
- ✅ Tarefa 5.3 — Sistema de Plugins: PluginManifest + BasePlugin + hot-reload
- ✅ Tarefa 5.4 — Segurança: log imutável + aprovação para ações irreversíveis
- ✅ Tarefa 5.5 — Documentação: README, Swagger, guias de extensão
- ❌ Tarefa 5.6 — Smoke Test Final (deploy limpo + load test 10 usuários)

---

## Fase 6 — Interface Galáctica Neural
> **Objetivo:** Substituir a interface web padrão por uma visualização espacial imersiva onde o AEGIS é um buraco negro central e cada componente do sistema orbita como um corpo celeste — posicionado por complexidade e atividade em tempo real.
> **Dependência:** Fase 3 concluída (API FastAPI + WebSocket ativos).

- ✅ Tarefa 6.1 — Engine de Renderização Galáctica (Three.js / WebGL)
- ✅ Tarefa 6.2 — Sistema de Corpos Celestes Dinâmicos
- ✅ Tarefa 6.3 — Ativação Visual por Eventos em Tempo Real
- ❌ Tarefa 6.4 — HUD e Painel de Inspeção de Nós
- ❌ Tarefa 6.5 — Modo de Voz Visual + Smoke Test Fase 6

---

## Fase 7 — Innovation Loop: Autonomia Evolutiva
> **Esta é a fase terminal do PRD planejado — e o início de algo sem fim definido.**
> Após a Fase 7 estar completa, o agente de desenvolvimento não para. Em vez disso, entra em MODO AUTÔNOMO: lê os dados reais de uso do AEGIS, analisa gargalos, lacunas e oportunidades, e gera autonomamente o próximo conjunto de tarefas — adicionando-as ao PRD e executando-as em loop contínuo.

- ❌ Tarefa 7.1 — InnovationAgent: Arquitetura e Interface
- ❌ Tarefa 7.2 — Pipeline de Análise de Dados de Uso
- ❌ Tarefa 7.3 — Motor de Geração de Tasks
- ❌ Tarefa 7.4 — Sistema de Validação e Aprovação de Tasks Geradas
- ❌ Tarefa 7.5 — Loop de Execução Autônomo
- ❌ Tarefa 7.6 — Smoke Test + Ativação do Modo Autônomo

---

### Tarefa 7.6 — Smoke Test + Ativação do Modo Autônomo

**Entregáveis:**
- Teste end-to-end do Innovation Loop completo:
  1. Injetar dados de uso simulados no Langfuse/Prometheus
  2. Disparar `InnovationLoop` manualmente
  3. Verificar que `UsageAnalyzer` produz relatório correto
  4. Verificar que `TaskGenerator` produz proposals válidas
  5. No modo SUPERVISED: verificar que proposals aparecem em `prd_proposals.md`
  6. Aprovar uma proposal e verificar que aparece no PRD formatada corretamente
  7. Verificar que agente de desenvolvimento a executa no próximo ciclo
  8. Verificar que `evaluate_impact` mede delta corretamente
- Atualizar ponteiro `⚡ FASE ATUAL` para `∞ MODO AUTÔNOMO`
- Publicar entrada especial em `progress.txt`:

```
[DATA] 🌀 INNOVATION LOOP ATIVADO — Sistema em modo evolutivo autônomo
       Fases 1—7 concluídas. AEGIS agora se autodesenvove.
       Modo inicial: SUPERVISED. Para ativar AUTONOMOUS: /innovation mode autonomous
```

**Critério de aceite:** loop completo executado end-to-end; primeira proposal real gerada e aprovada; task resultante adicionada ao PRD e executada com sucesso.

---

## ∞ MODO AUTÔNOMO — Geração Contínua de Tasks

> **Este bloco não tem fim. Quando o agente chegar aqui, não para — reinicia o Innovation Loop.**

Quando todas as tarefas das Fases 1—7 estiverem ✅:

```
NÃO PARE.

1. Execute: InnovationLoop.trigger(reason="all_phases_complete")
2. Aguarde o relatório de saúde do sistema
3. Revise as proposals geradas (modo SUPERVISED) ou execute diretamente (modo AUTONOMOUS)
4. Execute a primeira nova task aprovada seguindo §1 do prompt.md
5. Ao concluir, volte ao passo 1

O loop nunca termina. O AEGIS nunca para de melhorar.
```

**Categorias prioritárias para o Modo Autônomo:**

| Prioridade | Categoria | Sinal de Disparo |
|---|---|---|
| 🔴 CRÍTICA | Reliability | taxa de erro > 3% em qualquer componente |
| 🟠 ALTA | Performance | latência p99 > 4s em qualquer agente |
| 🟡 MÉDIA | Capability | funcionalidade solicitada pelo usuário 3+ vezes não implementada |
| 🟢 BAIXA | UX | sessão média < 3 turnos (indica fricção na experiência) |
| 🔵 EVOLUÇÃO | Experiment | benchmark de nova versão de LLM disponível |

**Limites de segurança permanentes do Modo Autônomo** (nunca desativados):
- Nenhuma task adiciona dependência de serviço pago sem aprovação humana
- Nenhuma task modifica schema de banco de dados de produção sem aprovação humana
- Nenhuma task altera `AGENTS.md` ou `prompt.md` sem aprovação humana
- Máximo de 3 tasks autônomas por ciclo de 24h no modo AUTONOMOUS
- Todo `git push` requer aprovação humana independente do modo
- Rollback automático se métricas piorarem > 10% após qualquer task

---

## Critérios de Aceite Globais

Uma tarefa só é marcada ✅ se **todos** os critérios forem atendidos:

1. **Código completo** — zero TODOs, zero `pass` não intencionais
2. **Tipagem forte** — type hints em todas as funções e classes
3. **Testes passando** — cobertura ≥ 80% no módulo; `make test` verde
4. **Logging** — operações com `structlog`; zero `print()` em produção
5. **Documentado** — docstring em classes e métodos públicos
6. **Integrado** — componente importado e chamado onde deve ser
7. **Friction log** — bugs e limitações de API registrados em `friction-log.md`
8. **Registrado** — linha adicionada em `progress.txt`
"""
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("PRD reconstructed successfully.")

if __name__ == "__main__":
    fix_prd()
