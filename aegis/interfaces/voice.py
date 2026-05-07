"""
aegis/interfaces/voice.py

Interface de voz para o sistema AEGIS.
Implementa STT (Speech-to-Text) usando OpenAI Whisper via API.
Implementa TTS (Text-to-Speech) usando ElevenLabs com fallback pyttsx3.
"""
from __future__ import annotations

import asyncio
import httpx
import structlog
from typing import Optional, Any

from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)


class VoiceInterface:
    """
    Interface para processamento de voz (STT e TTS).
    Responsável pela ponte entre dados de áudio e texto.
    """

    def __init__(self) -> None:
        """Inicializa a interface de voz com configurações globais."""
        self.settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """
        Lazy initialization do cliente HTTP async para evitar consumo de recursos
        se a voz não for utilizada.
        """
        if self._client is None:
            # Timeout estendido para uploads de áudio e processamento STT/TTS
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def transcribe_audio(
        self, audio_bytes: bytes, filename: str = "audio.wav", language: Optional[str] = None
    ) -> Optional[str]:
        """
        Converte áudio em texto usando a API Whisper da OpenAI.

        Args:
            audio_bytes: O conteúdo bruto do arquivo de áudio.
            filename: Nome do arquivo (usado para inferir o formato pela extensão).
            language: Código opcional da língua (ex: 'pt', 'en').

        Returns:
            Texto transcrito ou None se falhar.
        """
        if not self.settings.OPENAI_API_KEY:
            logger.error("voice.stt.missing_key", error="OPENAI_API_KEY não configurada no ambiente")
            return None

        logger.info("voice.stt.transcribing", filename=filename, size=len(audio_bytes))

        try:
            files = {
                "file": (filename, audio_bytes, "audio/wav"),
            }
            
            data = {
                "model": "whisper-1",
            }
            if language:
                data["language"] = language

            headers = {
                "Authorization": f"Bearer {self.settings.OPENAI_API_KEY.get_secret_value()}"
            }

            response = await self.client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
            )

            if response.status_code == 429:
                logger.warning("voice.stt.rate_limit", error=response.text)
                return None

            response.raise_for_status()
            result = response.json()
            
            transcription = result.get("text", "").strip()
            
            if not transcription:
                logger.warning("voice.stt.empty_result", filename=filename)
                return ""

            logger.info("voice.stt.success", text_length=len(transcription))
            return transcription

        except httpx.HTTPStatusError as e:
            logger.error(
                "voice.stt.http_error", 
                status=e.response.status_code, 
                error=e.response.text
            )
        except Exception as e:
            logger.error("voice.stt.unexpected_error", error=str(e), exc_info=True)

        return None

    async def speak_text(self, text: str) -> Optional[bytes]:
        """
        Converte texto em áudio usando ElevenLabs com fallback para pyttsx3.

        Args:
            text: O texto a ser convertido.

        Returns:
            Bytes do áudio (MP3 da ElevenLabs) ou None se usar fallback local.
        """
        if self.settings.ELEVENLABS_API_KEY:
            audio = await self._speak_elevenlabs(text)
            if audio:
                return audio
        
        logger.info("voice.tts.falling_back", text_preview=text[:30])
        await self._speak_pyttsx3(text)
        return None

    async def _speak_elevenlabs(self, text: str) -> Optional[bytes]:
        """Gera áudio via ElevenLabs API."""
        api_key = self.settings.ELEVENLABS_API_KEY
        if not api_key:
            return None

        voice_id = self.settings.ELEVENLABS_VOICE_ID
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key.get_secret_value(),
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        try:
            logger.info("voice.tts.elevenlabs.requesting", text_length=len(text))
            response = await self.client.post(url, json=data, headers=headers)
            
            if response.status_code == 429:
                logger.warning("voice.tts.elevenlabs.rate_limit")
                return None
                
            response.raise_for_status()
            logger.info("voice.tts.elevenlabs.success")
            return response.content
        except Exception as e:
            logger.error("voice.tts.elevenlabs.error", error=str(e))
            return None

    async def _speak_pyttsx3(self, text: str) -> None:
        """Gera voz local via pyttsx3 (fallback)."""
        try:
            # Import dinâmico para evitar erro se não estiver instalado
            import pyttsx3

            def _run_tts():
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()

            logger.info("voice.tts.pyttsx3.speaking")
            await asyncio.to_thread(_run_tts)
        except ImportError:
            logger.error("voice.tts.pyttsx3.missing", error="pyttsx3 não está instalado")
        except Exception as e:
            logger.error("voice.tts.pyttsx3.error", error=str(e))

    async def close(self) -> None:
        """Encerra recursos da interface, fechando o cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("voice.interface.closed")
