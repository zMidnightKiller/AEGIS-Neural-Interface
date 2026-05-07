import json
import time
from typing import Any, List, Optional

class MockRedis:
    def __init__(self):
        self.data = {}
    
    async def rpush(self, key: str, value: str):
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(value)
    
    async def lrange(self, key: str, start: int, stop: int):
        lst = self.data.get(key, [])
        if not lst: return []
        # Simplified slicing
        if stop == -1:
            return lst[start:]
        return lst[start:stop+1]
    
    async def expire(self, key: str, ttl: int):
        pass
    
    async def delete(self, key: str):
        if key in self.data:
            del self.data[key]
            
    async def close(self):
        pass

class MockChroma:
    def __init__(self):
        self.collections = {}
        
    def get_or_create_collection(self, name: str, **kwargs):
        if name not in self.collections:
            self.collections[name] = []
        return self
        
    def add(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        # Implementation depends on the library usage
        pass
        
    def query(self, query_texts: List[str], n_results: int = 5, **kwargs):
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

class MockNeo4j:
    def __init__(self):
        self.nodes = []
        self.rels = []
        
    def execute_query(self, query: str, **kwargs):
        return [], None, None
    
    def close(self):
        pass

import asyncio

class MockEngine:
    async def initialize(self):
        pass
        
    async def process(self, user_input):
        await asyncio.sleep(0.5) # Simula latência de forma assíncrona
        from aegis.core.models import AegisResponse
        return AegisResponse(
            text=f"MOCK_RESPONSE: Recebi sua mensagem: '{user_input.text}'. O sistema está operando em modo de demonstração local.",
            agent_used="innovation_agent",
            tools_used=["mock_tool"],
            memory_injected=True,
            latency_ms=500
        )
    
    @property
    def agents(self):
        return {}

def patch_aegis_for_demo():
    """Patch AEGIS components to use mocks for demonstration purposes."""
    import aegis.memory.working as working
    import aegis.memory.episodic as episodic
    import aegis.memory.semantic as semantic
    import aegis.core.engine as engine_module
    
    # Mock Engine
    engine_module.Engine = MockEngine
    
    # Mock Redis in WorkingMemory
    working.redis = type('obj', (object,), {'from_url': lambda *a, **k: MockRedis()})
    
    # Mock ChromaDB in EpisodicMemory
    episodic.chromadb = type('obj', (object,), {
        'PersistentClient': lambda *a, **k: MockChroma(),
        'Settings': type('obj', (object,), {})
    })
    
    # Mock Neo4j in SemanticMemory
    semantic.GraphDatabase = type('obj', (object,), {'driver': lambda *a, **k: MockNeo4j()})
    
    print("AEGIS patched with MOCKS (including Engine) for Local Demo.")

