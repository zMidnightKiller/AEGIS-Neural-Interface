import time
import os
import sys
from core.config import settings
from core.engine import engine
from execution.antigravity_monitor import AntigravityMonitor

def print_banner():
    banner = """
    ==========================================================
              ANTIGRAVITY KIT 2.0 - SYSTEM STATUS
    ==========================================================
    [PROJECT]  : HELEN AI
    [VERSION]  : 2.0.0 (Enhanced Architecture)
    [BASE]     : AGENTE.md Standards
    ----------------------------------------------------------
    """
    print(banner)

def check_kit_status():
    print_banner()
    
    # Verifica arquivos críticos
    paths = [
        "directives/antigravity_kit.md",
        "execution/antigravity_monitor.py",
        "execution/system_optimizer.py",
        "execution/skills/media_intelligence.py",
        "execution/skills/deep_research.py",
        "execution/skills/neural_memory_mapper.py",
        ".tmp/telemetry.log"
    ]
    
    print("[*] Verificando integridade dos módulos...")
    for path in paths:
        exists = "OK" if os.path.exists(path) else "MISSING"
        print(f"  > {path.ljust(35)}: [{exists}]")
    
    print("\n[*] Inicializando Engine com Kit 2.0...")
    if engine.monitor:
        print("  [+] Monitor de Recursos: ATIVO")
        stats = engine.monitor.get_system_stats()
        print(f"  [+] CPU Atual: {stats['cpu_percent']}% (Threshold: {settings.ANTIGRAVITY_CPU_THRESHOLD}%)")
        print(f"  [+] RAM Atual: {stats['memory_used_gb']:.2f}GB (Threshold: {settings.ANTIGRAVITY_RAM_THRESHOLD_GB}GB)")
        
        healthy, msg = engine.monitor.check_health()
        status_color = "HEALTHY" if healthy else "THROTTLED"
        print(f"\n[STATUS FINAL]: {status_color} - {msg}")
    else:
        print("  [!] ERRO: Kit 2.0 não detectado no motor principal.")

if __name__ == "__main__":
    try:
        check_kit_status()
    except Exception as e:
        print(f"Erro ao validar Kit: {e}")
