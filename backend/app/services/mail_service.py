from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MailService:
    def send_password_reset(self, *, to_email: str, reset_url: str) -> None:
        settings = get_settings()
        destination = (to_email or "").strip()
        if not destination:
            raise ValueError(
                "to_email é obrigatório para envio de redefinição de senha."
            )

        if not settings.smtp_host or not settings.smtp_from_email:
            logger.info(
                "mail.reset_password.skipped",
                extra={"to_email": destination, "reason": "smtp_not_configured"},
            )
            return

        message = EmailMessage()
        message["Subject"] = "Redefinição de senha - Estufa da varanda"
        message["From"] = settings.smtp_from_email
        message["To"] = destination
        message.set_content(
            "Você solicitou a redefinição da sua senha.\n\n"
            f"Use o link a seguir:\n{reset_url}\n\n"
            "Se você não solicitou esta alteração, ignore esta mensagem."
        )

        try:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=20,
            ) as client:
                client.ehlo()
                if settings.smtp_use_tls:
                    client.starttls()
                    client.ehlo()
                if settings.smtp_user and settings.smtp_password:
                    client.login(settings.smtp_user, settings.smtp_password)
                client.send_message(message)
        except Exception:
            logger.exception(
                "mail.reset_password.failed",
                extra={"to_email": destination},
            )
            raise

        logger.info("mail.reset_password.sent", extra={"to_email": destination})
