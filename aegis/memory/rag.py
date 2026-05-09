"""
aegis/memory/rag.py

RAG Engine: Retrieval Híbrido (ChromaDB + SQLite FTS5) e Reranking (CPU).
Configurado para proteção de VRAM na RTX 3060.
"""
from __future__ import annotations

import asyncio
import time
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any

import structlog

from aegis.core.config import get_settings
from aegis.memory.episodic import EpisodicMemory

logger = structlog.get_logger(__name__)

class RagEngine:
    """
    RAG Engine responsável pelo retrieval híbrido e reranking.
    """
    def __init__(self):
        self.settings = get_settings()
        self.episodic = EpisodicMemory()
        
        db_path = Path(self.settings.AEGIS_DATA_DIR) / "fts.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_fts()
        
        self._reranker = None

    def _init_fts(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                content, metadata UNINDEXED, doc_id UNINDEXED
            )
        ''')
        self.conn.commit()

    def add_to_fts(self, content: str, metadata: dict, doc_id: str):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO documents_fts (content, metadata, doc_id) VALUES (?, ?, ?)",
                (content, json.dumps(metadata), doc_id)
            )
            self.conn.commit()
        except Exception as e:
            logger.error("rag.fts_insert_error", error=str(e))

    def _get_reranker(self):
        if self._reranker is None:
            logger.info("rag.loading_reranker_cpu")
            try:
                from sentence_transformers import CrossEncoder
                # Roda obrigatoriamente na CPU para não competir com LLM pela VRAM (12GB teto)
                self._reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")
            except ImportError:
                logger.error("rag.missing_cross_encoder")
                self._reranker = "missing"
        return self._reranker

    def _search_fts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        try:
            # Filtro básico FTS5. Se falhar por sintaxe, usar fallback seguro
            query_clean = query.replace('"', '').replace("'", "")
            cursor.execute(
                "SELECT content, metadata, doc_id FROM documents_fts WHERE documents_fts MATCH ? ORDER BY rank LIMIT ?",
                (query_clean, limit)
            )
            results = []
            for row in cursor.fetchall():
                meta = {}
                try:
                    meta = json.loads(row[1]) if row[1] else {}
                except json.JSONDecodeError:
                    pass
                results.append({
                    "content": row[0],
                    "metadata": meta,
                    "id": row[2],
                    "similarity": 0.5 # Default base score para keyword search
                })
            return results
        except Exception as e:
            logger.error("rag.fts_search_error", error=str(e), query=query)
            return []

    async def retrieve(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        start_time = time.time()
        
        # 1. Retrieval híbrido (ChromaDB + SQLite)
        vector_results_task = asyncio.create_task(
            self.episodic.search_similar(query, collection_name="documents", n=n_results)
        )
        
        loop = asyncio.get_event_loop()
        fts_results_task = loop.run_in_executor(None, self._search_fts, query, n_results)
        
        vector_results = await vector_results_task
        fts_results = await fts_results_task
        
        # Combinar resultados, priorizando a similaridade do Chroma se houver duplicata
        combined = {}
        for r in vector_results + fts_results:
            content = r["content"]
            if content not in combined:
                combined[content] = r
            else:
                combined[content]["similarity"] = max(combined[content]["similarity"], r["similarity"])
                
        candidates = list(combined.values())
        if not candidates:
            return []
            
        retrieval_time = (time.time() - start_time) * 1000 # em ms
        
        # Se o retrieval demorou mais que 400ms, aborta o reranking para manter a latência final < 600ms
        if retrieval_time > 400:
            logger.warning("rag.retrieval_slow", time_ms=retrieval_time, action="skipping_reranking")
            
            # Registrar no friction-log conforme especificado no PRD para operações longas ou cortes
            friction_log_path = Path("friction-log.md")
            if friction_log_path.exists():
                with open(friction_log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n## [{time.strftime('%Y-%m-%d %H:%M')}] TAREFA 2.5 — RAG Reranking Skipped\n")
                    f.write(f"**Hardware:** RTX 3060 12GB VRAM\n")
                    f.write(f"**Contexto:** Busca híbrida RAG.\n")
                    f.write(f"**Problema:** Retrieval demorou {retrieval_time:.2f}ms (>400ms).\n")
                    f.write(f"**Solução:** Reranking cancelado para evitar latência excessiva.\n")
                    
            return sorted(candidates, key=lambda x: x["similarity"], reverse=True)[:n_results]

        # 2. Reranking (CPU)
        reranker = await loop.run_in_executor(None, self._get_reranker)
        if reranker == "missing":
            return sorted(candidates, key=lambda x: x["similarity"], reverse=True)[:n_results]
            
        pairs = [[query, c["content"]] for c in candidates]
        try:
            scores = await loop.run_in_executor(None, reranker.predict, pairs)
            for i, score in enumerate(scores):
                candidates[i]["rerank_score"] = float(score)
            
            reranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0), reverse=True)
            
            total_time = (time.time() - start_time) * 1000
            logger.info("rag.retrieval_complete", total_time_ms=total_time, matches=len(reranked))
            return reranked[:n_results]
        except Exception as e:
            logger.error("rag.reranking_failed", error=str(e))
            return sorted(candidates, key=lambda x: x["similarity"], reverse=True)[:n_results]

    def build_context(self, results: List[Dict[str, Any]], max_tokens: Optional[int] = None) -> str:
        """
        Monta os documentos para injeção no prompt.
        Respeita AEGIS_CONTEXT_LENGTH.
        """
        if max_tokens is None:
            # Context length padrão é 4096, reservamos 2000 para documentos, deixando folga para prompt e geração
            max_tokens = 2000
            
        context = "Documentos relevantes encontrados:\n\n"
        current_tokens = 0
        
        for r in results:
            content = r["content"]
            # Estimação simples e segura (1 token = ~4 caracteres)
            tokens = len(content) // 4
            
            if current_tokens + tokens > max_tokens:
                break
                
            source = r.get("metadata", {}).get("source", "Unknown")
            context += f"--- Fonte: {source} ---\n{content}\n\n"
            current_tokens += tokens
            
        return context.strip()
