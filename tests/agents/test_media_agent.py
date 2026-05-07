"""
tests/agents/test_media_agent.py

Testes unitários para o MediaAgent e suas ferramentas.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aegis.agents.media import MediaAgent
from aegis.core.context import Context
from aegis.tools.base import ToolResult

@pytest.fixture
def media_agent():
    return MediaAgent()

@pytest.fixture
def context():
    return Context(session_id="test_session")

@pytest.mark.asyncio
async def test_media_agent_routing_to_vision(media_agent, context):
    """Testa se o agente roteia corretamente para a ferramenta de visão."""
    task = "Analise esta imagem: https://example.com/photo.jpg"
    
    with patch("aegis.agents.media.VisionTool.execute", new_callable=AsyncMock) as mock_vision:
        mock_vision.return_value = ToolResult(success=True, data="Uma foto de um gato.")
        
        result = await media_agent.run(task, context)
        
        assert result.success is True
        assert "Análise da Imagem" in result.output
        assert "vision" in result.tools_used
        mock_vision.assert_called_once()

@pytest.mark.asyncio
async def test_media_agent_routing_to_generation(media_agent, context):
    """Testa se o agente roteia corretamente para a ferramenta de geração."""
    task = "Gere uma imagem de um astronauta em Marte."
    
    with patch("aegis.agents.media.ImageGenerationTool.execute", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ToolResult(success=True, data="https://openai.com/image.png")
        
        result = await media_agent.run(task, context)
        
        assert result.success is True
        assert "Imagem gerada com sucesso" in result.output
        assert "image_generation" in result.tools_used
        mock_gen.assert_called_once()

@pytest.mark.asyncio
async def test_media_agent_vision_no_source(media_agent, context):
    """Testa o comportamento quando nenhuma fonte de imagem é fornecida."""
    task = "Analise esta imagem que eu te mandei." # Sem URL ou caminho
    
    result = await media_agent.run(task, context)
    
    assert result.success is False
    assert "Não consegui identificar uma fonte" in result.output

@pytest.mark.asyncio
async def test_vision_tool_execute():
    """Testa a execução da VisionTool diretamente."""
    from aegis.tools.vision import VisionTool
    
    # Mock do cliente Anthropic
    with patch("aegis.tools.vision.AsyncAnthropic") as mock_anthropic:
        mock_instance = mock_anthropic.return_value
        mock_instance.messages.create = AsyncMock(return_value=MagicMock(content=[MagicMock(text="Descricao mockada")]))
        
        tool = VisionTool()
        
        # Mock do fetch de imagem
        with patch("aegis.tools.vision.VisionTool._get_image_data", new_callable=AsyncMock) as mock_data:
            mock_data.return_value = "base64data"
            
            result = await tool.execute(image_source="https://test.com/img.jpg", prompt="O que é isso?")
            
            assert result.success is True
            assert result.data == "Descricao mockada"

@pytest.mark.asyncio
async def test_image_generation_tool_execute():
    """Testa a execução da ImageGenerationTool diretamente."""
    from aegis.tools.image_generation import ImageGenerationTool
    
    # Mock do cliente OpenAI
    with patch("aegis.tools.image_generation.AsyncOpenAI") as mock_openai:
        mock_instance = mock_openai.return_value
        mock_instance.images.generate = AsyncMock(return_value=MagicMock(
            data=[MagicMock(url="http://gen-image.url", revised_prompt="revised prompt")]
        ))
        
        tool = ImageGenerationTool()
        # Garante que o cliente é instanciado (simula presença de chave)
        tool.client = mock_instance
        
        result = await tool.execute(prompt="Um dragão azul.")
        
        assert result.success is True
        assert result.data == "http://gen-image.url"
        assert result.metadata["revised_prompt"] == "revised prompt"
