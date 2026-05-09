# friction-log.md — Registro de Atrito do Projeto AEGIS
### Hardware: RTX 3060 (12GB VRAM) + 32GB RAM

> **Memória institucional.** Cada iteração é amnésica — este arquivo salva a próxima
> de repetir o OOM que quebrou esta. Leia antes de iniciar qualquer tarefa de GPU.
>
> **Quando registrar:** OOM, degradação por quantização, ResourceGuard atingindo STOP,
> config de fine-tuning que falhou, latência fora do esperado, decisão arquitetural que mudou.
>
> Append-only. Nunca edite entradas anteriores.

---

## Formato de Entrada

```
## [DATA] TAREFA-ID — Título

**Hardware:** RTX 3060 12GB / CUDA X.X / PyTorch X.X
**Modelo:** nome, formato
**VRAM no momento:** X.XGB / 12GB
**ResourceGuard nível:** SAFE | WARN | PAUSE | STOP
**Contexto:** O que estava sendo implementado.
**Problema:** O que quebrou.
**Causa raiz:** Por quê.
**Solução:** O que resolveu.
**Config final que funciona:** (parâmetros se relevante)
**Impacto futuro:** Quais tarefas devem consultar esta entrada.
```

---

## Entradas

*(Nenhuma ainda — projeto em setup inicial.)*

---

## Índice por Componente

| Componente | Problema | Entrada |
|---|---|---|
| *(vazio)* | *(vazio)* | *(vazio)* |

---

## Mapa de VRAM — RTX 3060 (12GB)

> Preencher conforme componentes são implementados.
> **Regra de ouro:** inferência (4.5GB) + embeddings (0.5GB) + whisper (0.9GB) = ~6GB → 6GB livres para contexto.
> Fine-tuning usa até 10.8GB no peak — exige descarregar tudo o mais antes.

| Componente | Modelo/Config | VRAM Idle | VRAM Peak | Co-execução segura |
|---|---|---|---|---|
| Inferência Mistral-7B | Q4_K_M, n_gpu_layers=28 | ~4.5 GB | ~5.8 GB | ✅ com embeddings + whisper |
| Inferência Mistral-7B | Q5_K_M, n_gpu_layers=28 | ~5.2 GB | ~6.5 GB | ⚠️ sem whisper simultaneamente |
| Inferência LLaMA-3-8B | Q4_K_M, n_gpu_layers=28 | ~4.8 GB | ~6.1 GB | ✅ com embeddings |
| Inferência Phi-3-mini | Q4_K_M, n_gpu_layers=32 | ~2.2 GB | ~3.0 GB | ✅ fallback leve |
| nomic-embed-text | via Ollama | ~0.5 GB | ~1.2 GB | ✅ com qualquer 7B Q4 |
| faster-whisper medium | CTranslate2 | ~0.9 GB | ~1.4 GB | ✅ com Q4_K_M |
| faster-whisper large-v2 | CTranslate2 | ~1.5 GB | ~2.2 GB | ⚠️ apertado com Q4 |
| Document Ingester | Text/PDF/DOCX | ~0.0 GB | ~0.1 GB | ✅ Seguro com co-execução |
| Document Ingester | Audio (Whisper) | ~0.9 GB | ~1.4 GB | ✅ Igual ao whisper solo |
| LoRA Fine-tuning | Mistral-7B, batch=1, seq=1024 | ~8.0 GB | ~10.8 GB | ❌ SOZINHO — descarregar tudo |
| LoRA Fine-tuning | Mistral-7B, batch=1, seq=512 | ~6.5 GB | ~8.5 GB | ❌ SOZINHO |
| LLaVA multimodal | Q4_K_M | ~9.0 GB | ~11.5 GB | ❌ SOZINHO — sem modelo texto |
| LLaMA-3-13B (split) | Q4_K_M, n_gpu_layers=20 | ~8.0 GB | ~10.5 GB | ❌ sem co-exec |

### Config de Fine-Tuning Validada para 3060

```python
# Esta config não causa OOM na RTX 3060 12GB
# NÃO altere sem testar e registrar resultado no friction-log
{
    "load_in_4bit": True,             # OBRIGATÓRIO
    "max_seq_length": 1024,           # 2048 → OOM (registrar se testado)
    "lora_r": 8,                      # 16 possível mas arriscado
    "lora_alpha": 16,
    "per_device_train_batch_size": 1, # OBRIGATÓRIO
    "gradient_accumulation_steps": 8,
    "gradient_checkpointing": True,   # OBRIGATÓRIO
    "optim": "adamw_8bit",
    "fp16": True,
    "max_steps": 200,
}
# Estimativa de tempo: 4–8h para 200 steps na 3060
# VRAM peak observado: ~10.8GB
```

---

## Decisões de Arquitetura Registradas

### Setup Inicial (RTX 3060)

**Motor de inferência:** `llama.cpp` via `llama-cpp-python` (primário), não vLLM.
Motivo: vLLM requer GPU com mais VRAM para ser eficiente; na 3060, llama.cpp com split
GPU+RAM é mais estável e flexível. vLLM será avaliado quando hardware escalar.

**n_gpu_layers=28:** 28 de ~32 camadas do Mistral-7B na GPU, restante na RAM.
Com 32GB RAM, o overflow é rápido o suficiente para uso normal (~8 tok/s).
Ajustar para 25 se houver instabilidade; aumentar para 30 se VRAM permitir.

**Modelo base:** Mistral-7B-Instruct-v0.3 Q4_K_M.
Motivo: melhor instruction-following em 7B; contexto 32k (limitado a 4096 na prática);
boa performance PT-BR; Q4_K_M cabe confortavelmente com folga de ~6GB para contexto.

**LoRA rank=8 em vez de 16:** 3060 tem VRAM apertada para fine-tuning.
rank=8 com gradient_checkpointing e batch=1 resulta em ~10.8GB peak — seguro.
rank=16 pode funcionar mas está no limite — registrar resultado se testado.

**Reranker na CPU:** `cross-encoder/ms-marco-MiniLM-L-6-v2` roda na CPU para não
competir com o modelo de inferência pela VRAM limitada da 3060.

**Whisper modelo medium:** large-v2 (~1.5GB VRAM) é apertado quando combinado com
Mistral-7B Q4 (~4.5GB). medium (~0.9GB) é o equilíbrio correto na 3060.

**ResourceGuard thresholds:** 80% warn / 92% pause / 96% stop.
Na 3060, 96% = ~11.5GB usados de 12GB — margem de ~500MB antes de OOM.
Calibrados conservadoramente para evitar crashes em operações de contexto longo.

---

## Limitações Conhecidas das Bibliotecas na 3060

| Biblioteca | Limitação | Workaround |
|---|---|---|
| `llama-cpp-python` | Compilação CUDA requer flags específicos | `CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python --no-cache-dir` |
| `unsloth` | Requer PyTorch específico; verificar tabela de compatibilidade | Consultar README do unsloth antes de instalar |
| `bitsandbytes` | Versão deve ser compatível com CUDA instalado | Verificar `bnb-cuda` na página de releases |
| `vLLM` | Não recomendado na 3060 — overhead de VRAM alto | Usar llama.cpp; migrar para vLLM ao escalar hardware |
| `faster-whisper large-v2` | 1.5GB VRAM — apertado com Mistral-7B Q4 | Usar `medium` (0.9GB) na 3060 |

## [2026-05-08 21:09] TAREFA 2.5 — RAG Reranking Skipped
**Hardware:** RTX 3060 12GB VRAM
**Contexto:** Busca híbrida RAG.
**Problema:** Retrieval demorou 505.63ms (>400ms).
**Solução:** Reranking cancelado para evitar latência excessiva.

## [2026-05-08 21:10] TAREFA 2.5 � RAG Engine

**Hardware:** RTX 3060 12GB VRAM / CPU
**Modelo:** cross-encoder/ms-marco-MiniLM-L-6-v2
**VRAM no momento:** 0GB (For�ado na CPU)
**ResourceGuard n�vel:** SAFE
**Contexto:** Implementa��o do Reranking do RAG.
**Problema:** Reranking pode competir com modelo LLM por VRAM.
**Solu��o:** CrossEncoder inicializado for�adamente com device='cpu' para proteger os 12GB da 3060 para infer�ncia.
**Impacto futuro:** Reranking na CPU introduz lat�ncia, timeout de 400ms implementado para abortar reranking e manter tempo de resposta da interface.

## [2026-05-08 21:28] TAREFA-3.2 - OOM no Fine-Tuning
**Hardware:** RTX 3060 12GB VRAM
**Contexto:** Treino LoRA com max_seq_length=1024
**Problema:** OutOfMemoryError durante SFTTrainer.train()
**Causa raiz:** batch_size ou max_seq_length estourou VRAM de 12GB.
**Solução:** Capturado try/except com torch.cuda.empty_cache(). Necessário reduzir max_seq_length e tentar de novo.

## [2026-05-08 21:31] TAREFA-3.3 - RLHF DPO Memory Requirements
**Hardware:** RTX 3060 12GB VRAM
**Contexto:** DPO Trainer com batch=1 e load_in_4bit=True
**Problema:** DPO exige processar prompt, chosen e rejected na memória.
**Solução:** Reutilizado o padrão de batch=1, gradient_checkpointing=True e rank=8 validado no Tarefa-3.2 para garantir operação segura na 3060.

## [2026-05-09 10:07] TAREFA 3.6 - Gest�o de Adapters
**Hardware:** RTX 3060 12GB VRAM
**Modelo:** LoRA Adapters
**VRAM no momento:** 0GB (Disk/CPU-bound)
**Contexto:** Implementa��o do AdapterManager.
**Solu��o:** Implementado sistema de registro e reten��o (max 5) para economizar disco e VRAM.
**Impacto futuro:** Permite rollback autom�tico em caso de degrada��o de qualidade detectada pelo Evaluator.
