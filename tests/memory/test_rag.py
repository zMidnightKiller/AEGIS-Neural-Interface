"""
tests/memory/test_rag.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_settings(tmp_path):
    with patch("aegis.memory.rag.get_settings") as mock:
        settings = MagicMock()
        settings.AEGIS_DATA_DIR = str(tmp_path)
        mock.return_value = settings
        yield settings

@pytest.fixture
def mock_episodic():
    with patch("aegis.memory.rag.EpisodicMemory") as mock:
        instance = MagicMock()
        instance.search_similar = AsyncMock(return_value=[
            {"content": "O céu é azul.", "metadata": {"source": "doc1.txt"}, "similarity": 0.8}
        ])
        mock.return_value = instance
        yield instance

@pytest.fixture
def mock_cross_encoder():
    with patch("aegis.memory.rag.RagEngine._get_reranker") as mock:
        instance = MagicMock()
        # Mock predict to return high score for first pair, low for second
        instance.predict.side_effect = lambda pairs: [0.9] * len(pairs)
        mock.return_value = instance
        yield instance

class TestRagEngine:
    @pytest.mark.asyncio
    async def test_hybrid_retrieval(self, mock_settings, mock_episodic, mock_cross_encoder):
        from aegis.memory.rag import RagEngine
        engine = RagEngine()
        
        # Add a keyword result to test FTS
        engine.add_to_fts("O mar é azul.", {"source": "doc2.txt"}, "doc2")
        
        results = await engine.retrieve("azul")
        assert len(results) > 0
        
        # Verify content was found
        contents = [r["content"] for r in results]
        assert "O céu é azul." in contents
        assert "O mar é azul." in contents
        
    @pytest.mark.asyncio
    async def test_fallback_when_slow(self, mock_settings, mock_episodic, mock_cross_encoder):
        from aegis.memory.rag import RagEngine
        engine = RagEngine()
        
        # Mock EpisodicMemory to sleep and simulate slow vector search (> 400ms)
        async def slow_search(*args, **kwargs):
            import asyncio
            await asyncio.sleep(0.5) 
            return [{"content": "Demorado", "metadata": {}, "similarity": 0.9}]
            
        mock_episodic.search_similar = slow_search
        
        results = await engine.retrieve("teste")
        assert len(results) >= 1
        
        # Find the slow result
        slow_res = next((r for r in results if r["content"] == "Demorado"), None)
        assert slow_res is not None
        assert "rerank_score" not in slow_res # Reranking should have been skipped
        
    def test_build_context(self, mock_settings, mock_episodic):
        from aegis.memory.rag import RagEngine
        engine = RagEngine()
        
        results = [
            {"content": "A", "metadata": {"source": "file1.txt"}},
            {"content": "B", "metadata": {"source": "file2.txt"}}
        ]
        
        context = engine.build_context(results)
        assert "Documentos relevantes" in context
        assert "file1.txt" in context
        assert "file2.txt" in context
