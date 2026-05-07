"""
aegis/tools/email.py

Ferramenta para envio e leitura de e-mails via SMTP/IMAP.
"""
from __future__ import annotations

import smtplib
import structlog
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Optional

from aegis.core.config import get_settings
from aegis.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)


class EmailTool(BaseTool):
    """Gerencia comunicacoes por e-mail."""

    name: str = "email"
    description: str = (
        "Envia e-mails para contatos ou para o proprio usuario. "
        "Use para notificacoes formais, compartilhamento de relatorios ou comunicacoes externas."
    )
    parameters: dict[str, Any] = {
        "to": "Endereco de e-mail do destinatario.",
        "subject": "Assunto do e-mail.",
        "body": "Conteudo do e-mail (texto ou HTML).",
        "action": "Acao: 'send' (padrao) ou 'read'."
    }

    async def execute(self, to: str = "", subject: str = "", body: str = "", action: str = "send") -> ToolResult:
        """
        Executa uma acao de e-mail.
        """
        settings = get_settings()
        
        if action == "send":
            return await self._send_email(to, subject, body, settings)
        elif action == "read":
            return await self._read_emails(settings)
        else:
            return ToolResult(success=False, error=f"Acao '{action}' ainda nao suportada.", metadata={})

    async def _send_email(self, to: str, subject: str, body: str, settings: Any) -> ToolResult:
        if not to or not subject or not body:
            return ToolResult(success=False, error="Destinatario, assunto e corpo sao obrigatorios para envio.", metadata={})

        if not settings.EMAIL_SENDER or not settings.EMAIL_PASSWORD:
            logger.warning("email.missing_credentials", sender=settings.EMAIL_SENDER)
            # Em modo desenvolvimento sem credenciais, apenas logamos o conteudo
            logger.info("email.simulation", to=to, subject=subject, body=body[:100] + "...")
            return ToolResult(
                success=True, 
                data={"status": "simulated", "to": to}, 
                metadata={"reason": "missing_credentials"}
            )

        logger.info("email.sending", to=to, subject=subject)
        
        try:
            # Implementacao real SMTP
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_SENDER
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_SENDER, settings.EMAIL_PASSWORD.get_secret_value())
                server.send_message(msg)

            logger.info("email.sent_success", to=to)
            return ToolResult(success=True, data={"status": "sent", "to": to}, metadata={})

        except Exception as e:
            logger.error("email.failed", error=str(e))
            return ToolResult(success=False, error=f"Falha ao enviar e-mail: {str(e)}", metadata={})

    async def _read_emails(self, settings: Any) -> ToolResult:
        """Mock de leitura de e-mails."""
        logger.info("email.reading")
        # Simulacao de leitura
        mock_emails = [
            {"id": 1, "from": "boss@example.com", "subject": "Relatorio Trimestral", "date": "2026-05-06 09:00"},
            {"id": 2, "from": "system@aegis.ai", "subject": "Alerta de Seguranca", "date": "2026-05-06 10:15"}
        ]
        return ToolResult(success=True, data=mock_emails, metadata={"count": len(mock_emails)})
