import os

prd_path = r"c:\Users\luanl\.gemini\Helen\PRD.md"

with open(prd_path, "rb") as f:
    content = f.read()

# Substituir o cabeçalho (Fase ativa)
# Note: Usando busca por partes para evitar problemas com caracteres especiais
content = content.replace(b"Fase ativa: FASE 5", b"Fase ativa: FASE 6")
content = content.replace(b"Pr\xef\xbf\xbdxima tarefa: Tarefa 5.4", b"Pr\xef\xbf\xbdxima tarefa: Tarefa 6.1")

# Substituir a tabela de resumo
content = content.replace(b"| 5 | Produ\xef\xbf\xbd\xef\xbf\xbdo & Observabilidade | 6 | 0 | \xef\xbf\xbd\xef\xbf\xbd Aguardando |", 
                          b"| 5 | Produ\xef\xbf\xbd\xef\xbf\xbdo & Observabilidade | 6 | 6 | \xe2\x9c\x85 Conclu\xef\xbf\xbd\xef\xbf\xbd|")

# Substituir as tarefas
content = content.replace(b"\xef\xbf\xbd?O Tarefa 5.4", b"\xe2\x9c\x85 Tarefa 5.4")
content = content.replace(b"\xef\xbf\xbd?O Tarefa 5.5", b"\xe2\x9c\x85 Tarefa 5.5")
content = content.replace(b"\xef\xbf\xbd?O Tarefa 5.6", b"\xe2\x9c\x85 Tarefa 5.6")

with open(prd_path, "wb") as f:
    f.write(content)
