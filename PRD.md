# PRD — AEGIS AI: Product Requirements Document

---

## ⚡ FASE ATUAL — LEIA ISTO PRIMEIRO

> **Fase ativa: ∞ MODO AUTÔNOMO — Geração Contínua**
> **Próxima tarefa: InnovationLoop.trigger(reason="all_phases_complete")**
> **Instruções: Consulte `prompt.md` §9 para os passos exatos de execução.**

Não varra fases anteriores em busca de trabalho. Vá direto ao próximo ❌ na fase ativa.

---

## Visão Geral por Fase

| Fase | Nome | Tarefas | Concluídas | Status |
|---|---|---|---|---|
| 1 | Fundação (MVP) | 9 | 0 | 🔵 Ativa |
| 2 | Memória Persistente & Agentes | 8 | 0 | ⚪ Aguardando |
| 3 | Interface Web & Voz | 8 | 0 | ⚪ Aguardando |
| 4 | Agentes Avançados & Automação | 6 | 0 | ⚪ Aguardando |
| 5 | Produção & Observabilidade | 6 | 0 | ⚪ Aguardando |
| 6 | Interface Galáctica Neural | 5 | 5 | ✅ Concluída |
| 7 | Innovation Loop — Autonomia Evolutiva | 6 | 0 | 🔵 Ativa |
| ∞ | MODO AUTÔNOMO — Geração Contínua | ∞ | — | 🔴 Inativo |

---

## Fase 1 — Fundação (MVP)

> **Objetivo:** Sistema funcional mínimo via CLI. AEGIS responde, usa uma ferramenta,
> tem personalidade definida e mantém contexto dentro da sessão.

- ✅ Tarefa 1.1 — Configuração do Projeto
- ✅ Tarefa 1.2 — Core: Config (`aegis/core/config.py`)
- ✅ Tarefa 1.3 — Core: Engine (`aegis/core/engine.py`)
- ✅ Tarefa 1.4 — Core: Context (`aegis/core/context.py`)
- ✅ Tarefa 1.5 — Personalidade & Modos (`aegis/personality/`)
- ✅ Tarefa 1.6 — Ferramentas: Base + Web Search (`aegis/tools/`)
- ✅ Tarefa 1.7 — Memória Working Memory (`aegis/memory/working.py`)
- ✅ Tarefa 1.8 — Interface CLI (`aegis/interfaces/cli.py`)
- ✅ Tarefa 1.9 — Smoke Test Fase 1

---

### Tarefa 1.1 — Configuração do Projeto

**Entregáveis:**
- Estrutura de diretórios completa conforme `AGENTS.md`
- `pyproject.toml` com dependências: `fastapi`, `anthropic`, `redis`, `langchain`, `chromadb`, `httpx`, `structlog`, `pydantic-settings`, `tenacity`, `typer`, `rich`, `pytest`, `pytest-asyncio`
- `.env.example` com todas as variáveis documentadas e comentadas
- `docker-compose.yml` com serviços: `redis`, `chromadb`, `neo4j`
- `Makefile` com: `make dev`, `make test`, `make lint`, `make docker-up`, `make docker-down`
- `pre-commit` config: `black`, `ruff`, `mypy`

**Critério de aceite:** `make docker-up` sobe todos os serviços sem erro; `make lint` passa.

---

### Tarefa 1.2 — Core: Config

**Arquivo:** `aegis/core/config.py`

**Entregáveis:**
- Classe `Settings` com Pydantic Settings v2
- Validação de todas as env vars no startup com mensagens de erro descritivas
- Suporte a ambientes: `development`, `production`, `test`
- Singleton via `lru_cache`
- Testes: `tests/core/test_config.py`

**Critério de aceite:** startup falha com mensagem clara se `ANTHROPIC_API_KEY` estiver ausente.

---

### Tarefa 1.3 — Core: Engine

**Arquivo:** `aegis/core/engine.py`

**Entregáveis:**
- Classe `Engine` com método `async process(input: UserInput) -> AgentResponse`
- Roteamento básico: detecta intenção e seleciona agente ou ferramenta
- Logging estruturado em cada etapa do pipeline (entrada → roteamento → execução → saída)
- Testes: `tests/core/test_engine.py`

**Critério de aceite:** `engine.process("oi")` retorna resposta sem exceção; logs aparecem.

---

### Tarefa 1.4 — Core: Context

**Arquivo:** `aegis/core/context.py`

**Entregáveis:**
- Classe `Context` para gestão da janela de contexto da sessão
- Controle de tamanho por max tokens (configurável via `Settings`)
- Métodos: `add_message`, `get_window`, `serialize`, `deserialize`
- Testes: `tests/core/test_context.py`

**Critério de aceite:** janela trunca corretamente ao atingir o limite de tokens.

---

### Tarefa 1.5 — Personalidade & Modos

**Arquivos:** `aegis/personality/modes.py`, `aegis/personality/prompts.py`

**Entregáveis:**
- Enum `OperatingMode`: `STANDARD`, `BRIEFING`, `ANALYSIS`, `SILENT`, `VERBOSE`
- Função `build_system_prompt(mode, tools_list, memory_context, user_profile) -> str`
- Cada modo produz variante distinta e verificável do system prompt
- Testes: `tests/personality/test_prompts.py`

**Critério de aceite:** modo `BRIEFING` produz prompt visivelmente mais curto que `ANALYSIS`.

---

### Tarefa 1.6 — Ferramentas: Base + Web Search

**Arquivos:** `aegis/tools/base.py`, `aegis/tools/web_search.py`

**Entregáveis:**
- Classe abstrata `BaseTool` com: `name`, `description`, `parameters`, `async execute(**kwargs) -> ToolResult`
- Dataclass `ToolResult(success: bool, data: Any, error: str | None, metadata: dict)`
- `WebSearchTool` com integração Tavily API
- Retry com backoff exponencial via `tenacity` (3 tentativas: 2s, 4s, 8s)
- Testes: `tests/tools/test_web_search.py` — Tavily mockado com `AsyncMock`

**Critério de aceite:** rate limit retorna `ToolResult(success=False)` sem exceção não tratada.

---

### Tarefa 1.7 — Memória: Working Memory

**Arquivo:** `aegis/memory/working.py`

**Entregáveis:**
- Classe `WorkingMemory` com Redis como backend
- Métodos: `save_message`, `get_history(n)`, `clear_session`, `get_session_id`
- TTL de sessão configurável (padrão: 24h)
- Testes: `tests/memory/test_working.py` — Redis mockado

**Critério de aceite:** histórico persiste entre chamadas na mesma sessão; expira após TTL.

---

### Tarefa 1.8 — Interface: CLI

**Arquivo:** `aegis/interfaces/cli.py`

**Entregáveis:**
- REPL interativo com Typer + Rich
- Cabeçalho com modo atual e ID de sessão
- Streaming de resposta token a token
- Comandos: `/mode <MODO>`, `/clear`, `/memory`, `/help`, `/exit`
- Testes: `tests/interfaces/test_cli.py`

**Critério de aceite:** `/mode BRIEFING` altera comportamento visivelmente na próxima resposta.

---

### Tarefa 1.9 — Smoke Test Fase 1

**Entregáveis:**
- Script `tests/smoke/test_fase1.py` validando fluxo completo end-to-end
- AEGIS responde via CLI com `web_search` ativo
- Contexto de sessão persiste dentro da conversa
- `make test` passa; todas as tarefas 1.1–1.8 marcadas ✅
- Atualizar ponteiro `⚡ FASE ATUAL` no topo deste arquivo para Fase 2

---

## Fase 2 — Memória Persistente & Agentes

> **Objetivo:** AEGIS lembra conversas passadas entre sessões. Agentes especializados
> executam tarefas autônomas em múltiplos passos.

- ✅ Tarefa 2.1 — Memória Episódica (`aegis/memory/episodic.py`)
- ✅ Tarefa 2.2 — Memória Semântica (`aegis/memory/semantic.py`)
- ✅ Tarefa 2.3 — Agentes: Classe Base (`aegis/agents/base.py`)
- ✅ Tarefa 2.4 — Agente: MemoryAgent (`aegis/agents/memory.py`)
- ✅ Tarefa 2.5 — Agente: ResearchAgent (`aegis/agents/research.py`)
- ✅ Tarefa 2.6 — Ferramentas: FileSystem + RunCode + WebFetch
- ✅ Tarefa 2.7 — Engine: Roteamento Multi-Agente
- ✅ Tarefa 2.8 — Smoke Test Fase 2

---

### Tarefa 2.1 — Memória Episódica

**Arquivo:** `aegis/memory/episodic.py`

**Entregáveis:**
- Classe `EpisodicMemory` com ChromaDB
- Embeddings: `text-embedding-3-small` (OpenAI) com fallback `nomic-embed-text` (Ollama)
- Métodos: `save_episode(text, metadata)`, `search_similar(query, threshold=0.75, n=5)`, `get_recent(n)`
- Injeção automática de contexto relevante no prompt via `prompts.py`
- Testes: `tests/memory/test_episodic.py`

---

### Tarefa 2.2 — Memória Semântica

**Arquivo:** `aegis/memory/semantic.py`

**Entregáveis:**
- Classe `SemanticMemory` com Neo4j
- Schema: `(User)-[PREFERS]->(Entity)`, `(Concept)-[RELATED_TO]->(Concept)`
- Métodos: `save_fact`, `get_user_profile`, `update_preference`, `query_graph(cypher)`
- Extração automática de entidades pós-conversa
- Testes: `tests/memory/test_semantic.py`

---

### Tarefa 2.3 — Agentes: Classe Base

**Arquivo:** `aegis/agents/base.py`

**Entregáveis:**
- Classe abstrata `BaseAgent` com `name`, `description`, `max_steps: int`
- Método `async run(task: str, context: Context) -> AgentResult`
- Loop: `plan → execute_tool → observe → iterate` (máx `max_steps`)
- Dataclass `AgentResult(success, output, steps_taken, tools_used, error)`
- Testes: `tests/agents/test_base.py`

---

### Tarefa 2.4 — Agente: MemoryAgent

**Arquivo:** `aegis/agents/memory.py`

**Entregáveis:**
- Ferramentas: `memory_search`, `memory_save`, `memory_update`
- Executado automaticamente **pre e post** em toda interação pela Engine
- Pre: busca episódios relevantes → injeta no contexto
- Post: extrai e persiste entidades e fatos novos
- Testes: `tests/agents/test_memory_agent.py`

---

### Tarefa 2.5 — Agente: ResearchAgent

**Arquivo:** `aegis/agents/research.py`

**Entregáveis:**
- Ferramentas: `WebSearchTool`, `WebFetchTool`
- Output: `ResearchReport(summary, sources, confidence_score, key_findings)`
- Trigger automático para queries factuais (classifier na Engine)
- Testes: `tests/agents/test_research_agent.py`

---

### Tarefa 2.6 — Ferramentas: FileSystem + RunCode + WebFetch

**Arquivos:** `aegis/tools/file_system.py`, `aegis/tools/run_code.py`, `aegis/tools/web_fetch.py`

**Entregáveis:**
- `FileSystemTool`: read, write, list — restrito a diretórios autorizados em config
- `RunCodeTool`: executa Python em Docker isolado; timeout configurável; sem acesso à rede
- `WebFetchTool`: fetch URL + extração de texto limpo; respeita robots.txt
- Testes com todas as dependências externas mockadas

---

### Tarefa 2.7 — Engine: Roteamento Multi-Agente

**Arquivo:** `aegis/core/engine.py` (atualização)

**Entregáveis:**
- Classifier de intenção LLM-based com prompt dedicado
- Roteamento para agente correto com base na intenção
- Suporte a pipeline sequencial de múltiplos agentes por query
- Testes: `tests/core/test_routing.py`

---

### Tarefa 2.8 — Smoke Test Fase 2

**Critérios:**
- AEGIS lembra fato de sessão anterior (ChromaDB ativo)
- ResearchAgent entrega `ResearchReport` com fontes reais
- MemoryAgent persiste e recupera preferência no Neo4j
- `make test` passa; tarefas 2.1–2.7 marcadas ✅
- Atualizar ponteiro `⚡ FASE ATUAL` para Fase 3

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
- ✅ Tarefa 5.3 — Sistema de Plugins: `PluginManifest` + `BasePlugin` + hot-reload
- ✅ Tarefa 5.4 — Segurança: log imutável + aprovação para ações irreversíveis
- ✅ Tarefa 5.5 — Documentação: README, Swagger, guias de extensão
- ✅ Tarefa 5.6 — Smoke Test Final (deploy limpo + load test 10 usuários)

---

## Fase 6 — Interface Galáctica Neural

> **Objetivo:** Substituir a interface web padrão por uma visualização espacial imersiva onde
> o AEGIS é um buraco negro central e cada componente do sistema orbita como um corpo
> celeste — posicionado por complexidade e atividade em tempo real.
>
> **Dependência:** Fase 3 concluída (API FastAPI + WebSocket ativos).

- ✅ Tarefa 6.1 — Engine de Renderização Galáctica (Three.js / WebGL)
- ✅ Tarefa 6.2 — Sistema de Corpos Celestes Dinâmicos
- ✅ Tarefa 6.3 — Ativação Visual por Eventos em Tempo Real
- ✅ Tarefa 6.4 — HUD e Painel de Inspeção de Nós
- ✅ Tarefa 6.5 — Modo de Voz Visual + Smoke Test Fase 6

---

### Tarefa 6.1 — Engine de Renderização Galáctica

**Arquivos:** `frontend/src/galaxy/engine.ts`, `frontend/src/galaxy/scene.ts`

**Entregáveis:**
- Setup Three.js com WebGL renderer, câmera perspectiva e OrbitControls
- Cena base: fundo espacial com campo de estrelas procedural (2.000+ partículas com shimmer)
- Nebulosa procedural ao fundo: blobs volumétricos em azul/violeta via ShaderMaterial
- Buraco negro central (AEGIS): esfera negra com disco de acreção animado via shader GLSL,
  lente gravitacional simulada ao redor, anel de luz ciano pulsando com `sin(time)`
- Linha de varredura de scan HUD sobreposta ao canvas (overlay 2D em CSS)
- Performance alvo: 60fps estável em hardware moderno; degradação graceful para 30fps
- Testes: renderiza sem WebGL error; cena inicializa em < 800ms

**Critério de aceite:** buraco negro visível com disco animado; câmera orbita com mouse.

---

### Tarefa 6.2 — Sistema de Corpos Celestes Dinâmicos

**Arquivos:** `frontend/src/galaxy/bodies.ts`, `frontend/src/galaxy/orbits.ts`

**Hierarquia orbital por complexidade:**

| Anel | Raio | Tipo de Corpo | Componentes AEGIS |
|---|---|---|---|
| 1 — Core | 90u | Estrelas (brilho alto) | Working Memory, Episodic Memory, Semantic Memory |
| 2 — Agents | 155u | Planetas (tamanho médio) | ResearchAgent, TaskAgent, CodeAgent, MemoryAgent, MediaAgent |
| 3 — Tools | 210u | Asteroides (pequenos) | WebSearch, FileSystem, RunCode, Calendar, Email, Git |
| 4 — Extended | 260u | Cometas (com cauda) | BrowserControl, ElevenLabs TTS, ImageGen, Plugins |

**Entregáveis:**
- Classe `CelestialBody` com: `mesh`, `orbit_radius`, `speed`, `complexity_score`, `label_sprite`
- Órbitas inclinadas levemente aleatoriamente (±15°) para profundidade 3D real
- Tamanho do corpo proporcional a `complexity_score` (float 0–1 calculado por uso real)
- Cometas com `TubeGeometry` de cauda que aponta na direção oposta ao movimento
- Labels flutuantes em CSS3DRenderer que sempre encaram a câmera
- Trilha orbital (`Line` com `BufferGeometry`) em opacidade baixa e tracejada
- Testes: todos os nós instanciam sem exceção; órbitas não colidem no raio mínimo

**Critério de aceite:** todos os componentes do AEGIS visíveis orbitando em anéis distintos.

---

### Tarefa 6.3 — Ativação Visual por Eventos em Tempo Real

**Arquivo:** `frontend/src/galaxy/events.ts`

**Entregáveis:**
- WebSocket consumer que escuta eventos da Engine AEGIS: `tool_called`, `agent_started`,
  `agent_finished`, `memory_retrieved`, `error`
- Ao `tool_called`: linha de energia animada (partícula viajando do nó até o buraco negro)
  via `THREE.Points` com shader de movimento; nó pulsa com escala 1.0 → 1.4 → 1.0
- Ao `memory_retrieved`: feixe de luz azul conectando nó de memória ao centro
- Ao `agent_started`: halo ao redor do planeta agente aumenta gradualmente
- Ao `agent_finished (success)`: explosão de partículas verdes ao redor do nó
- Ao `error`: nó pisca vermelho 3x; linha de energia fragmenta antes de chegar ao centro
- Ao `thinking`: buraco negro pulsa mais intensamente; disco de acreção acelera
- Testes: cada tipo de evento produz animação distinta sem memory leak após 1.000 eventos

**Critério de aceite:** conversa real com AEGIS produz animações visíveis e corretas na galáxia.

---

### Tarefa 6.4 — HUD e Painel de Inspeção de Nós

**Arquivos:** `frontend/src/galaxy/hud.tsx`, `frontend/src/galaxy/NodePanel.tsx`

**Entregáveis:**
- HUD overlay (React + CSS, position absolute sobre canvas): canto superior esquerdo mostra
  `MODO`, `NÓS ATIVOS`, `LATÊNCIA MÉDIA`; canto superior direito mostra `GRAVIDADE ∞`,
  `ÓRBITAS`, `STATUS`
- Raycasting: hover sobre corpo celeste exibe tooltip com nome, tipo, descrição e barra de
  complexidade (igual ao protótipo)
- Clique em nó abre painel lateral deslizante (`NodePanel`): métricas reais do componente
  (calls feitas, taxa de sucesso, latência p50/p99, último erro do friction-log)
- Painel do buraco negro (clique no centro): métricas globais do AEGIS — tokens processados,
  sessões ativas, memórias armazenadas, modo atual com botões de troca
- Botão `/mode` flutuante no canto inferior: abre seletor de modo com animação galáctica
  (modos diferentes alteram a intensidade do disco de acreção e a cor dominante da cena)
- Testes: raycasting detecta nó correto; painel abre/fecha sem rerender desnecessário

**Critério de aceite:** clicar em qualquer nó mostra dados reais do componente; painel fecha com ESC.

---

### Tarefa 6.5 — Modo de Voz Visual + Smoke Test Fase 6

**Entregáveis:**
- Quando TTS estiver falando: analisar amplitude de áudio via `Web Audio API`
  e mapear para escala do buraco negro (pulso sincronizado com a voz)
- Partículas da nebulosa se movem mais rapidamente durante fala ativa
- Quando STT estiver ouvindo: anel ciano ao redor do buraco negro pisca lentamente
- Quando em modo `SILENT`: cena em tons de cinza com brilho reduzido
- Quando em modo `ANALYSIS`: todos os anéis orbitais ficam visíveis e mais brilhantes
- Smoke test completo: conversa por voz produz animação sincronizada; troca de modo
  altera cena visualmente; métricas reais aparecem nos painéis
- Atualizar ponteiro `⚡ FASE ATUAL` para Fase 7

**Critério de aceite:** voz do AEGIS faz o buraco negro pulsar em sincronia audível.

---

## Fase 7 — Innovation Loop: Autonomia Evolutiva

> **Esta é a fase terminal do PRD planejado — e o início de algo sem fim definido.**
>
> Após a Fase 7 estar completa, o agente de desenvolvimento **não para**.
> Em vez disso, entra em **MODO AUTÔNOMO**: lê os dados reais de uso do AEGIS,
> analisa gargalos, lacunas e oportunidades, e gera autonomamente o próximo conjunto
> de tarefas — adicionando-as ao PRD e executando-as em loop contínuo.
>
> **Dependência:** Todas as Fases 1–6 concluídas. Langfuse/Prometheus ativos (Tarefa 5.1).

- ✅ Tarefa 7.1 — InnovationAgent: Arquitetura e Interface
- ✅ Tarefa 7.2 — Pipeline de Análise de Dados de Uso
- ✅ Tarefa 7.3 — Motor de Geração de Tasks
- ✅ Tarefa 7.4 — Sistema de Validação e Aprovação de Tasks Geradas
- ✅ Tarefa 7.5 — Loop de Execução Autônomo
- ✅ Tarefa 7.6 — Smoke Test + Ativação do Modo Autônomo

---

### Tarefa 7.1 — InnovationAgent: Arquitetura e Interface

**Arquivo:** `aegis/agents/innovation.py`

**Conceito:** O InnovationAgent é um agente de meta-nível. Ele não responde ao usuário —
ele observa o próprio AEGIS, identifica onde o sistema é fraco, e propõe melhorias concretas
como novas tarefas no PRD.

**Entregáveis:**
- Classe `InnovationAgent(BaseAgent)` com modo de operação exclusivo: não é chamado
  pela Engine normal — é disparado pelo scheduler após conclusão de todas as tasks do PRD
- Acesso de leitura a: Langfuse traces, Prometheus metrics, friction-log.md, progress.txt,
  PRD.md, e todo o código-fonte de `aegis/`
- Ferramentas exclusivas: `read_metrics`, `read_friction_log`, `read_codebase`,
  `write_prd_tasks`, `write_directive`, `run_benchmark`
- Dataclass `InnovationProposal(title, rationale, tasks: list[ProposedTask], priority, risk_level)`
- Dataclass `ProposedTask(id, phase, title, description, deliverables, acceptance_criteria, estimated_complexity)`
- Testes: `tests/agents/test_innovation_agent.py` — todas as fontes de dados mockadas

**Critério de aceite:** `InnovationAgent.run()` produz ao menos 1 `InnovationProposal` válida
com tasks bem-formadas sem intervenção humana.

---

### Tarefa 7.2 — Pipeline de Análise de Dados de Uso

**Arquivo:** `aegis/innovation/analyzer.py`

**Entregáveis:**
- Classe `UsageAnalyzer` que agrega dados de múltiplas fontes:

| Fonte | Métricas Extraídas |
|---|---|
| Langfuse traces | latência p50/p99 por agente, taxa de erro, tool calls por sessão |
| Prometheus | throughput, memória, tempo de resposta ao longo do tempo |
| ChromaDB stats | tamanho do índice, hits vs misses de busca semântica |
| Neo4j stats | densidade do grafo, entidades mais conectadas |
| friction-log.md | padrões de erros recorrentes, APIs problemáticas |
| progress.txt | velocidade de desenvolvimento por fase |

- Output: `SystemHealthReport(bottlenecks, gaps, opportunities, strengths)`
- Método `identify_weakest_component() -> str` — retorna o componente com pior score
- Método `find_capability_gaps() -> list[str]` — lista funcionalidades ausentes mas pedidas
- Método `detect_recurring_errors() -> list[ErrorPattern]` — agrupa erros do friction-log
- Testes: `tests/innovation/test_analyzer.py` com dados sintéticos realistas

**Critério de aceite:** `UsageAnalyzer.run()` produz `SystemHealthReport` em < 30s com dados reais.

---

### Tarefa 7.3 — Motor de Geração de Tasks

**Arquivo:** `aegis/innovation/task_generator.py`

**Entregáveis:**
- Classe `TaskGenerator` que usa LLM (Claude) com prompt de meta-nível para transformar
  `SystemHealthReport` em `list[InnovationProposal]`
- System prompt do gerador (hardcoded em `aegis/personality/prompts.py`):
  analista de sistemas sênior que conhece toda a arquitetura AEGIS e propõe melhorias
  com formato exato de task do PRD
- Categorias de tasks que o gerador pode propor:

| Categoria | Exemplos |
|---|---|
| `PERFORMANCE` | cache de embeddings, batching, lazy loading de agentes |
| `CAPABILITY` | nova ferramenta faltante, novo agente para caso de uso detectado |
| `RELIABILITY` | melhor tratamento de erro em X, circuit breaker em Y |
| `UX` | novo comando CLI, novo painel na galáxia para métrica Z |
| `REFACTOR` | extração de código duplicado, melhoria de interface |
| `EXPERIMENT` | A/B test de modelo diferente, novo método de embedding |

- Validação de formato: task gerada deve ter todos os campos de `ProposedTask` preenchidos;
  tasks sem critério de aceite claro são descartadas automaticamente
- Deduplicação: task não é proposta se similar (cosine > 0.85) a task já existente no PRD
- Testes: `tests/innovation/test_task_generator.py`

**Critério de aceite:** gerador produz 3–8 tasks válidas e não-duplicadas por execução.

---

### Tarefa 7.4 — Sistema de Validação e Aprovação

**Arquivo:** `aegis/innovation/validator.py`

**Duas modalidades de operação (configurável em `.env`):**

**Modo `SUPERVISED` (padrão):**
- Tasks geradas são escritas em `prd_proposals.md` (arquivo separado do PRD)
- AEGIS notifica o usuário: *"Gerei N propostas de melhoria. Revise em `prd_proposals.md`
  e execute `/approve all` ou `/approve <id>` para adicionar ao PRD."*
- Usuário aprova → tasks são movidas para o PRD na Fase correta → loop executa
- Usuário rejeita com motivo → motivo é salvo no friction-log para aprendizado futuro

**Modo `AUTONOMOUS` (requer aprovação explícita para ativar):**
- Tasks são adicionadas diretamente ao PRD após validação automática
- Validação automática: score de risco < threshold configurável; sem operações irreversíveis;
  sem novos serviços externos não aprovados; complexidade estimada < 3 (escala 1–5)
- Tasks de alto risco (novas integrações pagas, mudanças de schema de banco) sempre
  requerem aprovação humana independente do modo
- Audit log completo de toda task adicionada autonomamente

**Entregáveis:**
- Classe `TaskValidator` com os dois modos
- Arquivo `prd_proposals.md` gerado automaticamente com tasks formatadas
- Comando CLI `/proposals` mostra lista pendente; `/approve <id>` aprova individualmente
- Testes: `tests/innovation/test_validator.py`

**Critério de aceite:** no modo SUPERVISED, nenhuma task chega ao PRD sem aprovação;
no modo AUTONOMOUS, tasks de baixo risco são adicionadas e executadas sem intervenção.

---

### Tarefa 7.5 — Loop de Execução Autônomo

**Arquivo:** `aegis/innovation/loop.py`

**Entregáveis:**
- Classe `InnovationLoop` — o orchestrador do ciclo eterno
- Scheduler via `APScheduler`: roda após cada fase concluída, ou a cada 72h, ou sob demanda
- Fluxo completo do loop:

```
TRIGGER (fase concluída || tempo || comando manual)
        ↓
UsageAnalyzer.run()          → SystemHealthReport
        ↓
TaskGenerator.generate()     → list[InnovationProposal]
        ↓
TaskValidator.validate()     → proposals aprovadas ou pendentes
        ↓
[SUPERVISED] → notifica usuário → aguarda aprovação
[AUTONOMOUS] → adiciona tasks ao PRD diretamente
        ↓
Agente de desenvolvimento executa nova task (§1 do prompt.md)
        ↓
Atualiza progress.txt + friction-log.md
        ↓
InnovationLoop.evaluate_impact() → compara métricas pré/pós task
        ↓
Salva resultado no histórico de inovações
        ↓
REINICIA LOOP ∞
```

- Método `evaluate_impact(task_id)`: compara `SystemHealthReport` antes e depois da task;
  calcula delta de melhoria; registra se a task foi positiva, neutra ou negativa
- Tasks que pioram métricas são revertidas automaticamente (via git revert) e o aprendizado
  é salvo no friction-log
- Dashboard de inovações: nova rota `/innovation` na API mostrando histórico de loops,
  propostas geradas, aprovadas, rejeitadas e impacto medido
- Testes: `tests/innovation/test_loop.py` — loop completo mockado end-to-end

**Critério de aceite:** loop completo roda do trigger ao evaluate_impact sem intervenção;
impacto é medido e registrado corretamente.

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
       Fases 1–7 concluídas. AEGIS agora se autodesenvove.
       Modo inicial: SUPERVISED. Para ativar AUTONOMOUS: /innovation mode autonomous
```

**Critério de aceite:** loop completo executado end-to-end; primeira proposal real gerada
e aprovada; task resultante adicionada ao PRD e executada com sucesso.

---

## ∞ MODO AUTÔNOMO — Geração Contínua de Tasks

> **Este bloco não tem fim. Quando o agente chegar aqui, não para — reinicia o Innovation Loop.**

Quando todas as tarefas das Fases 1–7 estiverem ✅:

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
