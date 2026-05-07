import os
import sys

# Adiciona o diretório atual ao PYTHONPATH
sys.path.append(os.getcwd())

# Configura variáveis de ambiente mínimas
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-mock-key-for-ui-demo-purposes"
os.environ["ENVIRONMENT"] = "test"

from aegis.core.mocks import patch_aegis_for_demo

# Aplica os mocks antes de importar o app
patch_aegis_for_demo()

import uvicorn
from aegis.interfaces.api import app

if __name__ == "__main__":
    print("Iniciando AEGIS API em MODO DEMO (Sem Docker/DBs reais)...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
