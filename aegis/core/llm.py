import httpx
import json
import structlog
from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic
from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)

class LLMClient:
    """
    Cliente universal para LLMs (Anthropic ou Ollama Local).
    Abstrai a comunicação para permitir troca fácil de provedores.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.provider = self.settings.AEGIS_LLM_PROVIDER.lower()
        
        if self.provider == "anthropic":
            self.client = AsyncAnthropic(api_key=self.settings.ANTHROPIC_API_KEY.get_secret_value())
        else:
            # Ollama usa HTTP direto
            self.base_url = self.settings.OLLAMA_BASE_URL
            self.model = self.settings.AEGIS_MODEL_NAME

    async def create_message(
        self, 
        system: str, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        max_tokens: int = 1000
    ) -> str:
        """Envia uma solicitação para o provedor configurado."""
        
        if self.provider == "anthropic":
            return await self._call_anthropic(system, messages, model, max_tokens)
        else:
            return await self._call_ollama(system, messages, model)

    async def _call_anthropic(self, system: str, messages: List[Dict[str, str]], model: Optional[str], max_tokens: int) -> str:
        # Claude 3 Sonnet é o padrão para respostas complexas, Haiku para rápidas
        target_model = model or "claude-3-sonnet-20240229"
        
        response = await self.client.messages.create(
            model=target_model,
            max_tokens=max_tokens,
            system=system,
            messages=messages
        )
        return response.content[0].text

    async def _call_ollama(self, system: str, messages: List[Dict[str, str]], model: Optional[str]) -> str:
        target_model = model or self.model
        
        # Converte mensagens para o formato Ollama (incluindo System prompt como mensagem inicial se necessário)
        ollama_messages = [{"role": "system", "content": system}] + messages
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": target_model,
                        "messages": ollama_messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.7
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]
            except Exception as e:
                logger.error("llm.ollama_failed", error=str(e))
                return f"Erro na comunicação com o motor local (Ollama): {str(e)}"

    @property
    def messages(self):
        """Camada de compatibilidade para código que espera o formato client.messages.create"""
        return self

    async def create(self, **kwargs) -> Any:
        """Proxy para create_message mantendo compatibilidade com Anthropic SDK"""
        system = kwargs.get("system", "")
        messages = kwargs.get("messages", [])
        model = kwargs.get("model")
        max_tokens = kwargs.get("max_tokens", 1000)
        
        response_text = await self.create_message(system, messages, model, max_tokens)
        
        # Envelopa em um objeto que simula a resposta do Anthropic para não quebrar .content[0].text
        class MockContent:
            def __init__(self, text):
                self.text = text
        
        class MockResponse:
            def __init__(self, text):
                self.content = [MockContent(text)]
        
        return MockResponse(response_text)
