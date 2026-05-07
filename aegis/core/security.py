"""
aegis/core/security.py

Módulo de segurança para o sistema AEGIS.
Implementa logs de auditoria imutáveis e gerenciamento de ações irreversíveis.
"""
from __future__ import annotations

import os
import json
import datetime
import structlog
from pathlib import Path
from typing import Any, Callable, Coroutine
from aegis.core.config import get_settings

logger = structlog.get_logger(__name__)

class AuditLogger:
    """Log imutável (append-only) para auditoria de segurança."""
    
    def __init__(self, log_path: str | None = None):
        self.settings = get_settings()
        if log_path is None:
            # Tenta usar o diretório de dados definido na config
            data_dir = getattr(self.settings, "DATA_DIR", "data")
            log_path = os.path.join(data_dir, "audit.log")
            
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
    def log_action(self, user_id: str, action: str, details: dict[str, Any]):
        """Registra uma ação no log de auditoria."""
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "user_id": user_id,
            "action": action,
            "details": self._sanitize_details(details)
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            logger.info("audit.action_logged", action=action, user_id=user_id)
        except Exception as e:
            logger.error("audit.log_failed", error=str(e), action=action)

    def _sanitize_details(self, details: dict[str, Any]) -> dict[str, Any]:
        """Remove dados sensíveis antes de logar."""
        sensitive_keys = {"api_key", "password", "token", "secret"}
        sanitized = {}
        for k, v in details.items():
            if any(sk in k.lower() for sk in sensitive_keys):
                sanitized[k] = "********"
            else:
                sanitized[k] = v
        return sanitized

class SecurityManager:
    """Gerencia aprovações e verificações de segurança para o AEGIS."""
    
    # Ações que exigem aprovação explícita do usuário
    IRREVERSIBLE_ACTIONS = {
        "delete_file",
        "overwrite_file",
        "git_push",
        "send_email",
        "expensive_llm_call",
        "execute_system_command"
    }
    
    def __init__(self, audit_logger: AuditLogger | None = None):
        self.audit_logger = audit_logger or AuditLogger()
        self.settings = get_settings()
        
    async def verify_and_execute(
        self, 
        user_id: str, 
        action_name: str, 
        params: dict[str, Any], 
        func: Callable[..., Coroutine[Any, Any, Any]]
    ) -> Any:
        """
        Verifica se a ação é permitida e a executa, registrando tudo no log de auditoria.
        """
        is_irreversible = action_name in self.IRREVERSIBLE_ACTIONS
        
        # 1. Log de tentativa
        self.audit_logger.log_action(user_id, f"attempt:{action_name}", params)
        
        # 2. Verificação de aprovação para ações irreversíveis
        if is_irreversible:
            # Se não houver aprovação explícita nos parâmetros, bloqueia.
            # A flag 'approved' deve ser passada pela interface após confirmação do usuário.
            if not params.get("approved", False):
                self.audit_logger.log_action(user_id, f"blocked:{action_name}", {"reason": "missing_user_approval"})
                logger.warning("security.action_blocked", action=action_name, user_id=user_id)
                raise PermissionError(
                    f"Ação irreversível '{action_name}' bloqueada. Requer aprovação explícita do usuário."
                )
            
            logger.info("security.action_approved", action=action_name, user_id=user_id)
            self.audit_logger.log_action(user_id, f"authorized:{action_name}", {"status": "user_approved"})

        # 3. Execução
        try:
            result = await func(**params)
            
            # 4. Log de resultado
            # Tenta extrair 'success' do resultado se for um objeto tipo ToolResult
            success = getattr(result, "success", True)
            self.audit_logger.log_action(user_id, f"success:{action_name}", {"success": success})
            
            return result
        except Exception as e:
            self.audit_logger.log_action(user_id, f"failure:{action_name}", {"error": str(e)})
            logger.error("security.execution_failed", action=action_name, error=str(e))
            raise

# Instância global para facilidade de uso
audit_logger = AuditLogger()
security_manager = SecurityManager(audit_logger)
