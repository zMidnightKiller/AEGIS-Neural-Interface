import pytest
from unittest.mock import MagicMock, patch
from aegis.memory.episodic import EpisodicMemory

@pytest.fixture
def mock_settings():
    with patch("aegis.memory.episodic.get_settings") as mock:
        mock_settings_obj = MagicMock()
        mock_settings_obj.CHROMA_PERSIST_DIR = ":memory:"
        mock_settings_obj.OPENAI_API_KEY = None
        mock.return_value = mock_settings_obj
        yield mock

@pytest.fixture
def memory(mock_settings):
    with patch("chromadb.PersistentClient") as mock_client:
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        # Mocking embedding function setup to avoid real calls
        with patch("chromadb.utils.embedding_functions.DefaultEmbeddingFunction"):
            mem = EpisodicMemory()
            mem.collection = mock_collection
            return mem

class TestEpisodicMemory:
    @pytest.mark.asyncio
    async def test_save_episode(self, memory):
        episode_id = await memory.save_episode("Test content", {"key": "value"})
        assert episode_id is not None
        memory.collection.add.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_search_similar_filters_by_threshold(self, memory):
        memory.collection.query.return_value = {
            "documents": [["Match 1", "Match 2"]],
            "metadatas": [[{"id": 1}, {"id": 2}]],
            "distances": [[0.1, 0.4]] # Similarity 0.9 and 0.6
        }
        
        # Search with threshold 0.75 (only 0.9 similarity should pass)
        results = await memory.search_similar("query", threshold=0.75)
        
        assert len(results) == 1
        assert results[0]["content"] == "Match 1"
        assert abs(results[0]["similarity"] - 0.9) < 0.001

    @pytest.mark.asyncio
    async def test_search_similar_empty_results(self, memory):
        memory.collection.query.return_value = {
            "documents": None,
            "metadatas": None,
            "distances": None
        }
        results = await memory.search_similar("query")
        assert results == []

    @pytest.mark.asyncio
    async def test_get_recent(self, memory):
        memory.collection.peek.return_value = {
            "ids": ["id1"],
            "documents": ["doc1"],
            "metadatas": [{"m1": "v1"}]
        }
        results = await memory.get_recent(n=1)
        assert len(results) == 1
        assert results[0]["id"] == "id1"

    @pytest.mark.asyncio
    async def test_save_episode_failure(self, memory):
        memory.collection.add.side_effect = Exception("Chroma error")
        with pytest.raises(Exception) as exc:
            await memory.save_episode("content")
        assert "Chroma error" in str(exc.value)
