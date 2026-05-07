import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from aegis.interfaces.cli import AEGISCLI
from aegis.core.models import OperatingMode, AgentResponse

@pytest.fixture
def mock_engine_and_settings():
    with patch("aegis.interfaces.cli.get_settings") as mock_get_settings, \
         patch("aegis.interfaces.cli.Engine") as mock_engine_class:
        
        mock_settings = MagicMock()
        mock_settings.PROJECT_NAME = "AEGIS Test"
        mock_settings.VERSION = "0.0.1"
        mock_settings.AEGIS_MODE = "STANDARD"
        mock_settings.AEGIS_USER_NAME = "Tester"
        mock_get_settings.return_value = mock_settings
        
        mock_engine = MagicMock()
        mock_engine.process = AsyncMock()
        mock_engine_class.return_value = mock_engine
        
        yield mock_engine, mock_settings

@pytest.mark.asyncio
class TestAEGISCLI:
    """Testes para a interface CLI do AEGIS."""

    async def test_cli_initialization(self, mock_engine_and_settings):
        """Verifica se a CLI inicializa com os valores corretos."""
        cli = AEGISCLI()
        assert cli.mode == OperatingMode.STANDARD
        assert cli.is_running is True
        assert len(cli.session_id) > 0

    async def test_handle_command_exit(self, mock_engine_and_settings):
        """Verifica se o comando /exit encerra a CLI."""
        cli = AEGISCLI()
        await cli.handle_command("/exit")
        assert cli.is_running is False

    async def test_handle_command_mode_change(self, mock_engine_and_settings):
        """Verifica se o comando /mode altera o modo de operação."""
        cli = AEGISCLI()
        await cli.handle_command("/mode BRIEFING")
        assert cli.mode == OperatingMode.BRIEFING

    async def test_handle_command_mode_invalid(self, mock_engine_and_settings):
        """Garante que modos inválidos não alteram o estado."""
        cli = AEGISCLI()
        await cli.handle_command("/mode INVALIDO")
        assert cli.mode == OperatingMode.STANDARD

    async def test_process_input_calls_engine(self, mock_engine_and_settings):
        """Verifica se a entrada do usuário chega até a Engine."""
        mock_engine, _ = mock_engine_and_settings
        mock_engine.process.return_value = AgentResponse(
            text="Resposta de teste",
            agent_used="test_agent",
            tools_used=[],
            memory_injected=False,
            latency_ms=100
        )
        
        cli = AEGISCLI()
        # Mockando display_response para evitar sleeps e Rich UI nos testes
        with patch.object(cli, 'display_response', new_callable=AsyncMock) as mock_display:
            await cli.process_input("Olá AEGIS")
            
            mock_engine.process.assert_called_once()
            args = mock_engine.process.call_args[0][0]
            assert args.text == "Olá AEGIS"
            assert args.session_id == cli.session_id
            mock_display.assert_called_once()
