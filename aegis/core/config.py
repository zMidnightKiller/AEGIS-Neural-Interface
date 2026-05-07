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

    # --- API KEYS (Required) ---
    ANTHROPIC_API_KEY: SecretStr = Field(..., description="Chave da API Anthropic para o Claude")
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


    @field_validator("ANTHROPIC_API_KEY")
    @classmethod
    def validate_api_key(cls, v: SecretStr, info) -> SecretStr:
        """Garante que a chave não está vazia, exceto em desenvolvimento."""
        val = v.get_secret_value()
        # Se estiver em desenvolvimento, permitimos placeholder para fins de demo/build
        if not val or val == "your_key_here":
            logger.warning("ANTHROPIC_API_KEY não configurada ou usando placeholder. O sistema funcionará em modo limitado.")
            return SecretStr("mock_key_for_demo")
        return v


@lru_cache
def get_settings() -> Settings:
    """Retorna o singleton das configurações com cache."""
    return Settings()
