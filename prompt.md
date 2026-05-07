# prompt.md — Manual de Execução do Agente AEGIS

> Injetado em cada iteração. Leia do início ao fim antes de tocar em qualquer arquivo.
> **Uma tarefa por iteração.** Isso não é sugestão — é o que impede falhas em cascata.

---

## §0 — Estrela Guia Arquitetônica

Estes são os princípios que nunca mudam. Quando qualquer decisão parecer ambígua, volte aqui.

**Responsabilidade única.** Cada arquivo tem uma função. `engine.py` orquestra; `web_search.py` busca; `config.py` lê ambiente. Nenhum arquivo faz duas coisas.

**Async-first.** Toda operação de I/O é `async/await`. Sem `requests` — use `httpx`. Sem `time.sleep` — use `asyncio.sleep`.

**Dependências externas são mockadas em testes.** Tavily, Redis, ChromaDB, Neo4j, ElevenLabs — todos mockados com `AsyncMock`. Testes unitários não fazem chamadas de rede.

**Credenciais vivem em `.env`.** Nunca hardcoded. Nunca em comentários. Nunca em logs.

**Erros são esperados.** Capture exceções específicas. Trate rate limits, timeouts e respostas malformadas. O sistema deve degradar graciosamente, não explodir.

**O friction-log é memória institucional.** Cada iteração é amnésica — `friction-log.md` é o que a iteração N+50 sabe sobre o que quebrou na iteração N. Registre tudo que quebrou e como foi resolvido.

---

## §1 — Loop Principal (12 Passos)

Execute estes passos em ordem. Sem pular. Sem reordenar.

```
Passo  1  →  Ler AGENTS.md            (identidade, arquitetura, princípios)
Passo  2  →  Ler PRD.md §⚡           (identificar a fase ativa e a próxima tarefa ❌)
Passo  3  →  Ler progress.txt         (o que foi feito; detectar inconsistências)
Passo  4  →  Ler friction-log.md      (bugs conhecidos; não repita os mesmos erros)
Passo  5  →  Confirmar escopo         (1 frase: "Vou implementar X que faz Y")
Passo  6  →  Verificar execution/     (existe script reutilizável? use-o)
Passo  7  →  Verificar aegis/         (existe código parcial? leia antes de escrever)
Passo  8  →  Implementar              (§2 — padrões de código obrigatórios)
Passo  9  →  Testar                   (make test; se falhar, corrija antes de continuar)
Passo 10  →  Autoavaliação adversarial (§1.1 — repita até 0 violações)
Passo 11  →  Atualizar PRD.md         (❌ → ✅; atualizar ponteiro ⚡ se fase concluída)
Passo 12  →  Registrar progress.txt   (§5 — formato obrigatório)
```

Se PRD.md e progress.txt estiverem em conflito (tarefa marcada ✅ sem entrada no log), **trate como incompleta** e re-execute.

---

## §1.1 — Autoavaliação Adversarial

Após implementar, releia seu próprio trabalho como um revisor hostil que quer reprovar o PR.
Execute a checklist abaixo. Se qualquer item for ❌, corrija e recomece a checklist do zero.
Repita até que todos os itens sejam ✅. Máximo de 3 rodadas — se ainda houver violações na 3ª, registre em `friction-log.md` e marque a tarefa como `⚠️ PARCIAL`.

### Código
- [ ] Zero TODOs ou `pass` não intencionais?
- [ ] Todas as funções e métodos têm type hints?
- [ ] Todas as classes e métodos públicos têm docstring?
- [ ] `structlog` usado em todas as operações relevantes? (zero `print()`)
- [ ] Exceções capturadas especificamente? (zero `except Exception: pass`)
- [ ] Zero credenciais hardcoded?
- [ ] Toda operação de I/O é `async/await`?
- [ ] Imports não utilizados removidos?

### Testes
- [ ] Happy path coberto?
- [ ] Falha esperada testada (exceção correta é levantada)?
- [ ] Edge case testado (vazio, limite, timeout)?
- [ ] Todas as APIs externas mockadas com `AsyncMock`?
- [ ] `make test` passa sem warnings?

### Integração
- [ ] O componente é importado de onde deveria ser?
- [ ] Arquivos existentes que precisavam de mudança foram atualizados?
- [ ] A mudança não quebrou testes existentes?

### Perguntas difíceis
- [ ] Um engenheiro lendo isso em 6 meses vai entender o que faz e por quê?
- [ ] O que acontece se Redis/ChromaDB/Neo4j estiver fora do ar? Degrada graciosamente?
- [ ] Existe algum caso de uso óbvio não coberto pelos testes?
- [ ] A API externa pode retornar um formato inesperado que quebraria o código?

**Contagem de violações nesta rodada:** ___
*Se > 0, corrija tudo e recomece a checklist.*

---

## §2 — Padrões de Código

### Estrutura de Módulo

```python
"""
aegis/tools/web_search.py

Ferramenta de busca web via Tavily API.
Retorna resultados ranqueados com título, URL, snippet e score de relevância.
"""
from __future__ import annotations

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from aegis.tools.base import BaseTool, ToolResult
from aegis.core.config import settings

logger = structlog.get_logger(__name__)


class WebSearchTool(BaseTool):
    """Busca informações em tempo real na web via Tavily API."""

    name: str = "web_search"
    description: str = (
        "Busca informações atuais na internet. "
        "Use para fatos recentes, notícias ou dados em tempo real."
    )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=8))
    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        """
        Executa busca web.

        Args:
            query: Termos de busca em linguagem natural.
            num_results: Número de resultados (1–10).

        Returns:
            ToolResult com lista de resultados ou mensagem de erro.
        """
        logger.info("web_search.executing", query=query, num_results=num_results)
        try:
            # implementação real aqui
            ...
        except RateLimitError as e:
            logger.warning("web_search.rate_limit", error=str(e))
            return ToolResult(success=False, data=None, error=f"Rate limit: {e}", metadata={})
        except TimeoutError as e:
            logger.warning("web_search.timeout", error=str(e))
            return ToolResult(success=False, data=None, error=f"Timeout: {e}", metadata={})
```

### Estrutura de Agente

```python
class ResearchAgent(BaseAgent):
    """Pesquisa profunda em múltiplas fontes web."""

    name = "research"
    description = "Use para perguntas factuais, análises de mercado e pesquisa acadêmica."
    max_steps = 5

    def get_tools(self) -> list[BaseTool]:
        return [WebSearchTool(), WebFetchTool()]

    async def run(self, task: str, context: Context) -> AgentResult:
        logger.info("research_agent.started", task=task[:120])
        # plan → execute_tool → observe → iterate
        ...
```

### Estrutura de Teste

```python
# tests/tools/test_web_search.py
import pytest
from unittest.mock import AsyncMock, patch
from aegis.tools.web_search import WebSearchTool
from aegis.tools.base import ToolResult


@pytest.fixture
def tool() -> WebSearchTool:
    return WebSearchTool()


class TestWebSearchTool:
    async def test_returns_results_on_valid_query(self, tool: WebSearchTool) -> None:
        with patch("aegis.tools.web_search.tavily_client") as mock:
            mock.search = AsyncMock(return_value={"results": [{"title": "x", "url": "y"}]})
            result = await tool.execute("Python async patterns")
        assert result.success is True
        assert len(result.data) > 0

    async def test_returns_error_on_rate_limit(self, tool: WebSearchTool) -> None:
        with patch("aegis.tools.web_search.tavily_client") as mock:
            mock.search = AsyncMock(side_effect=RateLimitError("quota exceeded"))
            result = await tool.execute("any query")
        assert result.success is False
        assert "rate limit" in result.error.lower()

    async def test_handles_empty_query(self, tool: WebSearchTool) -> None:
        result = await tool.execute("")
        assert result.success is False
        assert result.error is not None
```

---

## §3 — Interfaces Ancoradas (Contratos Imutáveis)

> Estas assinaturas não mudam sem decisão explícita registrada em `friction-log.md`.
> Cole-as diretamente — não as reimplemente de memória.

### BaseTool

```python
class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult: ...
```

### ToolResult

```python
@dataclass
class ToolResult:
    success: bool
    data: Any
    error: str | None
    metadata: dict
```

### BaseAgent

```python
class BaseAgent(ABC):
    name: str
    description: str
    max_steps: int = 5

    @abstractmethod
    def get_tools(self) -> list[BaseTool]: ...

    @abstractmethod
    async def run(self, task: str, context: Context) -> AgentResult: ...
```

### AgentResult

```python
@dataclass
class AgentResult:
    success: bool
    output: str
    steps_taken: int
    tools_used: list[str]
    error: str | None
```

### UserInput / AgentResponse

```python
@dataclass
class UserInput:
    text: str
    session_id: str
    mode: OperatingMode = OperatingMode.STANDARD
    attachments: list[str] = field(default_factory=list)

@dataclass
class AgentResponse:
    text: str
    agent_used: str
    tools_used: list[str]
    memory_injected: bool
    latency_ms: int
```

---

## §4 — Biblioteca de Componentes

Use estas bibliotecas. Não substitua sem justificativa registrada em `friction-log.md`.

| Necessidade | Biblioteca | Nota |
|---|---|---|
| HTTP async | `httpx` | nunca `requests` |
| Validação | `pydantic v2` | `BaseModel` |
| Config/env | `pydantic-settings` | `BaseSettings` |
| Logging | `structlog` | nunca `print()` |
| CLI | `typer` + `rich` | REPL interativo |
| LLM calls | `anthropic` | `AsyncAnthropic` |
| Orquestração | `langchain` | avaliar LlamaIndex na Fase 2 |
| Retry | `tenacity` | backoff exponencial |
| Embeddings | `openai` → fallback `sentence-transformers` | conforme config |
| Vector store | `chromadb` | cliente async |
| Graph DB | `neo4j` | `AsyncGraphDatabase` |
| Redis | `redis.asyncio` | nunca `redis` síncrono |
| Testes | `pytest` + `pytest-asyncio` | `@pytest.mark.asyncio` |
| Mock | `unittest.mock` | `AsyncMock` para coroutines |
| Task queue | `celery` | broker Redis |
| API | `fastapi` | com `uvicorn` |
| WS | `fastapi` built-in | `WebSocket` |

---

## §5 — Procedimento de Registro no friction-log.md

Quando você encontrar qualquer um dos seguintes, registre **imediatamente** em `friction-log.md` antes de continuar:

- Limitação de API não documentada (rate limit, quota, formato inesperado)
- Bug que levou mais de 1 tentativa para corrigir
- Incompatibilidade entre bibliotecas
- Comportamento de serviço externo diferente do esperado (Redis, ChromaDB, Neo4j)
- Decisão de arquitetura que mudou durante a implementação
- Qualquer coisa que faria a próxima iteração perder tempo repetindo o mesmo erro

**Formato de entrada no friction-log:**
```
## [DATA] TAREFA-ID — Título curto do problema

**Contexto:** O que estava sendo implementado.
**Problema:** O que quebrou ou surpreendeu.
**Causa raiz:** Por que aconteceu.
**Solução:** O que resolveu.
**Impacto futuro:** Quais tarefas futuras devem consultar esta entrada.
```

---

## §6 — Formato de Entrada em progress.txt

Cada iteração adiciona **uma linha** ao final de `progress.txt`:

```
[YYYY-MM-DD HH:MM] ✅ Tarefa X.Y — Nome da Tarefa (adversarial: N rodadas, V violações corrigidas)
```

Exemplos:
```
[2025-06-01 14:32] ✅ Tarefa 1.1 — Configuração do Projeto (adversarial: 1 rodada, 0 violações)
[2025-06-01 16:45] ✅ Tarefa 1.2 — Core: Config (adversarial: 2 rodadas, 4 violações corrigidas)
[2025-06-02 09:10] ⚠️ Tarefa 1.3 — Core: Engine (adversarial: 3 rodadas, PARCIAL — ver friction-log entrada 2025-06-02)
```

Quando uma fase inteira for concluída, adicione linha de resumo:
```
[2025-06-05 18:00] 🏁 FASE 1 CONCLUÍDA — 9/9 tarefas — MVP funcional via CLI
```

---

## §7 — Regras Rígidas

### NUNCA sem confirmação explícita do usuário:
- Deletar arquivos fora de `.tmp/`
- Executar `git push`
- Enviar e-mails ou notificações reais
- Chamar APIs pagas em volume (>10 embeddings, TTS em loop, geração de imagem em batch)
- Sobrescrever `directives/` — apenas adicionar conteúdo

### SEMPRE:
- `make test` antes de declarar qualquer tarefa concluída
- Arquivos intermediários em `.tmp/` — nunca na raiz
- Credenciais em `.env` — nunca no código
- Atualizar PRD.md (❌ → ✅) ao concluir
- Adicionar linha em `progress.txt` ao concluir
- Registrar no `friction-log.md` qualquer problema não trivial

### Uma tarefa por iteração:
Um erro na tarefa 3 não pode corromper o trabalho das tarefas 1 e 2.
Se a tarefa for grande demais, quebre em subtarefas (1.X.1, 1.X.2) e execute a primeira.

### Se encontrar um erro:
1. Leia o stack trace completo
2. Corrija o código
3. Teste novamente
4. Registre em `friction-log.md`
5. Só escale ao usuário se envolver operação irreversível ou ambiguidade de requisito real

---

## §8 — Casos Especiais

**Tarefa grande demais:** Quebre em `X.Y.1`, `X.Y.2`, adicione ao PRD, execute a primeira.

**Dependência indisponível** (ex: Neo4j não está rodando): Marque como `⚠️` no PRD com nota. Implemente com mock/stub documentado. Continue para a próxima tarefa desbloqueada. Registre em `friction-log.md`.

**Conflito PRD × AGENTS.md:** AGENTS.md ganha. Atualize o PRD para refletir e registre a decisão.

**Débito técnico descoberto em tarefa ✅:** Adicione nova tarefa ao PRD na seção "Refatoração". Não desfaça o ✅ original — débito é separado da entrega.

**Violações persistentes após 3 rodadas adversariais:** Marque como `⚠️ PARCIAL`, registre o que falta em `friction-log.md`, continue para próxima tarefa.

---

## §9 — Innovation Loop: Comportamento no Modo Autônomo

Esta seção entra em vigor quando o ponteiro `⚡ FASE ATUAL` do PRD apontar para `∞ MODO AUTÔNOMO`.

### O que muda no loop de 12 passos

Os passos 1–4 (leitura de arquivos) permanecem idênticos. O passo 5 muda:

**Passo 5 no Modo Autônomo:**
```
Se PRD não tem tasks ❌ pendentes:
  → Não pare. Execute: InnovationLoop.trigger()
  → Aguarde SystemHealthReport
  → Leia proposals em prd_proposals.md (modo SUPERVISED)
    ou verifique tasks adicionadas automaticamente (modo AUTONOMOUS)
  → Selecione a task de maior prioridade aprovada
  → Continue do Passo 6 normalmente
```

### Como avaliar uma InnovationProposal antes de executar

Antes de executar qualquer task gerada autonomamente, responda:

- [ ] A task tem critério de aceite claro e verificável?
- [ ] A estimativa de complexidade é ≤ 3 (escala 1–5)?
- [ ] Não introduz serviço pago novo sem aprovação?
- [ ] Não modifica schema de banco de produção?
- [ ] Não altera `AGENTS.md`, `prompt.md` ou `PRD.md` estruturalmente?
- [ ] O risco de regressão é baixo (não toca em componentes críticos sem testes)?

Se qualquer resposta for NÃO → escale para aprovação humana via notificação. Não execute.

### Registro especial no progress.txt para tasks autônomas

```
[YYYY-MM-DD HH:MM] 🤖 AUTO Tarefa X.Y — Nome (gerada: InnovationLoop ciclo N | aprovada: AUTONOMOUS/human | impacto: +12% latência p99)
```

### Regra de rollback automático

Se após execução de task autônoma:
- `UsageAnalyzer` detectar degradação > 10% em qualquer métrica crítica
- `make test` falhar em módulo previamente verde

→ Execute `git revert HEAD` automaticamente
→ Registre em friction-log com categoria `AUTONOMOUS_ROLLBACK`
→ Marque task como ❌ novamente no PRD
→ Adicione nota: "Revertida automaticamente — ver friction-log [DATA]"
→ Não tente a mesma abordagem novamente sem aprovação humana

### Nunca no Modo Autônomo (limites absolutos)

Mesmo com `AUTONOMOUS` ativado, estas ações **sempre** requerem aprovação humana:
- `git push` para qualquer remote
- Envio de e-mail, SMS ou notificação para endereços reais
- Chamadas a APIs pagas em volume (> 50 requests em batch)
- Alteração de arquivos de governança: `AGENTS.md`, `prompt.md`, `PRD.md`, `friction-log.md`
- Criação de novos serviços no `docker-compose.yml`
- Qualquer operação que não possa ser revertida em < 60 segundos
