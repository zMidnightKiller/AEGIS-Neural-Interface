import pytest
from unittest.mock import patch, MagicMock

# Mocks para imports
with patch.dict("sys.modules", {
    "langfuse": MagicMock(),
    "prometheus_fastapi_instrumentator": MagicMock()
}):
    from aegis.core.observability import ObservabilityManager
    from aegis.core.config import get_settings

def test_prometheus_setup_logic():
    """Verifica se o setup do Prometheus chama os metodos corretos da lib."""
    mock_app = MagicMock()
    with patch("aegis.core.observability.Instrumentator") as mock_instrumentator:
        manager = ObservabilityManager()
        manager.setup_fastapi(mock_app)
        mock_instrumentator.return_value.instrument.assert_called_once_with(mock_app)
        mock_instrumentator.return_value.instrument.return_value.expose.assert_called_once()

def test_langfuse_trace_logic():
    """Verifica se o Langfuse trace e chamado quando obs_manager.trace_event e executado."""
    with patch("aegis.core.observability.Langfuse") as mock_langfuse_class:
        with patch("aegis.core.observability.settings") as mock_settings:
            mock_settings.LANGFUSE_PUBLIC_KEY = "pk-123"
            mock_settings.LANGFUSE_SECRET_KEY.get_secret_value.return_value = "sk-123"
            mock_settings.LANGFUSE_HOST = "https://cloud.langfuse.com"
            
            manager = ObservabilityManager()
            # O construtor deve ter instanciado o Langfuse
            mock_langfuse_class.assert_called_once()
            
            manager.trace_event("test_event", "user-1", "input_data")
            manager.langfuse.trace.assert_called_once()

def test_langfuse_disabled_without_keys():
    """Verifica se o Langfuse fica desabilitado sem chaves de API."""
    with patch("aegis.core.observability.settings") as mock_settings:
        mock_settings.LANGFUSE_PUBLIC_KEY = None
        manager = ObservabilityManager()
        assert manager.langfuse is None
