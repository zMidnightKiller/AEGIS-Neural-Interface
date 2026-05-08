#!/usr/bin/env python3
"""
scripts/download_models.py

Baixa modelos GGUF do HuggingFace para o diretório ./models/.
Verifica hash e suporta resumo de download via huggingface_hub.
"""
import os
import sys
from pathlib import Path
try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("Erro: huggingface_hub não instalado. Execute 'pip install huggingface-hub'.")
    sys.exit(1)

import structlog
from rich.console import Console
from rich.panel import Panel

console = Console()
logger = structlog.get_logger(__name__)

# Configuração dos modelos (calibrada para RTX 3060 12GB)
MODELS_TO_DOWNLOAD = [
    {
        "repo_id": "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF",
        "filename": "Mistral-7B-Instruct-v0.3.Q4_K_M.gguf",
        "alias": "Mistral-7B-Q4_K_M (Principal)",
    },
    {
        "repo_id": "bartowski/Meta-Llama-3-8B-Instruct-GGUF",
        "filename": "Meta-Llama-3-8B-Instruct-Q4_K_M.gguf",
        "alias": "LLaMA-3-8B-Q4_K_M (Alternativa)",
    },
    {
        "repo_id": "microsoft/Phi-3-mini-4k-instruct-gguf",
        "filename": "Phi-3-mini-4k-instruct-q4.gguf",
        "alias": "Phi-3-mini-Q4 (Fallback CPU)",
    },
    {
        "repo_id": "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF",
        "filename": "Mistral-7B-Instruct-v0.3.Q5_K_M.gguf",
        "alias": "Mistral-7B-Q5_K_M (Alta Qualidade)",
    },
]

# Tenta ler diretório do .env ou usa padrão
MODELS_DIR = Path("./models")

def download_models():
    """Baixa todos os modelos configurados."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    console.print(Panel("[bold cyan]AEGIS — Downloader de Modelos[/bold cyan]"))
    console.print(f"Diretório de destino: [yellow]{MODELS_DIR.absolute()}[/yellow]\n")
    
    for model in MODELS_TO_DOWNLOAD:
        repo_id = model["repo_id"]
        filename = model["filename"]
        alias = model["alias"]
        
        target_path = MODELS_DIR / filename
        
        if target_path.exists():
            console.print(f"[green]✔[/green] {alias} já existe.")
            continue
            
        console.print(f"[cyan]Iniciando download de:[/cyan] {alias}")
        console.print(f"Repo: [dim]{repo_id}[/dim] | Arquivo: [dim]{filename}[/dim]")
        
        try:
            # hf_hub_download faz verificação de hash e resume automaticamente
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=MODELS_DIR,
                local_dir_use_symlinks=False,
                resume_download=True
            )
            console.print(f"[green]✔[/green] Download concluído: {downloaded_path}\n")
        except Exception as e:
            console.print(f"[red]✘ Erro ao baixar {alias}:[/red] {e}\n")
            logger.error("download.error", model=alias, error=str(e))

if __name__ == "__main__":
    download_models()
