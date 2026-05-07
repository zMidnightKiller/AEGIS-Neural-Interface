import psutil
import time
import os
import sys
import logging
from datetime import datetime

# Antigravity Kit 2.0 - Resource Monitor & Telemetry
# Version: 2.0.0
# Author: Antigravity AI

class AntigravityMonitor:
    """
    Monitor de recursos avançado (Kit 2.0) para o ecossistema Helen AI.
    Implementa telemetria em tempo real e controle dinâmico de carga.
    """
    
    def __init__(self, cpu_threshold=40.0, ram_threshold_gb=6.0, log_file=".tmp/telemetry.log"):
        self.cpu_threshold = cpu_threshold
        self.ram_threshold_bytes = ram_threshold_gb * (1024**3)
        self.log_file = log_file
        self.process = psutil.Process(os.getpid())
        
        # Configuração de Logging
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] AntigravityKit: %(message)s'
        )
        logging.info("Antigravity Kit 2.0 Initialized.")

    def get_system_stats(self):
        """Retorna estatísticas detalhadas do sistema."""
        stats = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_used_gb": psutil.virtual_memory().used / (1024**3),
            "memory_percent": psutil.virtual_memory().percent,
            "process_cpu": self.process.cpu_percent(),
            "process_memory_mb": self.process.memory_info().rss / (1024**2),
            "timestamp": datetime.now().isoformat()
        }
        return stats

    def check_health(self):
        """Valida se o sistema está apto para tarefas pesadas."""
        stats = self.get_system_stats()
        
        reasons = []
        if stats["cpu_percent"] > self.cpu_threshold:
            reasons.append(f"CPU Overload ({stats['cpu_percent']}%)")
        
        if psutil.virtual_memory().used > self.ram_threshold_bytes:
            reasons.append(f"Memory Pressure ({stats['memory_used_gb']:.2f}GB used)")
            
        is_healthy = len(reasons) == 0
        status_msg = "HEALTHY" if is_healthy else f"THROTTLED: {', '.join(reasons)}"
        
        logging.info(f"Health Check: {status_msg}")
        return is_healthy, status_msg

    def optimize_performance(self):
        """Aplica otimizações de runtime (Kit 2.0)."""
        # Ajuste de prioridade
        if sys.platform == 'win32':
            self.process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else:
            self.process.nice(10)
            
        logging.info("Optimization: Process priority set to Below Normal/10.")
        return True

    def log_telemetry(self):
        """Grava métricas em arquivo para análise futura."""
        stats = self.get_system_stats()
        logging.info(f"Telemetry Snapshot: CPU={stats['cpu_percent']}% | RAM={stats['memory_percent']}% | ProcMem={stats['process_memory_mb']:.1f}MB")

if __name__ == "__main__":
    monitor = AntigravityMonitor()
    monitor.optimize_performance()
    print("[*] Antigravity Kit 2.0: Monitor Ativo.")
    while True:
        healthy, msg = monitor.check_health()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {msg}")
        monitor.log_telemetry()
        time.sleep(10)
