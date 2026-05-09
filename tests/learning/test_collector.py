import pytest
import sqlite3
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from aegis.learning.collector import TrainingDataCollector

@pytest.fixture
def mock_db_path(tmp_path):
    return tmp_path / "dataset.sqlite"

@pytest.fixture
def mock_inference_engine():
    with patch("aegis.model.inference.InferenceEngineFactory.create") as mock_create:
        engine = MagicMock()
        
        async def mock_generate(*args, **kwargs):
            yield "0.85"
            
        engine.generate = mock_generate
        mock_create.return_value = engine
        yield engine

@pytest.mark.asyncio
async def test_collection_filters(mock_db_path, mock_inference_engine):
    collector = TrainingDataCollector(db_path=str(mock_db_path))
    
    # 1. Very short completion
    await collector.collect("sess1", "prompt", "short answer")
    
    # 2. learn_enabled = False
    long_completion = "Esta é uma resposta adequadamente longa que deve ter mais de vinte palavras para passar no filtro de tamanho do nosso coletor de fine-tuning. " * 2
    await collector.collect("sess2", "prompt", long_completion, learn_enabled=False)
    
    # 3. user_refused = True
    await collector.collect("sess3", "prompt", long_completion, user_refused=True)
    
    # 4. Valid completion
    await collector.collect("sess4", "What is the capital of France?", long_completion)
    
    with sqlite3.connect(mock_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, quality_score FROM training_samples")
        rows = cursor.fetchall()
        
    assert len(rows) == 1
    assert rows[0][0] == "sess4"
    assert rows[0][1] == 0.85

@pytest.mark.asyncio
async def test_export_dataset(mock_db_path, mock_inference_engine):
    collector = TrainingDataCollector(db_path=str(mock_db_path))
    
    long_completion = "Esta é uma resposta adequadamente longa que deve ter mais de vinte palavras para passar no filtro de tamanho do nosso coletor de fine-tuning. " * 2
    
    await collector.collect("sess1", "Prompt 1", long_completion)
    await collector.collect("sess2", "Prompt 2", long_completion)
    
    dataset = collector.export_dataset(min_quality=0.8, format_type="alpaca")
    
    assert len(dataset) == 2
    assert "instruction" in dataset.features
    assert "input" in dataset.features
    assert "output" in dataset.features
    assert "text" in dataset.features
    
    assert dataset[0]["instruction"] == "Prompt 1"
