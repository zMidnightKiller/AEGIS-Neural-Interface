import sqlite3
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import re

import structlog
from datasets import Dataset

from aegis.core.config import get_settings
from aegis.model.inference import InferenceEngineFactory

logger = structlog.get_logger(__name__)
settings = get_settings()

class TrainingDataCollector:
    """Coletor de dados de treino de conversas para fine-tuning na RTX 3060."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = Path(settings.AEGIS_DATA_DIR) / "training" / "dataset.sqlite"
        else:
            self.db_path = Path(db_path)
            
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._engine = InferenceEngineFactory.create()

    def _init_db(self):
        """Inicializa o banco de dados SQLite para amostras."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    prompt TEXT,
                    completion TEXT,
                    quality_score REAL,
                    learn_enabled BOOLEAN,
                    user_refused BOOLEAN,
                    created_at TIMESTAMP
                )
            ''')
            conn.commit()

    async def _evaluate_quality(self, prompt: str, completion: str) -> float:
        """Avalia a qualidade da resposta usando o modelo local para gerar um score."""
        eval_prompt = (
            "Como um avaliador objetivo, dê uma nota de 0.0 a 1.0 para a seguinte resposta a uma instrução.\n"
            "Responda apenas com o número decimal.\n"
            f"Instrução: {prompt}\n"
            f"Resposta: {completion}\n"
            "Nota:"
        )
        try:
            response_chunks = []
            async for token in self._engine.generate(eval_prompt, max_tokens=10, temperature=0.1, stream=False):
                response_chunks.append(token)
                
            response = "".join(response_chunks).strip()
            
            # Extração simples de float
            match = re.search(r"0\.\d+|1\.0", response)
            if match:
                return float(match.group(0))
            return 0.5
        except Exception as e:
            logger.error("learning.eval_failed", error=str(e))
            return 0.5 # Fallback conservador

    async def collect(
        self,
        session_id: str,
        prompt: str,
        completion: str,
        learn_enabled: bool = True,
        user_refused: bool = False
    ):
        """Coleta um par prompt/completion no banco de dados se passar nos filtros."""
        if not learn_enabled:
            logger.debug("learning.collection_skipped.learn_disabled", session_id=session_id)
            return
            
        if user_refused:
            logger.debug("learning.collection_skipped.user_refused", session_id=session_id)
            return

        # Filtro de tamanho: completações muito curtas (< 30 palavras/tokens)
        if len(completion.split()) < 20:
            logger.debug("learning.collection_skipped.too_short", session_id=session_id)
            return
            
        quality_score = await self._evaluate_quality(prompt, completion)
        
        def _save():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO training_samples 
                    (session_id, prompt, completion, quality_score, learn_enabled, user_refused, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (session_id, prompt, completion, quality_score, learn_enabled, user_refused, datetime.now().isoformat()))
                conn.commit()
                
        await asyncio.to_thread(_save)
            
        logger.info("learning.sample_collected", session_id=session_id, quality=quality_score)

    def export_dataset(self, min_quality: float = 0.65, format_type: str = "alpaca") -> Dataset:
        """Exporta os dados filtrados como um objeto Dataset (HuggingFace)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT prompt, completion, quality_score 
                FROM training_samples 
                WHERE learn_enabled = 1 
                  AND user_refused = 0 
                  AND quality_score >= ?
            ''', (min_quality,))
            
            rows = cursor.fetchall()
            
        data = {
            "instruction": [],
            "input": [],
            "output": [],
            "text": []
        }
        
        for row in rows:
            prompt = row["prompt"]
            completion = row["completion"]
            
            if format_type == "alpaca":
                data["instruction"].append(prompt)
                data["input"].append("")
                data["output"].append(completion)
                text = f"### Instruction:\n{prompt}\n\n### Response:\n{completion}"
                data["text"].append(text)
                
        dataset = Dataset.from_dict(data)
        logger.info("learning.dataset_exported", format=format_type, num_samples=len(dataset))
        return dataset
