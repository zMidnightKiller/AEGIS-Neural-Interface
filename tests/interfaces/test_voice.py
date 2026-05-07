"""
tests/interfaces/test_voice.py

Testes unitários para a VoiceInterface (STT e TTS).
Garante que as chamadas às APIs e fallbacks sejam mockados corretamente.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aegis.interfaces.voice import VoiceInterface

@pytest.fixture
async def voice_interface():
    """Fixture que fornece uma instância limpa da VoiceInterface."""
    interface = VoiceInterface()
    yield interface
    await interface.close()

class TestVoiceInterface:
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, voice_interface):
        """Testa transcrição bem sucedida com resposta válida da API Whisper."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "Olá, esta é uma transcrição de teste."}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with patch("aegis.interfaces.voice.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.OPENAI_API_KEY.get_secret_value.return_value = "fake-key"
                mock_get_settings.return_value = mock_settings
                voice_interface.settings = mock_settings
                
                result = await voice_interface.transcribe_audio(b"fake audio data")
                
        assert result == "Olá, esta é uma transcrição de teste."
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "Authorization" in kwargs["headers"]
        assert "Bearer fake-key" in kwargs["headers"]["Authorization"]

    @pytest.mark.asyncio
    async def test_speak_text_elevenlabs_success(self, voice_interface):
        """Testa conversão de texto em áudio via ElevenLabs com sucesso."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake audio mp3 content"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with patch("aegis.interfaces.voice.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.ELEVENLABS_API_KEY.get_secret_value.return_value = "fake-eleven-key"
                mock_settings.ELEVENLABS_VOICE_ID = "fake-voice-id"
                mock_get_settings.return_value = mock_settings
                voice_interface.settings = mock_settings
                
                result = await voice_interface.speak_text("Olá, AEGIS falando.")
                
        assert result == b"fake audio mp3 content"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "xi-api-key" in kwargs["headers"]
        assert kwargs["headers"]["xi-api-key"] == "fake-eleven-key"

    @pytest.mark.asyncio
    async def test_speak_text_fallback_to_pyttsx3(self, voice_interface):
        """Testa fallback para pyttsx3 quando ElevenLabs falha ou não tem chave."""
        with patch("aegis.interfaces.voice.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.ELEVENLABS_API_KEY = None  # Sem chave -> fallback imediato
            mock_get_settings.return_value = mock_settings
            voice_interface.settings = mock_settings
            
            with patch("aegis.interfaces.voice.VoiceInterface._speak_pyttsx3", new_callable=AsyncMock) as mock_pyttsx3:
                result = await voice_interface.speak_text("Teste de fallback.")
                
        assert result is None
        mock_pyttsx3.assert_called_once_with("Teste de fallback.")

    @pytest.mark.asyncio
    async def test_speak_pyttsx3_execution(self, voice_interface):
        """Testa a execução interna do pyttsx3 (mockando a biblioteca)."""
        mock_engine = MagicMock()
        mock_pyttsx3 = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine
        
        with patch.dict("sys.modules", {"pyttsx3": mock_pyttsx3}):
            await voice_interface._speak_pyttsx3("Teste local.")
            
        mock_pyttsx3.init.assert_called_once()
        mock_engine.say.assert_called_once_with("Teste local.")
        mock_engine.runAndWait.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_audio_http_error(self, voice_interface):
        """Testa o comportamento em caso de erro de rede ou API."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("Connection timed out")
            
            with patch("aegis.interfaces.voice.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.OPENAI_API_KEY.get_secret_value.return_value = "fake-key"
                mock_get_settings.return_value = mock_settings
                voice_interface.settings = mock_settings
                
                result = await voice_interface.transcribe_audio(b"fake audio data")
                
        assert result is None
