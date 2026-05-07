import pytest
import os
from pydantic import ValidationError
from aegis.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_env():
    """Limpa variáveis de ambiente relevantes antes de cada teste."""
    env_vars = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TAVILY_API_KEY"]
    old_values = {var: os.environ.get(var) for var in env_vars}
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]
    yield
    # Restaura (opcional, mas boa prática)
    for var, val in old_values.items():
        if val is not None:
            os.environ[var] = val
        elif var in os.environ:
            del os.environ[var]


def test_settings_validation_fails_without_key():
    """Garante que a inicialização falha se ANTHROPIC_API_KEY estiver ausente."""
    with pytest.raises(ValidationError):
        # O Pydantic Settings tentará ler do env limpo
        Settings()


def test_settings_validation_fails_with_placeholder():
    """Garante que falha com o valor de exemplo do .env.example."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(ANTHROPIC_API_KEY="your_key_here")
    assert "ANTHROPIC_API_KEY deve ser uma chave válida" in str(excinfo.value)


def test_settings_load_defaults():
    """Verifica se os valores padrão são carregados corretamente."""
    # Nota: Passamos explicitamente para ignorar o ambiente
    s = Settings(ANTHROPIC_API_KEY="sk-ant-xxx")
    assert s.PROJECT_NAME == "AEGIS AI"
    assert s.VERSION == "0.1.0"
    assert s.ENVIRONMENT == "development"


def test_get_settings_singleton():
    """Verifica se get_settings retorna a mesma instância."""
    # Mockando o ambiente para permitir o init
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-xxx"
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    assert s1.ANTHROPIC_API_KEY.get_secret_value() == "sk-ant-xxx"
