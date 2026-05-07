"""
tests/smoke/test_fase5.py

Smoke Test para a Fase 5 do AEGIS.
Valida Cache Semântico, Sistema de Plugins, Segurança e Observabilidade.
"""
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Configurações de ambiente para testes
os.environ["ANTHROPIC_API_KEY"] = "fake-key"
os.environ["ENVIRONMENT"] = "test"

from aegis.core.security import SecurityManager, AuditLogger
from aegis.core.cache import SemanticCache
from aegis.plugins.manager import PluginManager
from aegis.core.models import UserInput, OperatingMode

class TestFase5Smoke:
    
    @pytest.mark.asyncio
    async def test_security_manager_blocking(self):
        """Valida que o SecurityManager bloqueia ações irreversíveis sem aprovação."""
        audit_logger = MagicMock(spec=AuditLogger)
        security = SecurityManager(audit_logger=audit_logger)
        
        async def mock_action(**kwargs):
            return "executed"
            
        # Tenta executar uma ação irreversível sem 'approved=True'
        with pytest.raises(PermissionError) as excinfo:
            await security.verify_and_execute(
                user_id="test_user",
                action_name="delete_file",
                params={"path": "important.txt"},
                func=mock_action
            )
        
        assert "bloqueada" in str(excinfo.value)
        audit_logger.log_action.assert_any_call("test_user", "blocked:delete_file", {"reason": "missing_user_approval"})

    @pytest.mark.asyncio
    async def test_semantic_cache_hit(self):
        """Valida o funcionamento básico do Cache Semântico."""
        with patch("aegis.core.cache.chromadb.PersistentClient") as mock_chroma:
            # Mock do client e collection
            mock_collection = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = mock_collection
            
            cache = SemanticCache()
            
            # Simula um cache hit
            mock_collection.query.return_value = {
                "ids": [["id1"]],
                "documents": [["Resposta cacheada"]],
                "distances": [[0.05]], # Similaridade = 0.95 >= 0.92
                "metadatas": [[{"original_query": "oi", "response": "Resposta cacheada"}]]
            }
            
            result = await cache.get("olá")
            assert result == "Resposta cacheada"

    @pytest.mark.asyncio
    async def test_plugin_manager_loading(self):
        """Valida que o PluginManager consegue listar plugins (mesmo que vazio)."""
        with patch("aegis.plugins.manager.Path.iterdir") as mock_iter:
            mock_iter.return_value = [] # Nenhum plugin no diretório de teste
            
            manager = PluginManager()
            await manager.load_all()
            assert len(manager.loaded_plugins) == 0
            
    @pytest.mark.asyncio
    async def test_audit_log_creation(self):
        """Valida que o AuditLogger cria o arquivo de log."""
        log_file = "./.tmp/test_audit.log"
        if os.path.exists(log_file):
            os.remove(log_file)
            
        logger = AuditLogger(log_path=log_file)
        logger.log_action("system", "smoke_test", {"status": "ok"})
        
        assert os.path.exists(log_file)
        with open(log_file, "r") as f:
            content = f.read()
            assert "smoke_test" in content
            assert "system" in content

    @pytest.mark.asyncio
    async def test_load_test_mock(self):
        """Simula um teste de carga leve (10 requisições simultâneas)."""
        security = SecurityManager()
        
        async def dummy_task(**kwargs):
            await asyncio.sleep(0.01)
            return "done"
            
        tasks = [
            security.verify_and_execute("user", "read_file", {"approved": True, "id": i}, dummy_task)
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 10
        assert all(r == "done" for r in results)
