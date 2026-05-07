"""
aegis/memory/semantic.py

Memória semântica utilizando Neo4j para armazenar fatos, preferências e relações.
"""
from __future__ import annotations

import json
import structlog
from anthropic import AsyncAnthropic
from neo4j import AsyncGraphDatabase
from typing import Any, Dict, List, Optional
from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)

EXTRACTION_SYSTEM_PROMPT = """
Você é um extrator de conhecimento para o sistema AEGIS. 
Sua tarefa é extrair entidades, fatos e preferências de uma conversa entre um usuário e um assistente.

Regras de Extração:
1. Identifique o Nome do Usuário se mencionado.
2. Identifique Preferências: (User)-[PREFERS|LIKES|DISLIKES]->(Entity).
3. Identifique Fatos Conceituais: (Concept)-[IS_A|RELATED_TO|PART_OF]->(Concept).
4. Retorne APENAS um JSON válido no formato abaixo.

Formato de Saída:
{
  "user_name": "nome_do_usuario_ou_null",
  "preferences": [
    {"entity": "nome_da_entidade", "relation": "PREFERS|LIKES|DISLIKES"}
  ],
  "facts": [
    {"subject": "conceito1", "relation": "IS_A|RELATED_TO|PART_OF", "object": "conceito2", "metadata": {}}
  ]
}
"""


class SemanticMemory:
    """
    Gerencia a memória semântica (grafo de conhecimento) usando Neo4j.
    """

    def __init__(self, uri: Optional[str] = None, password: Optional[str] = None):
        self.settings = get_settings()
        self.uri = uri or self.settings.NEO4J_URI
        # O Neo4j usa o usuário 'neo4j' por padrão
        self.password = password or (
            self.settings.NEO4J_PASSWORD.get_secret_value() 
            if self.settings.NEO4J_PASSWORD else ""
        )
        self.driver = AsyncGraphDatabase.driver(self.uri, auth=("neo4j", self.password))
        self.anthropic_client = AsyncAnthropic(api_key=self.settings.ANTHROPIC_API_KEY.get_secret_value())

    async def close(self):
        """Fecha a conexão com o driver."""
        await self.driver.close()

    async def save_fact(self, concept1: str, relation: str, concept2: str, metadata: Optional[Dict] = None):
        """
        Salva um fato no grafo: (Concept1)-[RELATION]->(Concept2).
        """
        rel_type = relation.upper().replace(" ", "_")
        query = (
            f"MERGE (c1:Concept {{name: $c1_name}}) "
            f"MERGE (c2:Concept {{name: $c2_name}}) "
            f"MERGE (c1)-[r:{rel_type}]->(c2) "
            f"SET r += $metadata"
        )
        logger.info("semantic_memory.save_fact", c1=concept1, rel=rel_type, c2=concept2)
        try:
            async with self.driver.session() as session:
                await session.run(query, c1_name=concept1, c2_name=concept2, metadata=metadata or {})
        except Exception as e:
            logger.error("semantic_memory.save_fact_failed", error=str(e), c1=concept1, rel=rel_type)
            raise

    async def update_preference(self, user_name: str, entity: str, preference_type: str = "PREFERS"):
        """
        Atualiza a preferência do usuário: (User)-[PREFERS]->(Entity).
        """
        pref_type = preference_type.upper().replace(" ", "_")
        query = (
            "MERGE (u:User {name: $user_name}) "
            "MERGE (e:Entity {name: $entity_name}) "
            f"MERGE (u)-[:{pref_type}]->(e)"
        )
        logger.info("semantic_memory.update_preference", user=user_name, entity=entity)
        try:
            async with self.driver.session() as session:
                await session.run(query, user_name=user_name, entity_name=entity)
        except Exception as e:
            logger.error("semantic_memory.update_preference_failed", error=str(e), user=user_name)
            raise

    async def extract_entities_from_text(self, text: str) -> Dict[str, Any]:
        """
        Usa LLM para extrair entidades e relações do texto e as persiste no Neo4j.
        """
        logger.info("semantic_memory.extracting_entities", text_len=len(text))
        
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                system=EXTRACTION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": text}]
            )
            
            # Extrair JSON da resposta
            content = response.content[0].text
            extracted_data = json.loads(content)
            
            user_name = extracted_data.get("user_name") or self.settings.AEGIS_USER_NAME
            
            # Persistir preferências
            for pref in extracted_data.get("preferences", []):
                await self.update_preference(user_name, pref["entity"], pref["relation"])
                
            # Persistir fatos
            for fact in extracted_data.get("facts", []):
                await self.save_fact(fact["subject"], fact["relation"], fact["object"], fact.get("metadata"))
                
            return extracted_data
            
        except Exception as e:
            logger.error("semantic_memory.extraction_failed", error=str(e))
            return {"error": str(e)}

    async def get_user_profile(self, user_name: str) -> List[Dict[str, Any]]:
        """
        Retorna o perfil do usuário (preferências e fatos relacionados).
        """
        query = (
            "MATCH (u:User {name: $user_name})-[r]->(e) "
            "RETURN type(r) as relation, e.name as entity"
        )
        try:
            async with self.driver.session() as session:
                result = await session.run(query, user_name=user_name)
                profile = [
                    {"relation": record["relation"], "entity": record["entity"]} 
                    async for record in result
                ]
                return profile
        except Exception as e:
            logger.error("semantic_memory.get_profile_failed", error=str(e), user=user_name)
            return []

    async def query_graph(self, cypher: str, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Executa uma query Cypher arbitrária.
        """
        try:
            async with self.driver.session() as session:
                result = await session.run(cypher, parameters or {})
                return [dict(record) async for record in result]
        except Exception as e:
            logger.error("semantic_memory.query_failed", error=str(e), query=cypher)
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do grafo de conhecimento."""
        node_query = "MATCH (n) RETURN count(n) as count"
        rel_query = "MATCH ()-[r]->() RETURN count(r) as count"
        try:
            async with self.driver.session() as session:
                node_res = await session.run(node_query)
                rel_res = await session.run(rel_query)
                
                nodes = await node_res.single()
                rels = await rel_res.single()
                
                return {
                    "nodes": nodes["count"] if nodes else 0,
                    "relationships": rels["count"] if rels else 0
                }
        except Exception as e:
            logger.error("semantic_memory.get_stats_failed", error=str(e))
            return {"nodes": 0, "relationships": 0, "error": str(e)}
