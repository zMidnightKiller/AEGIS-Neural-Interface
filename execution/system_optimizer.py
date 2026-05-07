import os
import shutil
import time
import logging

# Antigravity Kit 2.0 - System Optimizer
# Responsável por manter a saúde do diretório .tmp e liberar recursos.

def clean_tmp_dir(tmp_path=".tmp", max_age_hours=24):
    """Remove arquivos antigos do diretório temporário."""
    if not os.path.exists(tmp_path):
        return
    
    now = time.time()
    count = 0
    for filename in os.listdir(tmp_path):
        filepath = os.path.join(tmp_path, filename)
        if os.path.isfile(filepath):
            # Se o arquivo for mais antigo que max_age_hours
            if os.stat(filepath).st_mtime < now - (max_age_hours * 3600):
                try:
                    os.remove(filepath)
                    count += 1
                except Exception as e:
                    logging.error(f"Erro ao remover {filename}: {e}")
                    
    print(f"[*] Limpeza concluída: {count} arquivos removidos de {tmp_path}.")
    logging.info(f"System Optimizer: Cleaned {count} files from {tmp_path}.")

def force_garbage_collection():
    """Força a coleta de lixo no Python."""
    import gc
    before = gc.collect()
    logging.info(f"System Optimizer: Garbage collection forced. {before} objects collected.")
    return before

if __name__ == "__main__":
    logging.basicConfig(filename=".tmp/telemetry.log", level=logging.INFO)
    clean_tmp_dir()
    force_garbage_collection()
