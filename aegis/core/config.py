"""
aegis/core/config.py

Gestão de configurações centralizada do AEGIS.
Utiliza Pydantic Settings v2 para validação e tipagem forte.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

import structlog
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """
    Configurações globais do sistema AEGIS.
    As variáveis são lidas automaticamente do ambiente ou arquivo .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- INFRA ---
    PROJECT_NAME: str = "AEGIS AI"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"

    # --- MODELO LOCAL (RTX 3060) ---
    AEGIS_MODEL_PATH: str = "./models/mistral-7b-instruct-v0.3-q4_k_m.gguf"
    AEGIS_INFERENCE_BACKEND: Literal["llamacpp", "ollama", "vllm"] = "llamacpp"
    AEGIS_MODEL_NAME: str = "mistral-7b-instruct"
    AEGIS_MAX_TOKENS: int = 2048
    AEGIS_GPU_LAYERS: int = 28
    AEGIS_CONTEXT_LENGTH: int = 4096
    AEGIS_N_THREADS: int = 8

    # --- APRENDIZADO ---
    AEGIS_LEARNING_ENABLED: bool = True
    AEGIS_FINETUNE_SCHEDULE: str = "nightly"
    AEGIS_MIN_SAMPLES_FOR_FINETUNE: int = 30
    AEGIS_LORA_RANK: int = 8
    AEGIS_LORA_ALPHA: int = 16
    AEGIS_RLHF_ENABLED: bool = True
    AEGIS_FINETUNE_BATCH_SIZE: int = 1
    AEGIS_GRADIENT_CHECKPOINTING: bool = True

    # --- RESOURCE GUARD ---
    RESOURCE_GUARD_ENABLED: bool = True
    GPU_WARN_PCT: int = 80
    GPU_PAUSE_PCT: int = 92
    GPU_STOP_PCT: int = 96
    CPU_WARN_PCT: int = 70
    CPU_PAUSE_PCT: int = 85
    RAM_WARN_GB: int = 26
    RAM_PAUSE_GB: int = 29
    FINETUNE_ONLY_WHEN_IDLE: bool = True
    FINETUNE_IDLE_MINUTES: int = 30
    MAX_CONCURRENT_EMBEDDINGS: int = 2
    INFERENCE_PRIORITY: bool = True

    # --- DIRETÓRIOS ---
    AEGIS_DATA_DIR: str = "./data"
    AEGIS_MODELS_DIR: str = "./models"
    AEGIS_CHECKPOINTS_DIR: str = "./checkpoints"

    # --- LLM PROVISIONING (LEGACY/FALLBACK) ---
    AEGIS_LLM_PROVIDER: Literal["anthropic", "ollama"] = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # --- API KEYS ---
    ANTHROPIC_API_KEY: Optional[SecretStr] = Field(None, description="Chave da API Anthropic para o Claude")
    OPENAI_API_KEY: Optional[SecretStr] = None
    TAVILY_API_KEY: Optional[SecretStr] = None
    ELEVENLABS_API_KEY: Optional[SecretStr] = None

    # --- VOICE CONFIG ---
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel (default)

    # --- SERVICES ---
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_SESSION_TTL: int = 86400  # 24h em segundos

    CHROMA_PERSIST_DIR: str = "./data/chroma"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_PASSWORD: Optional[SecretStr] = None

    # --- OBSERVABILITY ---
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[SecretStr] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    ENABLE_PROMETHEUS: bool = True
    PROMETHEUS_ENDPOINT: str = "/metrics"

    # --- AEGIS ENGINE ---
    AEGIS_MODE: str = "STANDARD"
    AEGIS_USER_NAME: str = "User"
    CONTEXT_MAX_TOKENS: int = 4000
    
    # --- CACHE & OPTIMIZATION ---
    ENABLE_SEMANTIC_CACHE: bool = True
    CACHE_SIMILARITY_THRESHOLD: float = 0.92
    ENABLE_CONTEXT_COMPRESSION: bool = True
    CONTEXT_COMPRESSION_TOKEN_LIMIT: int = 3000 # Inicia compressão ao atingir este limite

    # --- ANTIGRAVITY KIT 2.0 ---
    ANTIGRAVITY_CPU_THRESHOLD: float = 40.0
    ANTIGRAVITY_RAM_THRESHOLD_GB: float = 6.0
    ANTIGRAVITY_TELEMETRY_LOG: str = ".tmp/telemetry.log"

    # --- TOOLS CONFIG ---
    ALLOWED_FS_PATHS: list[str] = ["./data", "./.tmp", "./docs"]
    RUNCODE_DOCKER_IMAGE: str = "python:3.11-slim"
    RUNCODE_TIMEOUT: int = 30

    # --- TASK AGENT CONFIG ---
    GOOGLE_CALENDAR_ID: str = "primary"
    EMAIL_SENDER: Optional[str] = None
    EMAIL_PASSWORD: Optional[SecretStr] = None
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587


@lru_cache
def get_settings() -> Settings:
    """Retorna o singleton das configurações com cache."""
    return Settings()
