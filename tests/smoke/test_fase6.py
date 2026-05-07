"""
tests/smoke/test_fase6.py

Smoke test para a Fase 6 - Interface Galáctica Neural.
Valida a emissão de eventos de voz e mudança de modo via WebSocket.
"""
import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from aegis.interfaces.api import app

@pytest.mark.asyncio
async def test_galaxy_visual_events_emission():
    """Valida se os eventos visuais da galáxia são emitidos corretamente via WebSocket."""
    # Como o TestClient de WebSocket é síncrono no FastAPI/Starlette padrão,
    # usamos o TestClient normal para simular a conexão.
    client = TestClient(app)
    
    with client.websocket_connect("/ws/test_session_fase6") as websocket:
        # 1. Testar evento de 'thinking' ao enviar mensagem
        websocket.send_json({"text": "Olá galáxia", "mode": "STANDARD"})
        
        # Recebe status 'thinking'
        response = websocket.receive_json()
        assert response["type"] == "status"
        assert response["status"] == "thinking"
        
        # 2. Testar evento de voz (se não for SILENT)
        # O backend deve emitir eventos via event_bus que o WS captura
        # Nota: O Engine emite 'agent_started', 'tool_called', etc.
        
        # Aguarda a resposta final (que inclui áudio no JSON)
        response = websocket.receive_json()
        assert response["type"] == "message"
        assert "text" in response
        assert "audio" in response # Deve ter áudio pois o modo é STANDARD

@pytest.mark.asyncio
async def test_operating_mode_visual_impact():
    """Valida se a troca de modo é aceita e refletida na sessão."""
    client = TestClient(app)
    
    with client.websocket_connect("/ws/test_session_mode") as websocket:
        # Testar modo SILENT
        websocket.send_json({"text": "Modo silêncio", "mode": "SILENT"})
        
        # Pula o status 'thinking'
        websocket.receive_json()
        
        response = websocket.receive_json()
        assert response["type"] == "message"
        assert response.get("audio") is None # No SILENT não deve ter áudio

if __name__ == "__main__":
    pytest.main([__file__])
