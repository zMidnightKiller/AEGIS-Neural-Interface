import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aegis.memory.semantic import SemanticMemory

@pytest.fixture
def mock_settings():
    with patch("aegis.memory.semantic.get_settings") as mock:
        settings = MagicMock()
        settings.NEO4J_URI = "bolt://localhost:7687"
        # Mock SecretStr
        password_mock = MagicMock()
        password_mock.get_secret_value.return_value = "password"
        settings.NEO4J_PASSWORD = password_mock
        mock.return_value = settings
        yield settings

@pytest.fixture
async def memory(mock_settings):
    with patch("aegis.memory.semantic.AsyncGraphDatabase.driver") as mock_driver:
        # Mock the driver and its methods
        driver_instance = MagicMock()
        driver_instance.close = AsyncMock()
        mock_driver.return_value = driver_instance
        
        mem = SemanticMemory()
        yield mem
        await mem.close()

@pytest.mark.asyncio
class TestSemanticMemory:
    async def test_save_fact(self, memory):
        # Mock session and run
        mock_session = AsyncMock()
        memory.driver.session.return_value.__aenter__.return_value = mock_session
        
        await memory.save_fact("Python", "IS_A", "Language", {"level": "high"})
        
        # Verify query was called
        mock_session.run.assert_called_once()
        args, kwargs = mock_session.run.call_args
        assert "MERGE (c1:Concept {name: $c1_name})" in args[0]
        assert "MERGE (c1)-[r:IS_A]->(c2)" in args[0]
        assert kwargs["c1_name"] == "Python"
        assert kwargs["c2_name"] == "Language"
        assert kwargs["metadata"] == {"level": "high"}

    async def test_update_preference(self, memory):
        mock_session = AsyncMock()
        memory.driver.session.return_value.__aenter__.return_value = mock_session
        
        await memory.update_preference("Luan", "Coffee", "LIKES")
        
        mock_session.run.assert_called_once()
        args, kwargs = mock_session.run.call_args
        assert "MERGE (u:User {name: $user_name})" in args[0]
        assert "MERGE (u)-[:LIKES]->(e)" in args[0]
        assert kwargs["user_name"] == "Luan"
        assert kwargs["entity_name"] == "Coffee"

    async def test_get_user_profile(self, memory):
        mock_session = AsyncMock()
        memory.driver.session.return_value.__aenter__.return_value = mock_session
        
        # Mock result stream
        mock_result = AsyncMock()
        # Mock the async iterator behavior
        mock_result.__aiter__.return_value = iter([
            {"relation": "PREFERS", "entity": "Linux"},
            {"relation": "LIKES", "entity": "Python"}
        ])
        mock_session.run.return_value = mock_result
        
        profile = await memory.get_user_profile("Luan")
        
        assert len(profile) == 2
        assert profile[0]["entity"] == "Linux"
        assert profile[1]["relation"] == "LIKES"

    async def test_query_graph(self, memory):
        mock_session = AsyncMock()
        memory.driver.session.return_value.__aenter__.return_value = mock_session
        
        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = iter([
            {"count": 10}
        ])
        mock_session.run.return_value = mock_result
        
        result = await memory.query_graph("MATCH (n) RETURN count(n) as count")
        
        assert len(result) == 1
        assert result[0]["count"] == 10

    async def test_extract_entities_from_text(self, memory):
        # Mock Anthropic response
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"user_name": "Luan", "preferences": [{"entity": "Rust", "relation": "LIKES"}], "facts": []}'
        mock_response.content = [mock_content]
        memory.anthropic_client.messages.create = AsyncMock(return_value=mock_response)
        
        # Mock Neo4j session
        mock_session = AsyncMock()
        memory.driver.session.return_value.__aenter__.return_value = mock_session
        
        result = await memory.extract_entities_from_text("Eu gosto de Rust.")
        
        assert result["user_name"] == "Luan"
        assert len(result["preferences"]) == 1
        assert result["preferences"][0]["entity"] == "Rust"
        
        # Verify Neo4j was called to save the preference
        assert mock_session.run.called
