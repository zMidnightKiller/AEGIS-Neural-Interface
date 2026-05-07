# Backend Dockerfile - AEGIS Core
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código fonte
COPY . .

# Expor porta da API
EXPOSE 8000

# Comando para iniciar a API
CMD ["uvicorn", "aegis.interfaces.api:app", "--host", "0.0.0.0", "--port", "8000"]
