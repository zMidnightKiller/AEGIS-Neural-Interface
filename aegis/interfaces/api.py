"""
aegis/interfaces/api.py

Interface de API FastAPI e WebSockets para o sistema AEGIS.
Permite comunicacao assincrona e streaming em tempo real.
"""
from __future__ import annotations

import time
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from aegis.core.config import get_settings
from aegis.core.engine import Engine
from aegis.innovation.loop import InnovationLoop
from aegis.core.models import UserInput, OperatingMode
from aegis.core.tasks import process_agent_task
from aegis.core.observability import obs_manager
from aegis.interfaces.voice import VoiceInterface

logger = structlog.get_logger(__name__)

# Instancias globais (singleton)
_engine: Engine | None = None
_voice_interface: VoiceInterface | None = None
_innovation_loop: InnovationLoop | None = None

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine

def get_innovation_loop() -> InnovationLoop:
    global _innovation_loop
    if _innovation_loop is None:
        _innovation_loop = InnovationLoop()
    return _innovation_loop

def get_voice_interface() -> VoiceInterface:
    global _voice_interface
    if _voice_interface is None:
        _voice_interface = VoiceInterface()
    return _voice_interface

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida da aplicacao: setup e teardown."""
    logger.info("api.startup", message="AEGIS API esta iniciando...")
    # Inicializa componentes
    engine = get_engine()
    await engine.initialize()
    
    innovation = get_innovation_loop()
    await innovation.start()
    
    get_voice_interface()
    yield
    logger.info("api.shutdown", message="AEGIS API esta encerrando...")
    if _innovation_loop:
        await _innovation_loop.stop()
    if _voice_interface:
        await _voice_interface.close()

app = FastAPI(
    title="AEGIS AI API",
    description="""
    Interface de comunicacao de alta performance para o sistema AEGIS.
    Suporta streaming via WebSockets, processamento assincrono via Celery e gerenciamento de memoria.
    """,
    version="0.1.0",
    lifespan=lifespan,
    contact={
        "name": "AEGIS Development Team",
        "url": "https://github.com/aegis-ai",
    },
    license_info={
        "name": "Proprietary",
    },
)

# Tags para agrupamento no Swagger
TAGS_METADATA = [
    {"name": "Core", "description": "Endpoints principais de chat e integridade"},
    {"name": "Memory", "description": "Acesso as camadas de memoria do sistema"},
    {"name": "Agents", "description": "Gerenciamento e status dos agentes especializados"},
    {"name": "Voice", "description": "Processamento de audio e voz"},
]
app.openapi_tags = TAGS_METADATA

# Inicializa Observabilidade (Prometheus Metrics)
obs_manager.setup_fastapi(app)

# Configuracao de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em producao, restringir ao dominio do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    """Modelo de requisicao de chat."""
    text: str = Field(..., description="Texto da mensagem do usuario")
    session_id: str = Field(..., description="Identificador unico da sessao")
    mode: OperatingMode = Field(default=OperatingMode.STANDARD, description="Modo de operacao do AEGIS")

class ChatResponse(BaseModel):
    """Modelo de resposta de chat."""
    text: str
    agent_used: str
    tools_used: list[str]
    memory_injected: bool
    latency_ms: int

class ResourceUpdate(BaseModel):
    """Modelo para atualizacao de recursos."""
    vram_used_gb: float
    vram_total_gb: float
    vram_pct: float
    gpu_pct: float
    gpu_temp_c: float
    cpu_pct: float
    ram_used_gb: float
    ram_total_gb: float
    level: str
    paused_ops: list[str]

@app.get("/health", tags=["Core"])
async def health_check():
    """Endpoint de verificacao de integridade."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "0.1.0"
    }

@app.get("/innovation", tags=["Core"])
async def get_innovation_status():
    """Retorna o status do Innovation Loop para o dashboard."""
    innovation = get_innovation_loop()
    return innovation.get_status()

@app.post("/innovation/trigger", tags=["Core"])
async def trigger_innovation_cycle():
    """Dispara manualmente um ciclo de inovação."""
    innovation = get_innovation_loop()
    result = await innovation.trigger(reason="api_request")
    return result

@app.post("/chat", response_model=ChatResponse, tags=["Core"])
async def chat(request: ChatRequest):
    """
    Endpoint sincrono para chat.
    Utilizado para interacoes simples onde o streaming nao e necessario.
    """
    engine = get_engine()
    user_input = UserInput(
        text=request.text,
        session_id=request.session_id,
        mode=request.mode
    )
    
    logger.info("api.chat_request", session_id=request.session_id, text=request.text[:50])
    
    try:
        response = await engine.process(user_input)
        return ChatResponse(
            text=response.text,
            agent_used=response.agent_used,
            tools_used=response.tools_used,
            memory_injected=response.memory_injected,
            latency_ms=response.latency_ms
        )
    except Exception as e:
        logger.error("api.chat_failed", error=str(e), session_id=request.session_id)
        raise HTTPException(status_code=500, detail=f"Erro interno no motor AEGIS: {str(e)}")

@app.get("/innovation", tags=["Innovation"])
async def get_innovation_status():
    """Retorna o status atual do Innovation Loop e histrico de ciclos."""
    loop = get_innovation_loop()
    return loop.get_status()

@app.post("/innovation/trigger", tags=["Innovation"])
async def trigger_innovation(reason: str = "manual"):
    """Dispara manualmente um novo ciclo de inovauo."""
    loop = get_innovation_loop()
    result = await loop.trigger(reason=reason)
    return result

@app.post("/chat/async", tags=["Core"])
async def chat_async(request: ChatRequest):
    """
    Endpoint para disparar processamento assincrono via Celery.
    Retorna o task_id para consulta posterior.
    """
    logger.info("api.chat_async_request", session_id=request.session_id, text=request.text[:50])
    
    # Dispara a tarefa no Celery
    task = process_agent_task.delay(
        text=request.text,
        session_id=request.session_id,
        mode=request.mode.value
    )
    
    return {
        "task_id": task.id,
        "status": "queued",
        "session_id": request.session_id
    }

@app.get("/tasks/{task_id}", tags=["Core"])
async def get_task_status(task_id: str):
    """
    Consulta o status e resultado de uma tarefa do Celery.
    """
    from celery.result import AsyncResult
    from aegis.core.celery_app import celery_app
    
    res = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": res.status,
    }
    
    if res.ready():
        if res.successful():
            response["result"] = res.result
        else:
            response["error"] = str(res.result)
            
    return response

@app.get("/memory/episodes", tags=["Memory"])
async def get_episodes(n: int = 10):
    """Retorna os episodios mais recentes da memoria episodica."""
    engine = get_engine()
    memory_agent = engine.agents.get("memory")
    if not memory_agent:
        return []
    return await memory_agent.episodic.get_recent(n=n)

@app.get("/memory/profile", tags=["Memory"])
async def get_profile(user_name: str = "default_user"):
    """Retorna o perfil semantico do usuario."""
    engine = get_engine()
    memory_agent = engine.agents.get("memory")
    if not memory_agent:
        return []
    return await memory_agent.semantic.get_user_profile(user_name)

@app.get("/sessions/{session_id}", tags=["Core"])
async def get_session_history(session_id: str):
    """Retorna o historico de uma sessao especifica."""
    from aegis.memory.working import WorkingMemory
    memory = WorkingMemory(session_id)
    try:
        history = await memory.get_history(n=50)
        return {"session_id": session_id, "history": history}
    finally:
        await memory.close()

@app.get("/mode", tags=["Core"])
async def get_mode():
    """Retorna o modo de operacao atual do sistema."""
    from aegis.core.config import get_settings
    settings = get_settings()
    return {"mode": settings.AEGIS_MODE}

@app.patch("/mode", tags=["Core"])
async def update_mode(mode: OperatingMode):
    """Atualiza o modo de operacao do sistema."""
    # Nota: Em um sistema real, isso alteraria o estado global ou settings
    # Por enquanto, apenas logamos a intencao de mudanca
    logger.info("api.mode_update", new_mode=mode)
    return {"status": "updated", "new_mode": mode}

@app.get("/model/status", tags=["Core"])
async def get_model_status():
    """Retorna informacoes sobre o modelo ativo e uso de VRAM."""
    from aegis.core.resource_guard import ResourceGuard
    guard = ResourceGuard.get_instance()
    status = await guard.check()
    
    from aegis.core.config import get_settings
    settings = get_settings()
    
    return {
        "model_name": settings.AEGIS_MODEL_NAME,
        "backend": settings.AEGIS_INFERENCE_BACKEND,
        "vram_status": status
    }

@app.get("/learning/status", tags=["Core"])
async def get_learning_status():
    """Retorna o status do pipeline de aprendizado."""
    from aegis.learning.collector import TrainingDataCollector
    collector = TrainingDataCollector()
    stats = await collector.get_stats()
    
    return {
        "samples_collected": stats.get("count", 0),
        "average_quality": stats.get("avg_quality", 0.0),
        "learning_enabled": get_settings().AEGIS_LEARNING_ENABLED
    }

@app.get("/memory/search", tags=["Memory"])
async def search_memory(query: str, n: int = 5):
    """Realiza uma busca na memoria RAG do sistema."""
    engine = get_engine()
    memory_agent = engine.agents.get("memory")
    if not memory_agent:
        # Fallback se o agente de memoria nao estiver carregado
        from aegis.agents.memory import MemoryAgent
        memory_agent = MemoryAgent()
        
    results = await memory_agent.episodic.search_similar(query, n=n)
    return {"query": query, "results": results}

@app.get("/agents/status", tags=["Agents"])
async def get_agents_status():
    """Retorna o status atual dos agentes disponiveis."""
    engine = get_engine()
    agents_status = []
    for name, agent in engine.agents.items():
        # Tenta obter descricao do agente, se disponivel
        desc = getattr(agent, "description", f"Agente especializado {name}")
        agents_status.append({
            "name": name,
            "description": desc,
            "status": "ready"
        })
    return agents_status

@app.post("/voice/transcribe", tags=["Voice"])
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Endpoint para transcricao de audio (STT).
    Recebe um arquivo de audio e retorna o texto transcrito via Whisper.
    """
    voice = get_voice_interface()
    try:
        audio_content = await file.read()
        transcription = await voice.transcribe_audio(
            audio_content, 
            filename=file.filename or "audio.wav"
        )
        
        if transcription is None:
            raise HTTPException(status_code=500, detail="Falha na transcricao do audio")
            
        return {"text": transcription}
    except Exception as e:
        logger.error("api.voice_transcribe_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """
    Endpoint WebSocket para comunicacao bidirecional e streaming.
    """
    from aegis.core.events import event_bus
    
    engine = get_engine()
    await websocket.accept()
    logger.info("api.ws_connected", session_id=session_id)
    
    # Callback para enviar eventos do EventBus para este WebSocket
    async def event_callback(event):
        # Filtra eventos por session_id para evitar vazamento entre sessoes
        if event.data.get("session_id") == session_id:
            try:
                await websocket.send_json({
                    "type": "event",
                    "event_type": event.type,
                    "data": event.data,
                    "timestamp": event.timestamp
                })
            except Exception:
                # Se falhar (ex: socket fechado), o loop principal tratara
                pass

    event_bus.subscribe(event_callback)

    try:
        while True:
            # Recebe mensagem do cliente
            try:
                data = await websocket.receive_json()
            except Exception as e:
                logger.warning("api.ws_invalid_json", session_id=session_id, error=str(e))
                await websocket.send_json({"type": "error", "message": "Formato JSON invalido"})
                continue

            text = data.get("text")
            mode_val = data.get("mode", "STANDARD")
            
            if not text:
                logger.debug("api.ws_empty_message", session_id=session_id)
                continue

            try:
                mode = OperatingMode(mode_val)
            except ValueError:
                mode = OperatingMode.STANDARD

            user_input = UserInput(text=text, session_id=session_id, mode=mode)
            
            logger.info("api.ws_message_received", session_id=session_id, text=text[:50])
            
            # Envia status de "processando"
            await websocket.send_json({
                "type": "status", 
                "status": "thinking",
                "timestamp": time.time()
            })
            
            try:
                response = await engine.process(user_input)
                
                # Gera áudio se não estiver no modo SILENT
                audio_base64 = None
                if mode != OperatingMode.SILENT:
                    voice = get_voice_interface()
                    audio_bytes = await voice.speak_text(response.text)
                    if audio_bytes:
                        import base64
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

                # Envia resposta final
                await websocket.send_json({
                    "type": "message",
                    "text": response.text,
                    "audio": audio_base64,
                    "agent_used": response.agent_used,
                    "tools_used": response.tools_used,
                    "memory_injected": response.memory_injected,
                    "latency_ms": response.latency_ms,
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error("api.ws_process_failed", session_id=session_id, error=str(e))
                await websocket.send_json({
                    "type": "error",
                    "message": f"Erro no processamento: {str(e)}"
                })
            
    except WebSocketDisconnect:
        logger.info("api.ws_ws_disconnect", session_id=session_id)
    except Exception as e:
        logger.error("api.ws_critical_error", session_id=session_id, error=str(e))
        try:
            await websocket.close(code=1011) # Internal Error
        except:
            pass
    finally:
        event_bus.unsubscribe(event_callback)
        logger.info("api.ws_cleanup_complete", session_id=session_id)

@app.websocket("/ws/resources")
async def websocket_resources_endpoint(websocket: WebSocket):
    """
    WebSocket para streaming contínuo de métricas do ResourceGuard.
    """
    from aegis.core.resource_guard import ResourceGuard
    guard = ResourceGuard.get_instance()
    
    await websocket.accept()
    logger.info("api.ws_resources_connected")
    
    try:
        while True:
            status = await guard.check()
            await websocket.send_json(asdict(status))
            # Atualiza a cada 2 segundos conforme PRD
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info("api.ws_resources_disconnected")
    except Exception as e:
        logger.error("api.ws_resources_error", error=str(e))
        try:
            await websocket.close()
        except:
            pass

@app.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """
    WebSocket para streaming de eventos do sistema (para Galaxy UI).
    """
    from aegis.core.events import event_bus
    
    await websocket.accept()
    logger.info("api.ws_events_connected")
    
    async def event_callback(event):
        try:
            await websocket.send_json(event.to_dict())
        except Exception:
            pass

    event_bus.subscribe(event_callback)
    
    try:
        while True:
            # Mantem a conexao aberta, recebendo pings ou apenas esperando
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("api.ws_events_disconnected")
    finally:
        event_bus.unsubscribe(event_callback)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("aegis.interfaces.api:app", host="0.0.0.0", port=8000, reload=True)
