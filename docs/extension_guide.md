# Guia de Extensão do AEGIS

O AEGIS foi projetado para ser modular. Você pode estendê-lo adicionando novos Agentes, Ferramentas ou Plugins.

## 🛠️ Criando uma Nova Ferramenta (Tool)

As ferramentas são scripts determinísticos que executam uma tarefa específica.

1.  Crie um novo arquivo em `aegis/tools/minha_ferramenta.py`.
2.  Estenda a classe `BaseTool`.

```python
from aegis.tools.base import BaseTool, ToolResult

class MinhaFerramenta(BaseTool):
    name: str = "nome_da_ferramenta"
    description: str = "Descricao do que a ferramenta faz."

    async def execute(self, param1: str) -> ToolResult:
        try:
            # Sua logica aqui
            resultado = f"Processado: {param1}"
            return ToolResult(success=True, data=resultado, error=None, metadata={})
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e), metadata={})
```

## 🤖 Criando um Novo Agente (Agent)

Agentes usam ferramentas para resolver tarefas complexas.

1.  Crie um novo arquivo em `aegis/agents/meu_agente.py`.
2.  Estenda a classe `BaseAgent`.

```python
from aegis.agents.base import BaseAgent, AgentResult
from aegis.tools.minha_ferramenta import MinhaFerramenta

class MeuAgente(BaseAgent):
    name: str = "meu_agente"
    description: str = "Responsavel por tarefas X."
    max_steps: int = 5

    def get_tools(self):
        return [MinhaFerramenta()]

    async def run(self, task: str, context: Context) -> AgentResult:
        # Loop de planejamento e execucao
        ...
```

## 🔌 Sistema de Plugins

Plugins permitem adicionar funcionalidades ao sistema AEGIS com suporte a carregamento dinâmico (hot-reload).

1.  Crie um diretório para seu plugin em `plugins/meu-plugin/`.
2.  Adicione um `manifest.json` e o código do plugin estendendo `BasePlugin`.

```python
from aegis.plugins.base import BasePlugin

class MeuPlugin(BasePlugin):
    async def on_load(self):
        print(f"Plugin {self.manifest.name} carregado!")

    async def on_unload(self):
        print(f"Plugin {self.manifest.name} descarregado!")
```

## 🧪 Testando sua Extensão

Sempre crie testes para suas extensões em `tests/`.
-   Para ferramentas: `tests/tools/test_minha_ferramenta.py`
-   Para agentes: `tests/agents/test_meu_agente.py`

Execute os testes com:
```bash
pytest tests/path/to/your/test.py
```
