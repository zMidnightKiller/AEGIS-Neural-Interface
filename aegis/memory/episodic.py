"""
aegis/memory/episodic.py

Memria episdica utilizando ChromaDB para busca semntica de interaes passadas.
"""
from __future__ import annotations

import uuid
from typing import Any, List, Optional

import chromadb
import structlog
from chromadb.utils import embedding_functions

from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)


class EpisodicMemory:
    """
    Gerencia a memria de longo prazo (episdica) usando ChromaDB.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        self.settings = get_settings()
        self.persist_directory = persist_directory or self.settings.CHROMA_PERSIST_DIR
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Configurao de Embeddings com Fallback
        self.embedding_function = self._setup_embedding_function()
        
        self.collection = self.client.get_or_create_collection(
            name="episodes",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

    def _setup_embedding_function(self) -> Any:
        """Configura a funo de embedding (OpenAI -> Fallback)."""
        api_key = self.settings.OPENAI_API_KEY
        if api_key:
            logger.info("episodic_memory.using_openai_embeddings")
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key.get_secret_value(),
                model_name="text-embedding-3-small"
            )
        else:
            logger.warning("episodic_memory.openai_key_missing", fallback="default")
            # DefaultEmbeddingFunction usa Sentence Transformers localmente
            return embedding_functions.DefaultEmbeddingFunction()

    async def save_episode(self, text: str, metadata: Optional[dict] = None) -> str:
        """
        Salva um novo episdio na memria.

        Args:
            text: O contedo textual do episdio.
            metadata: Metadados associados (ex: session_id, timestamp).

        Returns:
            O ID do episdio salvo.
        """
        episode_id = str(uuid.uuid4())
        logger.info("episodic_memory.saving_episode", episode_id=episode_id)
        
        try:
            # ChromaDB PersistentClient  sncrono, mas expomos como async para o Engine
            self.collection.add(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[episode_id]
            )
            return episode_id
        except Exception as e:
            logger.error("episodic_memory.save_failed", error=str(e))
            raise

    async def search_similar(self, query: str, threshold: float = 0.75, n: int = 5) -> List[dict[str, Any]]:
        """
        Busca episdios similares  query.

        Args:
            query: O texto de busca.
            threshold: Limiar de similaridade (0-1).
            n: Nmero mximo de resultados.

        Returns:
            Lista de episdios encontrados.
        """
        logger.info("episodic_memory.searching", query=query, threshold=threshold)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n,
                include=["documents", "metadatas", "distances"]
            )
            
            formatted_results = []
            if results["documents"] and results["distances"]:
                for i in range(len(results["documents"][0])):
                    distance = results["distances"][0][i]
                    # Cosine distance no Chroma: 0 = idntico, 1 = ortogonal, 2 = oposto
                    # Similaridade = 1 - distncia
                    similarity = 1 - distance
                    
                    if similarity >= threshold:
                        formatted_results.append({
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "similarity": similarity
                        })
            
            logger.info("episodic_memory.search_completed", matches=len(formatted_results))
            return formatted_results
        except Exception as e:
            logger.error("episodic_memory.search_failed", error=str(e))
            return []

    async def get_recent(self, n: int = 5) -> List[dict[str, Any]]:
        """
        Retorna os episódios mais recentes (peek).
        """
        try:
            results = self.collection.peek(limit=n)
            
            formatted_results = []
            if results["ids"]:
                for i in range(len(results["ids"])):
                    formatted_results.append({
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i],
                        "id": results["ids"][i]
                    })
            return formatted_results
        except Exception as e:
            logger.error("episodic_memory.get_recent_failed", error=str(e))
            return []

    def get_stats(self) -> dict[str, Any]:
        """Retorna estatísticas da coleção de memória."""
        try:
            return {
                "count": self.collection.count(),
                "name": self.collection.name,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            logger.error("episodic_memory.get_stats_failed", error=str(e))
            return {"count": 0, "error": str(e)}
