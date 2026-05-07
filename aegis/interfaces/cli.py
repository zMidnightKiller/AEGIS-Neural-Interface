"""
aegis/interfaces/cli.py

Interface de Linha de Comando (CLI) para interação com o AEGIS.
Utiliza Typer para comandos e Rich para uma interface visual premium.
"""
from __future__ import annotations

import asyncio
import uuid
import sys
from typing import Optional

import typer
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table

from aegis.core.engine import Engine
from aegis.core.models import UserInput, OperatingMode, AgentResponse
from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)
console = Console()
app = typer.Typer(help="AEGIS AI - Terminal Interface")

class AEGISCLI:
    """Gerenciador da interface REPL do AEGIS."""

    def __init__(self) -> None:
        self.engine = Engine()
        self.settings = get_settings()
        self.session_id = str(uuid.uuid4())
        self.mode = OperatingMode(self.settings.AEGIS_MODE)
        self.is_running = True

    def display_header(self) -> None:
        """Exibe o cabeçalho inicial do AEGIS."""
        table = Table(show_header=False, border_style="bold blue")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("SYSTEM", "AEGIS AI [ACTIVE]")
        table.add_row("VERSION", self.settings.VERSION)
        table.add_row("SESSION", self.session_id)
        table.add_row("MODE", f"[bold green]{self.mode.value}[/bold green]")
        table.add_row("COMMANDS", "/help, /mode, /clear, /memory, /exit")

        console.print(Panel(table, title="[bold white]AEGIS CORE INTERFACE[/bold white]", border_style="blue"))

    async def run(self) -> None:
        """Loop principal do REPL."""
        self.display_header()
        
        while self.is_running:
            try:
                # Prompt customizado
                user_text = Prompt.ask(f"\n[bold cyan]{self.settings.AEGIS_USER_NAME}[/bold cyan] @ [dim]{self.mode.value}[/dim]")
                
                if not user_text.strip():
                    continue

                if user_text.startswith("/"):
                    await self.handle_command(user_text)
                    continue

                await self.process_input(user_text)

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupção detectada. Encerrando...[/yellow]")
                self.is_running = False
            except Exception as e:
                console.print(f"\n[bold red]Erro Crítico:[/bold red] {e}")
                logger.error("cli.loop_error", error=str(e), exc_info=True)

    async def handle_command(self, command_text: str) -> None:
        """Processa comandos iniciados com '/'."""
        parts = command_text.split()
        cmd = parts[0].lower()

        if cmd == "/exit":
            console.print("[blue]Desconectando do AEGIS... Até breve.[/blue]")
            self.is_running = False
        
        elif cmd == "/help":
            self.show_help()
        
        elif cmd == "/mode":
            if len(parts) > 1:
                new_mode_str = parts[1].upper()
                try:
                    self.mode = OperatingMode(new_mode_str)
                    console.print(f"[green]Modo alterado para:[/green] [bold]{self.mode.value}[/bold]")
                except ValueError:
                    console.print(f"[red]Modo inválido: {new_mode_str}.[/red] Use: STANDARD, BRIEFING, ANALYSIS, SILENT, VERBOSE.")
            else:
                console.print(f"[cyan]Modo atual:[/cyan] {self.mode.value}")
        
        elif cmd == "/clear":
            console.clear()
            self.display_header()
        
        elif cmd == "/memory":
            console.print("[yellow]Working Memory (Redis) interface será implementada na Task 1.7.[/yellow]")
            # Nota: A Task 1.7 já foi concluída conforme progress.txt, 
            # mas este comando pode ser expandido depois.
        
        else:
            console.print(f"[red]Comando desconhecido: {cmd}[/red]. Digite /help para comandos disponíveis.")

    def show_help(self) -> None:
        """Exibe a lista de comandos disponíveis."""
        help_text = """
[bold cyan]Comandos Disponíveis:[/bold cyan]
• [bold]/mode <MODO>[/bold] - Altera o modo de operação (ex: /mode BRIEFING)
• [bold]/clear[/bold]        - Limpa a tela do terminal
• [bold]/memory[/bold]       - Exibe o estado da memória de trabalho (em breve)
• [bold]/help[/bold]         - Mostra esta mensagem de ajuda
• [bold]/exit[/bold]         - Encerra a sessão do AEGIS
        """
        console.print(Panel(help_text, title="AJUDA", border_style="cyan"))

    async def process_input(self, text: str) -> None:
        """Envia o texto para a Engine e exibe a resposta com efeito de streaming."""
        user_input = UserInput(
            text=text,
            session_id=self.session_id,
            mode=self.mode
        )

        with console.status("[bold blue]AEGIS está processando...[/bold blue]"):
            try:
                response = await self.engine.process(user_input)
                await self.display_response(response)
            except Exception as e:
                console.print(f"[bold red]Falha na Engine:[/bold red] {e}")

    async def display_response(self, response: AgentResponse) -> None:
        """Exibe a resposta do agente com efeito de digitação token a token."""
        console.print(f"\n[bold magenta]AEGIS[/bold magenta] [dim]({response.latency_ms}ms)[/dim]")
        
        # Simulação de streaming (conforme requisito da Task 1.8)
        # Dividimos em palavras para simular o recebimento de tokens
        words = response.text.split(" ")
        full_text = ""
        
        with Live(Markdown(""), refresh_per_second=20, console=console) as live:
            for word in words:
                full_text += word + " "
                live.update(Markdown(full_text))
                await asyncio.sleep(0.05) # Delay simulando streaming

@app.command()
def main() -> None:
    """Ponto de entrada da CLI."""
    cli = AEGISCLI()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    app()
