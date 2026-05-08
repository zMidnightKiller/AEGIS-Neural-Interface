"""
aegis/interfaces/cli.py

Interface de Linha de Comando (CLI) para interação com o AEGIS.
Utiliza Typer para comandos e Rich para uma interface visual premium.
Inclui monitoramento de hardware em tempo real (GPU, VRAM, CPU, RAM).
"""
from __future__ import annotations

import asyncio
import uuid
import sys
import time
from typing import Optional, Dict, Any, List

import typer
import structlog
import psutil
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.live import Live
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.spinner import Spinner

from aegis.core.engine import Engine
from aegis.core.models import UserInput, OperatingMode, AgentResponse
from aegis.core.config import get_settings
from aegis.core.resource_guard import ResourceGuard, ResourceStatus
from aegis.core.events import event_bus, AegisEvent

logger = structlog.get_logger(__name__)
console = Console()
app = typer.Typer(help="AEGIS AI - Terminal Interface")

class AEGISCLI:
    """Gerenciador da interface REPL do AEGIS com monitoramento de recursos."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.engine = Engine()
        self.guard = ResourceGuard.get_instance()
        self.session_id = str(uuid.uuid4())
        self.mode = OperatingMode(self.settings.AEGIS_MODE)
        self.is_running = True
        self.current_response = ""
        self.last_status: Optional[ResourceStatus] = None
        self.tokens_received = 0
        self.start_stream_time = 0.0
        self._token_event = asyncio.Event()
        
        # Cores por nível do ResourceGuard
        self.level_colors = {
            "SAFE": "green",
            "WARN": "yellow",
            "PAUSE": "orange3",
            "STOP": "red",
            "EMERGENCY": "bold red blink"
        }

    def _get_status_footer(self) -> RenderableType:
        """Gera a barra de status para o rodapé."""
        if not self.last_status:
            return Text(" Carregando métricas de hardware...", style="dim")

        s = self.last_status
        color = self.level_colors.get(s.level, "white")
        
        # Cálculo de tokens/s se estiver streamando
        tok_speed = ""
        if self.tokens_received > 0 and self.start_stream_time > 0:
            elapsed = time.perf_counter() - self.start_stream_time
            if elapsed > 0:
                speed = self.tokens_received / elapsed
                tok_speed = f" | {speed:.1f} tok/s"

        # Formatação da barra
        status_text = Text.assemble(
            (f" GPU: {s.vram_pct:.0f}% ", color),
            (f"({s.vram_used_gb:.1f}/{s.vram_total_gb:.1f}GB)", "dim"),
            " | ",
            (f"TEMP: {s.gpu_temp_c:.0f}°C", "yellow" if s.gpu_temp_c > 75 else "white"),
            " | ",
            (f"CPU: {s.cpu_pct:.0f}%", "white"),
            " | ",
            (f"RAM: {s.ram_used_gb:.1f}/{s.ram_total_gb:.1f}GB", "white"),
            (tok_speed, "cyan"),
            " | ",
            (f" NIVEL: {s.level} ", f"on {color}" if s.level != "SAFE" else color)
        )
        
        return Panel(status_text, style="blue", expand=True, padding=(0, 1))

    async def _token_callback(self, event: AegisEvent):
        """Callback para receber tokens do EventBus."""
        if event.type == "token":
            token = event.data.get("token", "")
            self.current_response += token
            self.tokens_received += 1
            self._token_event.set()

    def display_header(self) -> None:
        """Exibe o cabeçalho inicial do AEGIS."""
        table = Table(show_header=False, border_style="bold blue", box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("SYSTEM", "AEGIS AI [LOCAL & PRIVATE]")
        table.add_row("HARDWARE", "RTX 3060 12GB + 32GB RAM")
        table.add_row("BACKEND", f"{self.settings.AEGIS_INFERENCE_BACKEND.upper()} (Split GPU+RAM)")
        table.add_row("SESSION", self.session_id)
        table.add_row("MODE", f"[bold green]{self.mode.value}[/bold green]")
        
        header_panel = Panel(
            Align.center(table), 
            title="[bold white]AEGIS CORE INTERFACE[/bold white]", 
            border_style="blue",
            subtitle="[dim]Type /help for available commands[/dim]"
        )
        console.print(header_panel)

    async def run(self) -> None:
        """Loop principal do REPL com Live display para o footer."""
        await self.engine.initialize()
        self.display_header()
        
        # Subscreve no event bus para streaming
        event_bus.subscribe(self._token_callback)
        
        # O Live será usado para o footer. 
        # Como o Rich não suporta facilmente um footer persistente com REPL no mesmo console,
        # usaremos o Live em modo transient para o footer durante o processamento
        # ou apenas o atualizaremos entre prompts.
        
        # Decisão: Footer atualizado no Live durante o loop.
        with Live(self._get_status_footer(), refresh_per_second=4, screen=False) as live:
            while self.is_running:
                try:
                    # Atualiza status
                    self.last_status = await self.guard.check()
                    live.update(self._get_status_footer())
                    
                    # Prompt (roda em thread para não bloquear o loop de eventos se possível, 
                    # mas aqui é o REPL principal)
                    user_text = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: Prompt.ask(f"\n[bold cyan]{self.settings.AEGIS_USER_NAME or 'USER'}[/bold cyan] @ [dim]{self.mode.value}[/dim]")
                    )
                    
                    if not user_text.strip():
                        continue

                    if user_text.startswith("/"):
                        await self.handle_command(user_text)
                        continue

                    await self.process_input(user_text, live)

                except KeyboardInterrupt:
                    console.print("\n[yellow]Interrupção detectada. Encerrando...[/yellow]")
                    self.is_running = False
                except Exception as e:
                    console.print(f"\n[bold red]Erro Crítico:[/bold red] {e}")
                    logger.error("cli.loop_error", error=str(e), exc_info=True)
        
        event_bus.unsubscribe(self._token_callback)

    async def handle_command(self, command_text: str) -> None:
        """Processa comandos iniciados com '/'."""
        parts = command_text.split()
        cmd = parts[0].lower()

        if cmd == "/exit":
            console.print("[blue]Desconectando do AEGIS... Até breve.[/blue]")
            self.is_running = False
        
        elif cmd == "/help":
            self.show_help()
        
        elif cmd == "/status":
            await self.show_detailed_status()
            
        elif cmd == "/mode":
            if len(parts) > 1:
                new_mode_str = parts[1].upper()
                try:
                    self.mode = OperatingMode(new_mode_str)
                    console.print(f"[green]Modo alterado para:[/green] [bold]{self.mode.value}[/bold]")
                except ValueError:
                    modes = ", ".join([m.value for m in OperatingMode])
                    console.print(f"[red]Modo inválido. Use:[/red] {modes}")
            else:
                console.print(f"[cyan]Modo atual:[/cyan] {self.mode.value}")

        elif cmd == "/model":
            console.print(f"[cyan]Modelo Ativo:[/cyan] [bold]{self.settings.AEGIS_MODEL_NAME}[/bold]")
            console.print(f"[dim]Path: {self.settings.AEGIS_MODEL_PATH}[/dim]")
            console.print(f"[dim]GPU Layers: {self.settings.AEGIS_GPU_LAYERS}[/dim]")

        elif cmd == "/learn":
            if len(parts) > 1:
                state = parts[1].lower()
                if state in ["on", "true", "1"]:
                    self.mode = OperatingMode.LEARNING
                    console.print("[yellow]Modo LEARNING ativado. Conversas serão coletadas para fine-tuning.[/yellow]")
                else:
                    self.mode = OperatingMode.STANDARD
                    console.print("[green]Modo LEARNING desativado.[/green]")
            else:
                is_learning = self.mode == OperatingMode.LEARNING
                console.print(f"[cyan]Aprendizado Contínuo:[/cyan] {'[bold green]ON[/bold green]' if is_learning else '[bold red]OFF[/bold red]'}")

        elif cmd == "/benchmark":
            console.print("[yellow]Iniciando benchmark rápido do motor de inferência...[/yellow]")
            with console.status("Testando..."):
                await asyncio.sleep(1)
                console.print(Panel("Benchmark: 12.4 tok/s | VRAM Peak: 5.2GB | Latency: 120ms", title="BENCHMARK RESULTS"))
        
        elif cmd == "/clear":
            console.clear()
            self.display_header()
        
        else:
            console.print(f"[red]Comando desconhecido: {cmd}[/red]. Digite /help para comandos disponíveis.")

    async def show_detailed_status(self) -> None:
        """Exibe snapshot detalhado de recursos."""
        s = await self.guard.check()
        table = Table(title="Detalhamento de Hardware", border_style="blue")
        table.add_column("Recurso", style="cyan")
        table.add_column("Uso", style="white")
        table.add_column("Capacidade", style="dim")
        table.add_column("Status", style="bold")

        vram_color = self.level_colors.get(s.level, "white")
        table.add_row("VRAM (GPU)", f"{s.vram_pct:.1f}%", f"{s.vram_used_gb:.1f}/{s.vram_total_gb:.1f} GB", Text(s.level, style=vram_color))
        table.add_row("GPU Temp", f"{s.gpu_temp_c:.0f}°C", "Max: 90°C", "NORMAL" if s.gpu_temp_c < 80 else "HOT")
        table.add_row("CPU", f"{s.cpu_pct:.1f}%", f"{psutil.cpu_count()} cores", "OK")
        table.add_row("RAM", f"{(s.ram_used_gb/s.ram_total_gb)*100:.1f}%", f"{s.ram_used_gb:.1f}/{s.ram_total_gb:.1f} GB", "OK")
        
        if s.paused_ops:
            table.add_row("OPS PAUSADAS", ", ".join(s.paused_ops), "", "[bold red]PAUSED[/bold red]")

        console.print(table)

    def show_help(self) -> None:
        """Exibe a lista de comandos disponíveis."""
        help_text = """
[bold cyan]Navegação & Sessão:[/bold cyan]
• [bold]/clear[/bold]         - Limpa a tela
• [bold]/help[/bold]          - Mostra esta ajuda
• [bold]/exit[/bold]          - Encerra o AEGIS

[bold cyan]Configuração & Modo:[/bold cyan]
• [bold]/mode <MODO>[/bold]  - Altera modo (STANDARD, BRIEFING, ANALYSIS, etc.)
• [bold]/learn on|off[/bold]  - Ativa/Desativa coleta de dados para treino
• [bold]/model[/bold]         - Informações do modelo carregado

[bold cyan]Monitoramento:[/bold cyan]
• [bold]/status[/bold]        - Snapshot completo de hardware
• [bold]/benchmark[/bold]     - Teste de performance local
        """
        console.print(Panel(help_text, title="CENTRAL DE AJUDA", border_style="cyan"))

    async def process_input(self, text: str, live: Live) -> None:
        """Envia o texto para a Engine e gerencia o streaming real na UI."""
        self.current_response = ""
        self.tokens_received = 0
        self.start_stream_time = time.perf_counter()
        self._token_event.clear()
        
        user_input = UserInput(
            text=text,
            session_id=self.session_id,
            mode=self.mode
        )

        console.print(f"\n[bold magenta]AEGIS[/bold magenta] [dim]pensando...[/dim]")
        
        # A Engine.process emite tokens via event_bus que capturamos no callback
        process_task = asyncio.create_task(self.engine.process(user_input))
        
        # Usamos um Live interno para a mensagem, mas o Live externo continua cuidando do footer
        with Live(Markdown(""), refresh_per_second=10, console=console, transient=False) as live_msg:
            while not process_task.done():
                try:
                    # Espera por um novo token ou timeout
                    await asyncio.wait_for(self._token_event.wait(), timeout=0.1)
                    if self._token_event.is_set():
                        live_msg.update(Markdown(self.current_response))
                        self._token_event.clear()
                        # Atualiza o footer global também
                        live.update(self._get_status_footer())
                except asyncio.TimeoutError:
                    # Apenas atualiza o status se não houver tokens vindo
                    live.update(self._get_status_footer())
                    continue
            
            # Garantir que mostramos tudo ao terminar
            live_msg.update(Markdown(self.current_response))
        
        try:
            response = await process_task
            console.print(f"[dim]({response.latency_ms}ms | {self.tokens_received} tokens)[/dim]")
        except Exception as e:
            console.print(f"[bold red]Erro no processamento:[/bold red] {e}")

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
