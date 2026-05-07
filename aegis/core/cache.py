"""
aegis/core/cache.py

Sistema de cache semântico para respostas do AEGIS utilizando ChromaDB.
Permite reutilizar respostas para queries similares, economizando tokens e reduzindo latência.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

import chromadb
import structlog
from chromadb.utils import embedding_functions

from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)


class SemanticCache:
    """
    Gerencia o cache semântico de interações usando ChromaDB.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        self.settings = get_settings()
        self.persist_directory = persist_directory or self.settings.CHROMA_PERSIST_DIR
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Configuração de Embeddings (reutiliza lógica da memória episódica)
        self.embedding_function = self._setup_embedding_function()
        
        self.collection = self.client.get_or_create_collection(
            name="semantic_cache",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

    def _setup_embedding_function(self) -> Any:
        """Configura a função de embedding (OpenAI -> Fallback)."""
        api_key = self.settings.OPENAI_API_KEY
        if api_key:
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key.get_secret_value(),
                model_name="text-embedding-3-small"
            )
        else:
            logger.warning("semantic_cache.openai_key_missing", fallback="default")
            return embedding_functions.DefaultEmbeddingFunction()

    async def get(self, query: str) -> Optional[str]:
        """
        Busca uma resposta no cache para uma query similar.

        Args:
            query: O texto da query do usuário.

        Returns:
            A resposta em cache se encontrada e acima do threshold, senão None.
        """
        if not self.settings.ENABLE_SEMANTIC_CACHE:
            return None

        threshold = self.settings.CACHE_SIMILARITY_THRESHOLD
        logger.debug("semantic_cache.checking", query=query, threshold=threshold)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=1,
                include=["documents", "metadatas", "distances"]
            )
            
            if results["documents"] and results["distances"] and len(results["documents"][0]) > 0:
                distance = results["distances"][0][0]
                similarity = 1 - distance
                
                if similarity >= threshold:
                    response = results["metadatas"][0][0].get("response")
                    logger.info(
                        "semantic_cache.hit", 
                        similarity=round(similarity, 4),
                        cache_id=results["ids"][0][0]
                    )
                    return response
            
            logger.debug("semantic_cache.miss")
            return None
        except Exception as e:
            logger.error("semantic_cache.get_failed", error=str(e))
            return None

    async def set(self, query: str, response: str, metadata: Optional[dict] = None) -> None:
        """
        Armazena uma nova resposta no cache.

        Args:
            query: A query original.
            response: A resposta gerada.
            metadata: Metadados adicionais.
        """
        if not self.settings.ENABLE_SEMANTIC_CACHE:
            return

        cache_id = str(uuid.uuid4())
        logger.debug("semantic_cache.saving", cache_id=cache_id)
        
        try:
            # Armazenamos a query como documento (para busca semântica)
            # e a resposta nos metadados
            meta = metadata or {}
            meta["response"] = response
            
            self.collection.add(
                documents=[query],
                metadatas=[meta],
                ids=[cache_id]
            )
        except Exception as e:
            logger.error("semantic_cache.set_failed", error=str(e))
