"""
tests/smoke/test_fase1.py

Smoke Test para a Fase 1 do AEGIS.
Valida o fluxo end-to-end local: Engine + Context + Working Memory + ResourceGuard.
"""
import pytest
import asyncio
import sys
import json
from unittest.mock import AsyncMock, MagicMock, patch

# Mock problematic imports BEFORE importing aegis modules
sys.modules["llama_cpp"] = MagicMock()
sys.modules["pynvml"] = MagicMock()
sys.modules["psutil"] = MagicMock()

from aegis.core.engine import Engine
from aegis.core.models import UserInput, OperatingMode, AgentResponse
from aegis.core.resource_guard import ResourceGuard, ResourceUnsafeError

@pytest.fixture
def mock_local_env():
    """Moca o ambiente local (LLM, GPU, Redis)."""
    with patch("aegis.core.resource_guard.pynvml"), \
         patch("aegis.core.resource_guard.psutil"), \
         patch("aegis.model.inference.InferenceEngineFactory.create") as mock_factory_create, \
         patch("aegis.memory.working.redis.from_url") as mock_redis_fn:
        
        # Setup Mock Engine
        mock_engine = AsyncMock()
        
        # O gerador de tokens deve ser um AsyncIterator
        async def mock_generate(*args, **kwargs):
            yield "Resposta Mockada do AEGIS"
            
        mock_engine.generate = mock_generate
        mock_factory_create.return_value = mock_engine
        
        # Setup Redis Mock
        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = []
        mock_redis_fn.return_value = mock_redis
        
        yield {
            "engine": mock_engine,
            "redis": mock_redis
        }

@pytest.mark.asyncio
async def test_fase1_full_flow(mock_local_env):
    """Valida o fluxo completo de uma requisição na Engine local."""
    engine = Engine()
    await engine.initialize()
    
    # Forçamos o classificador a retornar CHAT para simplificar o smoke test
    with patch.object(engine.classifier, "classify", return_value="CHAT"):
        user_input = UserInput(
            text="Olá AEGIS, como você está?",
            session_id="smoke-test-session",
            mode=OperatingMode.STANDARD
        )
        
        response = await engine.process(user_input)
        
        # Verificações
        assert isinstance(response, AgentResponse)
        assert response.agent_used == "core_engine"
        assert "Resposta Mockada" in response.text
        assert response.latency_ms > 0

@pytest.mark.asyncio
async def test_fase1_operating_modes(mock_local_env):
    """Valida se os modos de operação (BRIEFING, ANALYSIS) são respeitados."""
    engine = Engine()
    await engine.initialize()
    
    # Precisamos capturar o prompt enviado para a engine
    # Como mock_generate é uma função local, vamos usar um SideEffect
    prompts_received = []
    async def side_effect(prompt, *args, **kwargs):
        prompts_received.append(prompt)
        yield "Resposta"
        
    mock_local_env["engine"].generate = side_effect
    
    with patch.object(engine.classifier, "classify", return_value="CHAT"):
        # 1. Modo BRIEFING
        user_input_brief = UserInput(
            text="Teste briefing",
            session_id="mode-test",
            mode=OperatingMode.BRIEFING
        )
        await engine.process(user_input_brief)
        assert any("BRIEFING" in p for p in prompts_received)
        
        # 2. Modo ANALYSIS
        prompts_received.clear()
        user_input_analysis = UserInput(
            text="Teste analysis",
            session_id="mode-test",
            mode=OperatingMode.ANALYSIS
        )
        await engine.process(user_input_analysis)
        assert any("ANALYSIS" in p for p in prompts_received)

@pytest.mark.asyncio
async def test_fase1_resource_guard_blocking(mock_local_env):
    """Valida se a Engine respeita o bloqueio do ResourceGuard."""
    engine = Engine()
    await engine.initialize()
    
    guard = ResourceGuard.get_instance()
    
    # Simula nível STOP
    with patch.object(guard, "check", return_value=AsyncMock(level="STOP")):
        # Forçamos o nível internamente para o assert_safe disparar
        guard.level = "STOP"
        
        user_input = UserInput(
            text="Isso deve falhar",
            session_id="error-test"
        )
        
        response = await engine.process(user_input)
        
        assert "carga pesada" in response.text
        assert response.agent_used == "resource_guard"
        
        # Volta para SAFE
        guard.level = "SAFE"

@pytest.mark.asyncio
async def test_fase1_context_compression_trigger(mock_local_env):
    """Valida se a compressão de contexto é tentada quando o limite é atingido."""
    engine = Engine()
    await engine.initialize()
    
    # Mock do Context.compress_if_needed
    with patch("aegis.core.context.Context.compress_if_needed", new_callable=AsyncMock) as mock_compress:
        user_input = UserInput(text="Provocar compressao", session_id="comp-test")
        await engine.process(user_input)
        
        mock_compress.assert_called_once()
