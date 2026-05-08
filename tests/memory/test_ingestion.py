"""
tests/memory/test_ingestion.py

Testes para o pipeline de ingestão de documentos.
Moca o ResourceGuard e bibliotecas externas.
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from aegis.memory.ingestion import DocumentIngester

@pytest.fixture
def mock_resource_guard():
    """ResourceGuard sempre retorna SAFE em testes."""
    with patch("aegis.core.resource_guard.ResourceGuard.get_instance") as mock:
        guard = MagicMock()
        guard.assert_safe = AsyncMock()
        guard.wait_for_safe = AsyncMock()
        guard.is_safe_for = MagicMock(return_value=True)
        mock.return_value = guard
        yield guard

@pytest.fixture
def temp_data_dir(tmp_path):
    """Cria um diretório temporário para dados."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    inbox = data_dir / "inbox"
    inbox.mkdir()
    return data_dir

@pytest.mark.asyncio
async def test_ingest_txt_file(mock_resource_guard, temp_data_dir):
    # Setup
    with patch("aegis.core.config.get_settings") as mock_settings:
        settings = MagicMock()
        settings.AEGIS_DATA_DIR = str(temp_data_dir)
        mock_settings.return_value = settings
        
        ingester = DocumentIngester()
        test_file = temp_data_dir / "inbox" / "test.txt"
        content = "Este é um documento de teste.\n\nContém dois parágrafos para validar o chunking."
        test_file.write_text(content, encoding="utf-8")
        
        # Action
        chunks = await ingester.ingest_file(test_file)
        
        # Assert
        assert len(chunks) > 0
        assert chunks[0]["content"] == content.strip()
        assert chunks[0]["metadata"]["source"] == str(test_file)
        # is_safe_for deve ser chamado, mas wait_for_safe não se is_safe_for retornar True
        mock_resource_guard.is_safe_for.assert_called_with("ingest")

@pytest.mark.asyncio
async def test_ingest_duplicate_file(mock_resource_guard, temp_data_dir):
    with patch("aegis.core.config.get_settings") as mock_settings:
        settings = MagicMock()
        settings.AEGIS_DATA_DIR = str(temp_data_dir)
        mock_settings.return_value = settings
        
        ingester = DocumentIngester()
        test_file = temp_data_dir / "inbox" / "dup.txt"
        test_file.write_text("Conteúdo duplicado", encoding="utf-8")
        
        # Primeira vez
        chunks1 = await ingester.ingest_file(test_file)
        assert len(chunks1) == 1
        
        # Segunda vez (mesmo conteúdo)
        chunks2 = await ingester.ingest_file(test_file)
        assert len(chunks2) == 0 # Deve ser filtrado

@pytest.mark.asyncio
async def test_chunking_logic(mock_resource_guard, temp_data_dir):
    with patch("aegis.core.config.get_settings") as mock_settings:
        settings = MagicMock()
        settings.AEGIS_DATA_DIR = str(temp_data_dir)
        mock_settings.return_value = settings
        
        ingester = DocumentIngester()
        
        # Criar texto longo (> 2000 chars)
        long_text = ("Parágrafo longo.\n\n" * 200) # ~3600 chars
        
        chunks = ingester._create_chunks(long_text, "long.txt")
        
        assert len(chunks) > 1
        # Verificar overlap
        assert chunks[0]["metadata"]["end_index"] > chunks[1]["metadata"]["start_index"]
        assert chunks[1]["metadata"]["start_index"] == chunks[0]["metadata"]["end_index"] - 200

@pytest.mark.asyncio
async def test_unsupported_format(mock_resource_guard, temp_data_dir):
    with patch("aegis.core.config.get_settings") as mock_settings:
        settings = MagicMock()
        settings.AEGIS_DATA_DIR = str(temp_data_dir)
        mock_settings.return_value = settings
        
        ingester = DocumentIngester()
        bad_file = temp_data_dir / "inbox" / "test.exe"
        bad_file.write_bytes(b"\x00\x01\x02")
        
        chunks = await ingester.ingest_file(bad_file)
        assert len(chunks) == 0

@pytest.mark.asyncio
async def test_pdf_extraction_mocked(mock_resource_guard, temp_data_dir):
    with patch("aegis.core.config.get_settings") as mock_settings:
        settings = MagicMock()
        settings.AEGIS_DATA_DIR = str(temp_data_dir)
        mock_settings.return_value = settings
        
        # Mocking the library dynamic import
        with patch("aegis.memory.ingestion.DocumentIngester._extract_pdf") as mock_extract:
            mock_extract.return_value = "Texto do PDF"
            
            ingester = DocumentIngester()
            pdf_file = temp_data_dir / "inbox" / "test.pdf"
            pdf_file.write_bytes(b"%PDF-1.4")
            
            chunks = await ingester.ingest_file(pdf_file)
            assert len(chunks) == 1
            assert chunks[0]["content"] == "Texto do PDF"
