# AEGIS AI (Adaptive Engineered General Intelligence System)

AEGIS é um sistema de inteligência artificial de alto desempenho projetado para operar em um ambiente de desenvolvimento estruturado. Ao contrário de chatbots genéricos, o AEGIS utiliza uma arquitetura de três camadas para garantir confiabilidade, determinismo e melhoria contínua.

## 🚀 Arquitetura em 3 Camadas

1.  **Camada de Diretivas (`directives/`)**: SOPs (Procedimentos Operacionais Padrão) escritos em Markdown que definem objetivos, entradas e lógica esperada.
2.  **Camada de Orquestração (Core)**: O motor AEGIS (`aegis/core/engine.py`) que lê diretivas, decide quais ferramentas chamar e gerencia o fluxo de trabalho.
3.  **Camada de Execução (`execution/` & `aegis/tools/`)**: Scripts Python determinísticos que realizam o trabalho pesado (busca web, manipulação de arquivos, execução de código, etc.).

## 🛠️ Stack Tecnológica

-   **Backend**: Python 3.11+, FastAPI, Celery, Redis
-   **Memória**:
    -   **Trabalho**: Redis (sessão atual)
    -   **Episódica**: ChromaDB (memória persistente de longo prazo)
    -   **Semântica**: Neo4j (grafos de conhecimento e preferências do usuário)
-   **IA**: LangChain / LlamaIndex
-   **Interfaces**: CLI, API (FastAPI) e WebSockets

## 📦 Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd Helen

# Crie um ambiente virtual e instale as dependências
python -m venv venv
source venv/bin/activate  # Ou `venv\Scripts\activate` no Windows
pip install -e .
```

## ⚙️ Configuração

Crie um arquivo `.env` na raiz baseado no `.env.example`:

```env
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
TAVILY_API_KEY=your_key
REDIS_URL=redis://localhost:6379
CHROMA_PERSIST_DIR=./data/chroma
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_password
```

## 🚀 Como Executar

### CLI (Interface de Linha de Comando)
```bash
python aegis/interfaces/cli.py
```

### API Backend (FastAPI)
```bash
python aegis/interfaces/api.py
```
Acesse a documentação interativa em: `http://localhost:8000/docs`

### Docker
```bash
docker-compose up -d
```

## 🧪 Testes

Para rodar a suite de testes completa:
```bash
pytest tests/
```

## 📖 Documentação Adicional

-   [Guia de Extensão](docs/extension_guide.md): Saiba como criar novos Agentes, Ferramentas e Plugins.
-   [Registro de Atrito (Friction Log)](friction-log.md): Histórico de problemas resolvidos e lições aprendidas.
-   [PRD](PRD.md): Documento de Requisitos de Produto e Roadmap.

---
*AEGIS: The orchestration layer between human intent and deterministic execution.*
