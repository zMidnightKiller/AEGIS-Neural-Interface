# PRD — AEGIS AI: Product Requirements Document
### Sistema de IA Privado, Local e Auto-Aprendente
### Hardware: RTX 3060 (12GB VRAM) + 32GB RAM

---

## ⚡ FASE ATUAL — LEIA ISTO PRIMEIRO

> **Fase ativa: FASE 2 — Sistema de Memória & RAG Próprio**
> **Próxima tarefa: Tarefa 2.6 — MemoryAgent**
> **Instruções: Consulte `prompt.md` §1 para os passos exatos de execução.**

Não varra fases anteriores. Vá direto ao próximo ❌ na fase ativa.

---

## Visão Geral por Fase

| Fase | Nome | Tarefas | Concluídas | Status |
|---|---|---|---|---|
| 0 | Fundação de Hardware & Modelo Local | 8 | 8 | ✅ Concluída |
| 1 | Core Engine, Personalidade & Resource Guard | 8 | 8 | ✅ Concluída |
| 2 | Sistema de Memória & RAG Próprio | 7 | 5 | 🔵 Ativa |
| 3 | Pipeline de Aprendizado Contínuo | 8 | 0 | ⚪ Aguardando |
| 4 | Agentes & Ferramentas Locais | 7 | 0 | ⚪ Aguardando |
| 5 | Interfaces: Web, Voz & Galaxy UI | 7 | 0 | ⚪ Aguardando |
| 6 | Produção, Escala & Observabilidade | 6 | 0 | ⚪ Aguardando |
| 7 | Innovation Loop — Autonomia Evolutiva | 6 | 0 | ⚪ Aguardando |
| ∞ | MODO AUTÔNOMO — Evolução Contínua | ∞ | — | 🔴 Inativo |

---

## Fase 0 — Fundação de Hardware & Modelo Local

> **Objetivo:** AEGIS roda e responde localmente na RTX 3060.
> Modelo Q4_K_M na GPU com latência < 3s por token.
> ResourceGuard ativo desde o primeiro boot.
> Nenhuma chamada externa durante inferência.

- ✅ Tarefa 0.1 — Setup de Ambiente GPU & Dependências
- ✅ Tarefa 0.2 — Script de Validação de Hardware
- ✅ Tarefa 0.3 — Download & Benchmark de Modelos Base
- ✅ Tarefa 0.4 — Motor de Inferência: llama.cpp com Split GPU+RAM
- ✅ Tarefa 0.5 — Pipeline de Quantização Automática
- ✅ Tarefa 0.6 — Gestão de Modelos & Hot-Swap
- ✅ Tarefa 0.7 — Embeddings Locais (nomic-embed-text)
- ✅ Tarefa 0.8 — Smoke Test Fase 0

---

### Tarefa 0.1 — Setup de Ambiente GPU & Dependências

**Arquivos:** `Makefile`, `pyproject.toml`, `docker-compose.yml`, `.env.example`

**Entregáveis:**
- CUDA toolkit verificado e compatível com PyTorch (`nvidia-smi` retorna RTX 3060, 12GB)
- `pyproject.toml` com dependências:
  `torch` (CUDA 12.x), `llama-cpp-python` (build CUDA),
  `unsloth`, `peft`, `trl`, `bitsandbytes`, `transformers`, `datasets`,
  `chromadb`, `neo4j`, `redis`, `fastapi`, `celery`,
  `structlog`, `pydantic-settings`, `tenacity`, `apscheduler`,
  `faster-whisper`, `TTS`, `typer`, `rich`,
  `pynvml`, `psutil`,
  `pytest`, `pytest-asyncio`
- `docker-compose.yml` com serviços: `redis`, `chromadb`, `neo4j`, `ollama`,
  `prometheus`, `grafana`, `searxng` — todos sem porta exposta externamente,
  todos com `mem_limit` definido para não consumir RAM ilimitada
- `Makefile`: `make setup-gpu`, `make pull-models`, `make dev`, `make test`,
  `make train`, `make benchmark`, `make docker-up`, `make docker-down`, `make status`
- `.env.example` completo conforme `AGENTS.md`

**Critério de aceite:** `make docker-up` sobe todos os serviços; `make status` mostra
GPU, VRAM livre e RAM disponível corretamente.

---

### Tarefa 0.2 — Script de Validação de Hardware

**Arquivo:** `scripts/check_hardware.py`

**Entregáveis:**
- Valida: CUDA disponível, VRAM ≥ 10GB livre, RAM ≥ 20GB livre, disco ≥ 50GB livre
- Valida versões: CUDA ≥ 12.0, PyTorch compatível, `llama-cpp-python` compilado com CUDA
- Exibe mapa de VRAM: o que cabe, o que não cabe, configuração recomendada para o hardware detectado
- Modo `--strict`: falha com código de saída 1 se qualquer requisito não for atendido
- Rodado automaticamente por `make setup-gpu` e `make dev`
- Testes: `tests/scripts/test_check_hardware.py` — hardware mockado

**Critério de aceite:** script detecta RTX 3060 12GB e recomenda `Q4_K_M`, `n_gpu_layers=28`.

---

### Tarefa 0.3 — Download & Benchmark de Modelos Base

**Arquivos:** `scripts/download_models.py`, `aegis/model/benchmark.py`

**Modelos a baixar e testar:**

| Modelo | Formato | VRAM estimada | Contexto | Uso |
|---|---|---|---|---|
| `Mistral-7B-Instruct-v0.3` | Q4_K_M GGUF | ~4.5 GB | 4096 | **Principal** |
| `LLaMA-3-8B-Instruct` | Q4_K_M GGUF | ~4.8 GB | 4096 | Alternativa |
| `Phi-3-mini-4k-instruct` | Q4_K_M GGUF | ~2.2 GB | 4096 | Fallback leve (CPU) |
| `Mistral-7B-Instruct-v0.3` | Q5_K_M GGUF | ~5.2 GB | 4096 | Alta qualidade (sem co-exec) |

**Entregáveis:**
- `scripts/download_models.py`: baixa de HuggingFace para `./models/`, verifica hash,
  retoma download interrompido
- `ModelBenchmark`: tokens/s, VRAM peak, perplexidade, qualidade PT-BR
- Suite de benchmarks: raciocínio, código Python, resposta PT-BR, instrução, function calling
- Relatório `./benchmarks/baseline_YYYY-MM-DD.json`
- Testes: `tests/model/test_benchmark.py`

**Critério de aceite:** Mistral-7B Q4_K_M ≥ 8 tok/s na 3060; benchmark salvo.

---

### Tarefa 0.4 — Motor de Inferência: llama.cpp com Split GPU+RAM

**Arquivo:** `aegis/model/inference.py`

**Entregáveis:**
- Classe abstrata `BaseInferenceEngine`:
  `async generate(prompt, max_tokens, temperature, stream) -> AsyncIterator[str]`
- `LlamaCppEngine` (primário na 3060):
  - `n_gpu_layers=28` por padrão (configurável via `AEGIS_GPU_LAYERS`)
  - `n_ctx=4096`, `n_threads=8`
  - Streaming token a token
  - Verifica VRAM via `ResourceGuard.assert_safe("inference")` antes de cada geração
  - Métricas por geração: tokens/s, VRAM peak, time-to-first-token
- `OllamaEngine` (dev): para testes rápidos sem gestão manual de modelo
- Factory `InferenceEngineFactory.create(backend) -> BaseInferenceEngine`
- Fallback automático: LlamaCpp falhou → Ollama → registra no friction-log
- Testes: `tests/model/test_inference.py` — GPU mockada

**Critério de aceite:** `LlamaCppEngine.generate("Olá")` retorna tokens PT-BR com
split GPU+RAM; ResourceGuard impede geração se VRAM > 96%.

---

### Tarefa 0.5 — Pipeline de Quantização Automática

**Arquivo:** `aegis/model/quantize.py`

**Entregáveis:**
- `QuantizationPipeline`:
  - `to_gguf(model_path, quant_type="Q4_K_M")` — padrão para 3060
  - `to_gguf(model_path, quant_type="Q5_K_M")` — para uso sem co-execução
  - `to_gguf(model_path, quant_type="Q2_K")` — fallback extremo (qualidade baixa)
- Validação pós-quantização: benchmark comparativo; qualidade não deve cair > 5%
- Script CLI: `python scripts/quantize_model.py --model llama3-8b --quant Q4_K_M`
- Testes: `tests/model/test_quantize.py` — pipeline mockado

**Critério de aceite:** Mistral-7B Q4_K_M ocupa < 5GB VRAM; benchmark ≥ 95% do Q5.

---

### Tarefa 0.6 — Gestão de Modelos & Hot-Swap

**Arquivo:** `aegis/model/loader.py`

**Entregáveis:**
- `ModelManager`: registry de modelos em `./models/`
- `load(model_id)`: verifica VRAM via ResourceGuard antes de carregar
- `swap(new_model_id)`: descarrega atual → `torch.cuda.empty_cache()` → carrega novo
- `get_active() -> ModelInfo`: modelo em uso com métricas de VRAM
- VRAM budget: impede carregar modelo que exceda `GPU_PAUSE_PCT` de ocupação
- Auto-seleção: escolhe maior modelo que cabe com folga de 1.5GB para contexto
- Testes: `tests/model/test_loader.py`

**Critério de aceite:** swap entre Mistral-7B e LLaMA-3-8B sem reiniciar; VRAM
liberada e confirmada antes do carregamento do novo modelo.

---

### Tarefa 0.7 — Embeddings Locais

**Arquivo:** `aegis/model/embedder.py`

**Entregáveis:**
- `LocalEmbedder` com `nomic-embed-text` via Ollama (~0.5GB VRAM)
- Fallback CPU: `all-MiniLM-L6-v2` via `sentence-transformers` (zero VRAM)
- Batching automático com limite de `MAX_CONCURRENT_EMBEDDINGS=2`
- Cache Redis (TTL 24h) para textos repetidos
- ResourceGuard: pausa se VRAM total (modelo + embeddings) > `GPU_PAUSE_PCT`
- Testes: `tests/model/test_embedder.py`

**Critério de aceite:** 500 documentos indexados em < 120s; fallback CPU ativo quando
VRAM está quase cheia.

---

### Tarefa 0.8 — Smoke Test Fase 0

**Entregáveis:**
- `tests/smoke/test_fase0.py`:
  1. RTX 3060 detectada com ≥ 10GB VRAM livre
  2. Modelo Q4_K_M carregado e gerando tokens PT-BR
  3. Split GPU+RAM funcionando (`n_gpu_layers=28`)
  4. Streaming token a token visível
  5. Embeddings gerados localmente
  6. ResourceGuard ativo e reportando métricas
  7. Todos os serviços Docker rodando
  8. `tcpdump` durante inferência: zero tráfego para IPs de LLM externos
- `make test` verde; tarefas 0.1–0.7 marcadas ✅
- Atualizar ponteiro `⚡ FASE ATUAL` para Fase 1

---

## Fase 1 — Core Engine, Personalidade & Resource Guard

> **Objetivo:** AEGIS tem personalidade própria, entende intenções e roteia para agentes.
> Resource Guard completo protege o hardware em todos os cenários de uso.

- ✅ Tarefa 1.1 — Core Config & Settings
- ✅ Tarefa 1.2 — Resource Guard: Implementação Completa
- ✅ Tarefa 1.3 — Core Engine: Orquestrador Principal
- ✅ Tarefa 1.4 — Core Context: Janela de Contexto com Compressão
- ✅ Tarefa 1.5 — Personalidade: System Prompts & Modos Locais
- ✅ Tarefa 1.6 — Classifier de Intenção (modelo local)
- ✅ Tarefa 1.7 — Interface CLI com Streaming & Monitor de Recursos
- ✅ Tarefa 1.8 — Smoke Test Fase 1

---

### Tarefa 1.1 — Core Config & Settings

**Arquivo:** `aegis/core/config.py`

**Entregáveis:**
- `Settings` com Pydantic Settings v2 — carrega todas as variáveis do `.env`
- Validação no startup: verifica CUDA, VRAM disponível, modelo existe em `./models/`
- Perfis: `development` (Ollama, Phi-3-mini), `production` (llama.cpp, Mistral-7B)
- Singleton `lru_cache`
- Testes: `tests/core/test_config.py`

---

### Tarefa 1.2 — Resource Guard: Implementação Completa

**Arquivo:** `aegis/core/resource_guard.py`

Esta é a tarefa de segurança mais importante do projeto.

**Entregáveis:**
- Classe `ResourceGuard` com monitoramento contínuo via `pynvml` (GPU) e `psutil` (CPU/RAM)
- Background task assíncrona: polling a cada 5s, notifica subscribers via evento
- `ResourceStatus`: snapshot com VRAM usada/livre, CPU%, RAM usada/livre, temperatura GPU
- `assert_safe(op: str)`: lança `ResourceUnsafeError` se operação não é segura agora
- `wait_for_safe(op: str, timeout_s=300)`: aguarda até seguro ou timeout
- `is_safe_for(op: str) -> bool`: check síncrono sem bloqueio
- Subscriber pattern: componentes se registram para receber alertas de limite
- Ações automáticas por nível:
  - `WARN (80% VRAM)`: log + notificação no CLI
  - `PAUSE (92% VRAM)`: pausa jobs de background (fine-tuning, ingestão)
  - `STOP (96% VRAM)`: para novas inferências não urgentes; alerta crítico
  - `EMERGENCY (>98% VRAM)`: `torch.cuda.empty_cache()` forçado + pausa total
- Temperatura GPU: aviso > 80°C, pausa background > 85°C, alerta crítico > 90°C
- Métricas Prometheus: `aegis_vram_used_bytes`, `aegis_gpu_temp_celsius`,
  `aegis_cpu_percent`, `aegis_ram_used_bytes`, `aegis_guard_pauses_total`
- Testes: `tests/core/test_resource_guard.py` — pynvml e psutil mockados

**Critério de aceite:** quando VRAM mockada a 93%, fine-tuning é pausado automaticamente
e CLI exibe alerta; quando volta a 78%, fine-tuning resume sozinho.

---

### Tarefa 1.3 — Core Engine

**Arquivo:** `aegis/core/engine.py`

**Entregáveis:**
- `Engine.process(input: UserInput) -> AgentResponse` — pipeline completo
- Verifica `ResourceGuard.assert_safe("inference")` antes de cada geração
- Pipeline: input → enriquecer com memória → construir prompt → gerar (stream) → pós-processar
- Logging: tokens usados, latência, VRAM no momento, modelo utilizado
- Testes: `tests/core/test_engine.py`

---

### Tarefa 1.4 — Core Context: Janela com Compressão

**Arquivo:** `aegis/core/context.py`

**Entregáveis:**
- Gestão de janela respeitando `AEGIS_CONTEXT_LENGTH=4096`
- Compressão automática quando janela > 80%: sumarização via modelo local
- Na 3060, contexto longo (> 3000 tokens) aumenta VRAM — ResourceGuard monitorado
- Métodos: `add_message`, `get_window`, `compress_if_needed`, `token_count`
- Testes: `tests/core/test_context.py`

---

### Tarefa 1.5 — Personalidade: System Prompts & Modos

**Arquivos:** `aegis/personality/modes.py`, `aegis/personality/prompts.py`

**Entregáveis:**
- `OperatingMode`: `STANDARD`, `BRIEFING`, `ANALYSIS`, `SILENT`, `VERBOSE`, `LEARNING`
- Templates por modelo: `[INST]...[/INST]` (Mistral), `<|user|>...<|assistant|>` (LLaMA-3)
- Modo `BRIEFING`: respostas curtas — menor consumo de tokens e VRAM
- Modo `LEARNING`: sessão marcada para coleta de dados de fine-tuning
- Testes: `tests/personality/test_prompts.py`

---

### Tarefa 1.6 — Classifier de Intenção Local

**Arquivo:** `aegis/core/classifier.py`

**Entregáveis:**
- Usa o modelo local com prompt few-shot de classificação
- Cache de classificações similares (evita re-inferência)
- Fallback por regras/keywords se VRAM próxima do limite
- Categorias: `CHAT`, `RESEARCH`, `TASK`, `CODE`, `MEMORY_QUERY`, `LEARNING_FEEDBACK`
- Testes: `tests/core/test_classifier.py`

---

### Tarefa 1.7 — Interface CLI com Monitor de Recursos

**Arquivo:** `aegis/interfaces/cli.py`

**Entregáveis:**
- REPL com Typer + Rich; streaming token a token
- **Barra de status em tempo real no rodapé:** `GPU: 45% (5.4/12GB) | CPU: 23% | RAM: 14/32GB | 11.2 tok/s`
- Alerta visual quando ResourceGuard entra em nível WARN ou PAUSE
- Comandos: `/mode`, `/model`, `/clear`, `/learn on|off`, `/memory`,
  `/status` (snapshot detalhado de recursos), `/benchmark`, `/help`, `/exit`
- Testes: `tests/interfaces/test_cli.py`

**Critério de aceite:** barra de status atualiza a cada 2s; `/status` exibe snapshot
completo incluindo temperatura da GPU.

---

### Tarefa 1.8 — Smoke Test Fase 1

**Critérios:**
- Conversa end-to-end com modelo local; streaming visível
- ResourceGuard ativo e visível na CLI
- Simulação de alta VRAM: ResourceGuard pausa corretamente
- Modo LEARNING marca sessão; modo BRIEFING gera resposta mais curta
- `make test` verde; tarefas 1.1–1.7 marcadas ✅
- Atualizar ponteiro `⚡ FASE ATUAL` para Fase 2

---

## Fase 2 — Sistema de Memória & RAG Próprio

> **Objetivo:** AEGIS lembra tudo entre sessões usando embeddings e grafos 100% locais.
> RAG com reranking local. Zero dado enviado para fora.

- ✅ Tarefa 2.1 — Pipeline de Ingestão de Documentos
- ✅ Tarefa 2.2 — Memória Episódica (ChromaDB local)
- ✅ Tarefa 2.3 — Memória Semântica (Neo4j local)
- ✅ Tarefa 2.4 — Working Memory (Redis)
- ✅ Tarefa 2.5 — RAG Engine: Retrieval Híbrido + Reranking CPU
- ❌ Tarefa 2.6 — MemoryAgent
- ❌ Tarefa 2.7 — Smoke Test Fase 2

---

### Tarefa 2.1 — Pipeline de Ingestão de Documentos

**Arquivo:** `aegis/memory/ingestion.py`

**Entregáveis:**
- `DocumentIngester`: PDF, DOCX, TXT, MD, HTML, código-fonte, imagens (OCR via `tesseract`),
  áudio (transcrição via `faster-whisper`)
- Chunking: 512 tokens, 10% overlap, respeita parágrafos
- Deduplicação via hash
- Watcher: `./data/inbox/` monitorado — novos arquivos indexados em background
- ResourceGuard: ingestão pausa se RAM > `RAM_PAUSE_GB` ou VRAM > `GPU_PAUSE_PCT`
- Máximo 1 documento processado por vez na 3060 (`MAX_CONCURRENT_EMBEDDINGS=2`)
- Testes: `tests/memory/test_ingestion.py`

---

### Tarefa 2.2 — Memória Episódica (ChromaDB)

**Arquivo:** `aegis/memory/episodic.py`

**Entregáveis:**
- `EpisodicMemory` com ChromaDB persistido em `./data/chroma/`
- Embeddings via `LocalEmbedder` (zero API externa)
- Métodos: `save_episode`, `search_similar(query, threshold=0.72, n=5)`, `get_recent(n)`
- Coleções: `conversations`, `documents`, `facts`
- Compressão de episódios > 30 dias via sumarização local
- Testes: `tests/memory/test_episodic.py`

---

### Tarefa 2.3 — Memória Semântica (Neo4j)

**Arquivo:** `aegis/memory/semantic.py`

**Entregáveis:**
- `SemanticMemory` com Neo4j Community local
- Schema: `(User)-[PREFERS|KNOWS|DISLIKES]->(Entity)`,
  `(Concept)-[RELATED_TO|PART_OF]->(Concept)`
- Extração automática de entidades via modelo local (NER prompt)
- Métodos: `save_fact`, `get_user_profile`, `update_preference`, `query_graph(cypher)`
- Testes: `tests/memory/test_semantic.py`

---

### Tarefa 2.4 — Working Memory (Redis)

**Arquivo:** `aegis/memory/working.py`

**Entregáveis:**
- Sessão atual em Redis, TTL 48h
- `checkpoint()`: persiste snapshot para recuperação após crash
- Testes: `tests/memory/test_working.py`

---

### Tarefa 2.5 — RAG Engine: Retrieval Híbrido + Reranking CPU

**Arquivo:** `aegis/memory/rag.py`

**Entregáveis:**
- Retrieval híbrido: ChromaDB (vetorial) + SQLite FTS5 (keyword)
- Reranking: `cross-encoder/ms-marco-MiniLM-L-6-v2` rodando na **CPU** (não GPU)
  para não competir com o modelo de inferência pela VRAM
- Context builder: monta documentos para injeção respeitando `AEGIS_CONTEXT_LENGTH`
- Se retrieval > 400ms: retorna resultado sem reranking e loga no friction-log
- Testes: `tests/memory/test_rag.py`

**Critério de aceite:** pergunta sobre documento ingerido → resposta factual correta;
retrieval + reranking < 600ms na 3060.

---

### Tarefa 2.6 — MemoryAgent

**Arquivo:** `aegis/agents/memory.py`

**Entregáveis:**
- Pre-interação: RAG retrieval + injeção de contexto
- Post-interação: extração de entidades → Neo4j; salva episódio → ChromaDB
- Detecção de contradição: nova info vs. grafo existente → flagga em vez de sobrescrever
- ResourceGuard: pula extração de entidades se VRAM em nível WARN
- Testes: `tests/agents/test_memory_agent.py`

---

### Tarefa 2.7 — Smoke Test Fase 2

**Critérios:**
- Ingere PDF de 30 páginas; pergunta sobre conteúdo → resposta correta
- Fato de sessão anterior é lembrado na sessão nova
- Grafo Neo4j contém entidades extraídas
- Zero chamada de rede externa durante todo o processo
- ResourceGuard não disparou nenhum alerta durante a sessão
- Atualizar ponteiro `⚡ FASE ATUAL` para Fase 3

---

## Fase 3 — Pipeline de Aprendizado Contínuo

> **Objetivo:** AEGIS aprende com uso. Fine-tuning LoRA automático na 3060.
> RLHF com DPO. Modelo melhora sem intervenção manual.
> ResourceGuard garante que treino nunca trave a máquina.

- ❌ Tarefa 3.1 — Coletor de Dados de Treino
- ❌ Tarefa 3.2 — Pipeline de Fine-Tuning Unsloth + LoRA (3060-safe)
- ❌ Tarefa 3.3 — Sistema de Feedback & RLHF com DPO
- ❌ Tarefa 3.4 — Avaliador de Qualidade Pós-Treino
- ❌ Tarefa 3.5 — Scheduler GPU-aware + ResourceGuard
- ❌ Tarefa 3.6 — Gestão de LoRA Adapters & Versionamento
- ❌ Tarefa 3.7 — Dash de Aprendizado na CLI
- ❌ Tarefa 3.8 — Smoke Test Fase 3: Primeira Melhoria Mensurável

---

### Tarefa 3.1 — Coletor de Dados de Treino

**Arquivo:** `aegis/learning/collector.py`

**Entregáveis:**
- `TrainingDataCollector`: monitora conversas, extrai pares de treino
- Formato: `{"prompt": "...", "completion": "...", "quality_score": 0.0–1.0}`
- Filtros: remove < 30 tokens, remove sessões com `/learn off`,
  remove onde usuário pediu refazer (feedback implícito negativo)
- Score de qualidade via modelo local (prompt de avaliação simples)
- SQLite em `./data/training/`
- `export_dataset(min_quality=0.65, format="alpaca") -> datasets.Dataset`
- Testes: `tests/learning/test_collector.py`

**Critério de aceite:** após 30 conversas, dataset exportado com exemplos ≥ 0.65 qualidade.

---

### Tarefa 3.2 — Pipeline de Fine-Tuning Unsloth + LoRA (3060-safe)

**Arquivo:** `aegis/learning/finetuner.py`

**Config obrigatória para caber nos 12GB:**

```python
# Configuração validada para RTX 3060 12GB
FINETUNE_CONFIG = {
    "load_in_4bit": True,           # OBRIGATÓRIO — sem isso: OOM
    "max_seq_length": 1024,         # 2048 causa OOM na 3060
    "lora_rank": 8,                  # 16 possível mas arriscado
    "lora_alpha": 16,
    "lora_dropout": 0.05,
    "batch_size": 1,                 # OBRIGATÓRIO — batch > 1: OOM
    "gradient_accumulation_steps": 8, # Simula batch=8 sem OOM
    "gradient_checkpointing": True,  # OBRIGATÓRIO
    "optim": "adamw_8bit",           # 8-bit optimizer — menos VRAM
    "fp16": True,
    "max_steps": 200,                # Por ciclo — não épocas completas
}
```

**Entregáveis:**
- `LoRAFinetuner` com Unsloth
- Verificação de VRAM antes: `guard.assert_safe("finetune")` — falha se VRAM > 85%
- Verificação de sessão ativa: recusa iniciar se `WorkingMemory.has_active_session()`
- Progresso reportado a cada 10 steps via log estruturado
- OOM handler: `torch.cuda.empty_cache()` + registro no friction-log + retry com `max_seq_length` reduzido
- Adapter salvo em `./checkpoints/lora_YYYY-MM-DD_HH-MM/`
- Estimativa de tempo: ~4–8h para 200 steps na 3060 (depende do modelo)
- Testes: `tests/learning/test_finetuner.py` — treino mockado

**Critério de aceite:** ciclo de fine-tuning completo sem OOM; adapter carregado em < 30s.

---

### Tarefa 3.3 — Sistema de Feedback & RLHF com DPO

**Arquivo:** `aegis/learning/rlhf.py`

**Entregáveis:**
- Feedback explícito: 👍/👎 na interface
- Feedback implícito: usuário editou resposta → par `(ruim, bom)` criado
- Formato DPO: `{"prompt": "...", "chosen": "...", "rejected": "..."}`
- `DPOTrainer` com `trl` — mesma config 3060-safe do fine-tuning (batch=1, 4bit)
- Threshold: mínimo 15 pares antes de ciclo RLHF (menos que o plano anterior — 3060 é mais lenta)
- Testes: `tests/learning/test_rlhf.py`

---

### Tarefa 3.4 — Avaliador de Qualidade Pós-Treino

**Arquivo:** `aegis/learning/evaluator.py`

**Entregáveis:**
- Roda automaticamente após cada ciclo de fine-tuning
- Métricas locais: perplexidade (holdout 20%), 10 perguntas PT-BR, seguimento de instrução
- Latência: tokens/s antes vs. depois (adapter não deve adicionar > 15% de overhead)
- Decisão automática: qualquer métrica caiu > 5% → rollback via `AdapterManager`
- Relatório JSON em `./benchmarks/eval_YYYY-MM-DD.json`
- Testes: `tests/learning/test_evaluator.py`

---

### Tarefa 3.5 — Scheduler GPU-aware + ResourceGuard

**Arquivo:** `aegis/learning/scheduler.py`

**Regras de disparo (TODAS devem ser verdadeiras):**
- `ResourceGuard.is_safe_for("finetune")` → true
- `WorkingMemory.has_active_session()` → false (sem sessão nos últimos 30min)
- GPU utilization < 15% nos últimos 10min
- Amostras acumuladas ≥ `AEGIS_MIN_SAMPLES_FOR_FINETUNE`
- Não rodou fine-tuning nas últimas 8h
- Hora atual entre 00h–06h (horário preferencial) OU modo manual

**Entregáveis:**
- `TrainingScheduler` com APScheduler; polling a cada 15min
- Cancela treino em andamento se usuário inicia sessão (ResourceGuard notifica)
- Notificação na CLI: "Fine-tuning iniciado. Estimativa: ~6h. Sessões disponíveis normalmente."
- Testes: `tests/learning/test_scheduler.py`

---

### Tarefa 3.6 — Gestão de LoRA Adapters & Versionamento

**Arquivo:** `aegis/learning/adapter_manager.py`

**Entregáveis:**
- Registry de adapters com metadata: data, amostras, métricas, modelo base
- `rollback(n=1)`: reverte para adapter anterior
- `compare(a, b)`: benchmark comparativo
- Retenção: últimos 5 adapters (3060 tem menos disco geralmente)
- `export_merged(adapter_id, output_path)`: merge completo para distribuição
- Testes: `tests/learning/test_adapter_manager.py`

---

### Tarefa 3.7 — Dashboard de Aprendizado na CLI

**Arquivo:** atualização em `aegis/interfaces/cli.py`

**Entregáveis:**
- Comando `/learn status`: exibe amostras coletadas, qualidade média, próximo treino agendado,
  último adapter e sua melhoria vs. baseline
- Comando `/learn history`: tabela com todos os ciclos de treino e impacto medido
- Durante fine-tuning ativo: barra de progresso na CLI com steps, loss, ETA, VRAM atual
- Testes: `tests/interfaces/test_cli_learning.py`

---

### Tarefa 3.8 — Smoke Test Fase 3

**Critérios:**
- 30+ conversas coletadas com qualidade ≥ 0.65
- Ciclo de fine-tuning completo na 3060 sem OOM
- Scheduler não disparou durante sessão ativa do usuário
- Avaliador confirmou que novo adapter não regrediu
- ResourceGuard não atingiu nível STOP durante o treino
- Atualizar ponteiro `⚡ FASE ATUAL` para Fase 4

---

## Fase 4 — Agentes & Ferramentas Locais

> **Objetivo:** Agentes especializados executam tarefas autônomas usando ferramentas locais.
> Busca web opcional via SearXNG self-hosted. ResourceGuard em cada agente.

- ❌ Tarefa 4.1 — Ferramentas Base: FileSystem, RunCode, WebFetch
- ❌ Tarefa 4.2 — Busca Web Privada: SearXNG Self-Hosted
- ❌ Tarefa 4.3 — Agentes: Base + ResearchAgent
- ❌ Tarefa 4.4 — Agentes: TaskAgent + CodeAgent
- ❌ Tarefa 4.5 — Agentes: MediaAgent (visão e áudio locais)
- ❌ Tarefa 4.6 — Engine: Roteamento Multi-Agente
- ❌ Tarefa 4.7 — Smoke Test Fase 4

---

### Tarefa 4.1 — Ferramentas Base

**Arquivos:** `aegis/tools/base.py`, `aegis/tools/file_system.py`, `aegis/tools/run_code.py`

**Entregáveis:**
- `BaseTool`: `name`, `description`, `async execute(**kwargs) -> ToolResult`
- `ToolResult(success, data, error, metadata)` — metadata inclui `vram_used_gb`, `latency_ms`
- `FileSystemTool`: restrito a `AEGIS_DATA_DIR`
- `RunCodeTool`: Docker isolado, timeout 30s, sem acesso à rede, RAM limitada a 2GB no container
- Testes para cada ferramenta

---

### Tarefa 4.2 — Busca Web Privada: SearXNG Self-Hosted

**Arquivo:** `aegis/tools/web_search.py`

**Entregáveis:**
- SearXNG no `docker-compose.yml` com `mem_limit: 512m`
- `WebSearchTool` → `SEARXNG_URL` local apenas
- `WEB_SEARCH_ENABLED=false` por padrão
- Aviso ao ativar: "Suas queries passam pelo SearXNG local mas resultados vêm de buscadores externos."
- Testes: SearXNG mockado

---

### Tarefa 4.3 — Agentes: Base + ResearchAgent

**Arquivos:** `aegis/agents/base.py`, `aegis/agents/research.py`

**Entregáveis:**
- `BaseAgent`: loop plan → execute_tool → observe → iterate (max_steps configurável)
- Cada `run()` verifica `ResourceGuard.is_safe_for("inference")` antes de cada step
- `ResearchAgent`: RAG local primeiro; web apenas se RAG insuficiente E `WEB_SEARCH_ENABLED=true`
- Testes para ambos

---

### Tarefa 4.4 — Agentes: TaskAgent + CodeAgent

**Arquivos:** `aegis/agents/task.py`, `aegis/agents/code.py`

**Entregáveis:**
- `TaskAgent`: agenda, arquivos, lembretes — local apenas
- `CodeAgent`: escreve e testa código via `RunCodeTool` (sandbox Docker)
- Ambos verificam ResourceGuard antes de steps com inferência
- Testes para ambos

---

### Tarefa 4.5 — Agentes: MediaAgent (Visão & Áudio Locais)

**Arquivo:** `aegis/agents/media.py`

**Entregáveis:**
- OCR: `tesseract` (CPU — não compete com GPU)
- Transcrição de áudio: `faster-whisper` modelo `medium` (~0.9GB VRAM)
  — ResourceGuard verifica se há VRAM disponível sem comprometer inferência
- Análise de imagem: `BLIP-2` Q4 ou `LLaVA-1.6-7B` Q4 — **só carrega se modelo principal
  estiver descarregado** (não há VRAM para ambos simultâneos na 3060)
- Testes: `tests/agents/test_media_agent.py`

---

### Tarefa 4.6 — Engine: Roteamento Multi-Agente

**Arquivo:** `aegis/core/engine.py` (atualização)

**Entregáveis:**
- Classifier de intenção aprimorado com modelo local fine-tuned
- Roteamento sem chamada externa
- ResourceGuard no início de cada pipeline de agente
- Testes: `tests/core/test_routing.py`

---

### Tarefa 4.7 — Smoke Test Fase 4

**Critérios:**
- AEGIS responde usando RAG local (sem web)
- CodeAgent escreve e executa Python no sandbox
- MediaAgent transcreve áudio localmente sem travar inferência
- Zero chamada de rede externa
- ResourceGuard não atingiu STOP em nenhuma operação
- Atualizar ponteiro `⚡ FASE ATUAL` para Fase 5

---

## Fase 5 — Interfaces: Web, Voz & Galaxy UI

> **Objetivo:** Interface visual completa. Voz 100% offline.
> Galaxy UI com anel especial de aprendizado.
> Painel de saúde do hardware integrado.

- ❌ Tarefa 5.1 — Backend: FastAPI + WebSockets + Eventos de Recursos
- ❌ Tarefa 5.2 — Voz Local: STT faster-whisper + TTS Coqui/Piper
- ❌ Tarefa 5.3 — Frontend: React Dark-Theme HUD com Monitor de Recursos
- ❌ Tarefa 5.4 — Galaxy UI: Engine Three.js + Buraco Negro
- ❌ Tarefa 5.5 — Galaxy UI: Corpos Celestes & Ativação por Eventos
- ❌ Tarefa 5.6 — Galaxy UI: HUD, Inspeção de Nós & Modo de Voz Visual
- ❌ Tarefa 5.7 — Smoke Test Fase 5

---

### Tarefa 5.1 — Backend: FastAPI + WebSockets + Eventos de Recursos

**Arquivo:** `aegis/interfaces/api.py`

**Entregáveis:**
- REST: `POST /chat`, `GET /sessions/{id}`, `GET /memory/search`,
  `PATCH /mode`, `GET /model/status`, `GET /learning/status`
- WebSocket `/ws/chat`: streaming tokens do modelo local
- WebSocket `/ws/events`: eventos de agentes usados pela Galaxy UI
- WebSocket `/ws/resources`: stream contínuo de métricas do ResourceGuard
  → alimenta barra de recursos no frontend e animações da Galaxy UI
- Testes: `tests/interfaces/test_api.py`

---

### Tarefa 5.2 — Voz Local: STT + TTS

**Arquivo:** `aegis/interfaces/voice.py`

**Entregáveis:**
- STT: `faster-whisper` modelo `medium` local; PT-BR first
- TTS: `Coqui TTS` com fallback `Piper TTS`; sem ElevenLabs
- Wake word: `openwakeword` customizável
- ResourceGuard: STT só carrega na GPU se VRAM < 75% (caso contrário roda na CPU)
- Latência alvo: < 2s do fim da fala ao primeiro token (3060 é mais lenta que 4090)
- Testes: `tests/interfaces/test_voice.py`

---

### Tarefa 5.3 — Frontend: React Dark-Theme HUD com Monitor de Recursos

**Arquivos:** `frontend/src/`

**Entregáveis:**
- React + TypeScript + Vite + Tailwind dark (navy/cyan)
- Componentes: `ChatWindow`, `MessageBubble`, `StreamingIndicator`,
  `LearningIndicator` (modo LEARNING), `ResourceBar` (VRAM, CPU, RAM, temp GPU)
- `ResourceBar` atualiza em tempo real via `/ws/resources`
- Cores: verde ≤ 70%, amarelo 70–85%, vermelho > 85%
- Painel de modelo: modelo ativo, adapter LoRA, próximo fine-tuning agendado
- Todos os assets servidos localmente pelo FastAPI (sem CDN)

---

### Tarefa 5.4 — Galaxy UI: Engine Three.js + Buraco Negro

**Arquivo:** `frontend/src/galaxy/engine.ts`

**Entregáveis:**
- Three.js WebGL renderer; câmera perspectiva; OrbitControls
- Campo de estrelas procedural (1.500 partículas — menos que 4090 para manter 60fps)
- Nebulosa procedural com ShaderMaterial
- Buraco negro: esfera negra + disco de acreção GLSL + anel ciano pulsando
- Painel de temperatura GPU integrado ao HUD: quando temp > 80°C,
  o buraco negro muda de ciano para laranja; > 85°C: vermelho
- 60fps alvo; graceful degradation para 30fps

---

### Tarefa 5.5 — Galaxy UI: Corpos Celestes & Ativação por Eventos

**Arquivo:** `frontend/src/galaxy/bodies.ts`, `frontend/src/galaxy/events.ts`

**Hierarquia orbital:**

| Anel | Raio | Tipo | Componentes |
|---|---|---|---|
| Core | 90u | Estrelas | Working Memory, Episodic Memory, Semantic Memory, RAG Engine |
| Agents | 155u | Planetas | ResearchAgent, TaskAgent, CodeAgent, MemoryAgent, MediaAgent |
| Tools | 210u | Asteroides | FileSystem, RunCode, WebSearch, Calendar |
| Learning | 260u | Cometas (cauda) | LoRA Finetuner, DPO Trainer, Evaluator, Scheduler |

**Eventos via `/ws/events`:**
- `tool_called`: partícula viaja do nó ao centro
- `learning_started`: cometa do Finetuner pulsa dourado
- `finetuning_epoch`: contador de epoch no HUD atualiza
- `resource_warn`: anel de aviso aparece ao redor do buraco negro (amarelo)
- `resource_pause`: anel vermelho + animação de pulso de emergência
- `resource_resume`: anel desaparece, sistema volta ao normal

---

### Tarefa 5.6 — Galaxy UI: HUD, Inspeção & Modo de Voz Visual

**Arquivos:** `frontend/src/galaxy/hud.tsx`, `frontend/src/galaxy/NodePanel.tsx`

**Entregáveis:**
- HUD: modo atual, GPU%, tokens/s, temp GPU, adapter LoRA ativo
- Raycasting: hover → tooltip; clique → `NodePanel` com métricas reais
- Painel do buraco negro: tokens totais, conversas, adapters treinados,
  melhoria % desde baseline, estado do ResourceGuard
- Modo de voz: buraco negro pulsa sincronizado com áudio via Web Audio API
- ResourceGuard visual: quando em PAUSE, todos os cometas do anel Learning ficam cinzas

---

### Tarefa 5.7 — Smoke Test Fase 5

**Critérios:**
- Conversa por voz 100% local (STT + LLM + TTS sem internet)
- Galaxy UI exibe eventos de agentes e fine-tuning em tempo real
- ResourceBar no HUD muda de cor quando VRAM sobe artificialmente
- Temperatura GPU reflete na cor do buraco negro
- Modo LEARNING: aura dourada ao redor do buraco negro visível
- Atualizar ponteiro `⚡ FASE ATUAL` para Fase 6

---

## Fase 6 — Produção, Escala & Observabilidade

> **Objetivo:** Sistema pronto para uso contínuo e futuro multi-usuário.
> Preparado para escalar quando hardware for atualizado.

- ❌ Tarefa 6.1 — Observabilidade Local (Prometheus + Grafana + ResourceGuard dashboard)
- ❌ Tarefa 6.2 — Multi-Usuário: Isolamento de Sessão & Perfis
- ❌ Tarefa 6.3 — Escalabilidade: Preparação para Hardware Maior
- ❌ Tarefa 6.4 — Sistema de Plugins Local
- ❌ Tarefa 6.5 — Segurança & Auditoria Local
- ❌ Tarefa 6.6 — Smoke Test Fase 6

---

### Tarefa 6.1 — Observabilidade Local

**Entregáveis:**
- Prometheus com métricas: GPU (pynvml), inferência (latência, tokens/s),
  ResourceGuard (pauses_total, current_level), fine-tuning (epochs, loss),
  memória (VRAM, RAM, ChromaDB size)
- Grafana dashboards: Hardware Health, Inference Performance, Learning Progress,
  Resource Guard Events
- Alertas locais: GPU temp > 83°C, VRAM > 90%, RAM > 28GB, fine-tuning OOM

---

### Tarefa 6.2 — Multi-Usuário

**Entregáveis:**
- Memórias isoladas por usuário (ChromaDB collections separadas)
- Modelos compartilhados; adapters LoRA por usuário (opcional)
- Auth local (username + senha, sem OAuth externo)
- ResourceGuard: limites por usuário para evitar que um usuário monopolize a GPU

---

### Tarefa 6.3 — Escalabilidade: Preparação para Hardware Maior

**Entregáveis:**
- `ModelManager` preparado para vLLM quando hardware escalar
- `make upgrade-hardware` detecta nova GPU e reconfigura automaticamente:
  - 4090 detectada → `n_gpu_layers=40`, Q5_K_M, context=8192, batch_size=4
  - A100 detectada → vLLM ativado, modelos 13B ou 70B Q4
- ResourceGuard thresholds se ajustam à nova VRAM detectada
- Fine-tuning: batch_size, max_seq_length e LoRA rank aumentam automaticamente

---

### Tarefa 6.4 — Sistema de Plugins Local

**Entregáveis:**
- Interface `LocalPlugin`: manifest + ferramenta + diretiva
- Plugins em `./plugins/`; hot-reload
- Sandbox: plugins não acessam dados de outros usuários, respeitam ResourceGuard
- Documentação: criar plugin em < 50 linhas

---

### Tarefa 6.5 — Segurança & Auditoria

**Entregáveis:**
- Log imutável append-only de ações de agentes
- Aprovação obrigatória para: deletar memórias, export de dados, ações irreversíveis
- `scripts/audit.py`: verifica checksums de modelos para detectar modificação
- Criptografia opcional de `./data/` e `./checkpoints/`

---

### Tarefa 6.6 — Smoke Test Fase 6

**Critérios:**
- 2 usuários simultâneos com memórias isoladas; ResourceGuard distribuindo recursos
- Grafana mostrando todas as métricas em tempo real
- `make upgrade-hardware` simulado: detecta nova config e reconfigura
- Atualizar ponteiro `⚡ FASE ATUAL` para Fase 7

---

## Fase 7 — Innovation Loop: Autonomia Evolutiva

> **O AEGIS observa a si mesmo, detecta onde é fraco, e propõe melhorias.**
> Usa o próprio modelo local para raciocinar sobre melhorias.
> ResourceGuard garante que o loop não monopolize o hardware.

- ❌ Tarefa 7.1 — InnovationAgent (meta-nível, modelo local)
- ❌ Tarefa 7.2 — Pipeline de Análise: Métricas + Qualidade + Recursos
- ❌ Tarefa 7.3 — Motor de Geração de Tasks (AEGIS analisa AEGIS)
- ❌ Tarefa 7.4 — Validação & Aprovação (SUPERVISED / AUTONOMOUS)
- ❌ Tarefa 7.5 — Innovation Loop com Avaliação de Impacto
- ❌ Tarefa 7.6 — Smoke Test + Ativação do Modo Autônomo

---

### Tarefa 7.1 — InnovationAgent

**Arquivo:** `aegis/agents/innovation.py`

**Entregáveis:**
- `InnovationAgent` usa o **próprio AEGIS local** para raciocinar — não Claude, não GPT
- Acesso a: Prometheus metrics, benchmark history, friction-log.md, training data stats, ResourceGuard history
- Ferramentas exclusivas: `read_metrics`, `read_benchmarks`, `read_friction_log`, `write_prd_tasks`
- **Só roda quando ResourceGuard está em nível SAFE** — nunca consome recursos durante uso normal
- Prompt calibrado para modelos 7B: direto, estruturado, exemplos concretos

---

### Tarefa 7.2 — Pipeline de Análise

**Arquivo:** `aegis/innovation/analyzer.py`

**Fontes (todas locais):**

| Fonte | Métricas |
|---|---|
| Prometheus | latência p99, throughput, GPU usage histórico |
| Benchmark history | evolução de qualidade por adapter |
| Training collector | qualidade dos dados, gaps temáticos |
| RLHF feedback | padrões de rejeição |
| Friction log | OOMs, erros recorrentes, configs que falharam |
| ResourceGuard history | frequência de PAUSEs, picos de VRAM |

**Output:** `SystemHealthReport` com seção de saúde de hardware — quantas vezes
ResourceGuard pausou operações, componentes que mais consomem VRAM.

---

### Tarefa 7.3 — Motor de Geração de Tasks

**Arquivo:** `aegis/innovation/task_generator.py`

**Categorias (específicas para IA local na 3060):**

| Categoria | Exemplos |
|---|---|
| `MODEL_QUALITY` | coletar mais dados em domínio onde modelo erra |
| `HARDWARE_OPT` | ajustar n_gpu_layers para melhor throughput medido |
| `MEMORY_EFFICIENCY` | melhorar chunking para documentos frequentes |
| `CAPABILITY` | nova ferramenta local para caso de uso detectado |
| `RESOURCE_OPT` | reduzir VRAM de componente X que causa PAUSEs frequentes |
| `TRAINING_DATA` | gerar dataset sintético para lacuna identificada |

---

### Tarefas 7.4 — 7.6

Idênticas à versão anterior com adição:
- Modo `AUTONOMOUS` só é liberado após 3 ciclos consecutivos sem necessitar correção
- Tasks de `MODEL_QUALITY` e `HARDWARE_OPT` sempre requerem aprovação humana
- Innovation Loop **verifica ResourceGuard antes de cada análise** — posterga se sistema ocupado

---

## ∞ MODO AUTÔNOMO — Evolução Contínua

> Quando todas as tarefas 0–7 estiverem ✅, não pare. Reinicie o Innovation Loop.

```
O AEGIS agora se autodesevolve usando o próprio modelo local.
Cada ciclo: analisa → propõe → valida → implementa → mede → reinicia.
ResourceGuard garante que o loop nunca interfira no uso normal.
```

**Prioridades do Modo Autônomo para RTX 3060:**

| Prioridade | Trigger | Ação |
|---|---|---|
| 🔴 CRÍTICA | ResourceGuard PAUSE > 3x/dia | Propõe otimização de VRAM do componente causador |
| 🔴 CRÍTICA | Benchmark caiu > 5% após adapter | Rollback automático + análise |
| 🟠 ALTA | RAG recall@5 < 0.75 | Melhoria de chunking ou re-embedding |
| 🟡 MÉDIA | Usuário rejeita respostas em domínio X > 30% | Coleta dados nesse domínio |
| 🟢 BAIXA | Modelo base com versão nova disponível | Propõe avaliação local |
| 🔵 EVOLUÇÃO | 1.000+ exemplos PT-BR de qualidade acumulados | Ciclo de fine-tuning dedicado |

**Limites permanentes (nunca desativados):**
- Nunca merge de adapter sem aprovação humana
- Nunca deleta checkpoints sem aprovação humana
- Nunca ativa web search sem aprovação humana
- Nenhuma chamada de inferência para serviço externo
- Máximo 1 ciclo de fine-tuning autônomo por semana (3060 leva horas)
- Innovation Loop só roda quando ResourceGuard está em SAFE há pelo menos 30min

---

## Critérios de Aceite Globais

Uma tarefa só é marcada ✅ se **todos** os critérios forem atendidos:

1. **Zero chamadas externas de inferência** — nenhum token gerado fora da máquina
2. **ResourceGuard integrado** — toda operação pesada verifica antes de executar
3. **Código completo** — zero TODOs, zero `pass` não intencionais
4. **Tipagem forte** — type hints em todas as funções e classes
5. **Testes passando** — cobertura ≥ 80%; GPU mockada em testes unitários
6. **Logging** — `structlog` em operações relevantes; zero `print()`
7. **GPU-aware** — sem operação que cause OOM sem verificação prévia
8. **Friction log** — bugs, OOMs e limitações registrados em `friction-log.md`
9. **Registrado** — linha adicionada em `progress.txt`
