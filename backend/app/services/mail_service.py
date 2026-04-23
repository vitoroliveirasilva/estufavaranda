from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MailService:
    def send_password_reset(self, *, to_email: str, reset_url: str) -> None:
        settings = get_settings()
        if not settings.smtp_host or not settings.smtp_from_email:
            logger.info(
                "mail.reset_password.skipped",
                extra={"to_email": to_email, "reset_url": reset_url},
            )
            return

        message = EmailMessage()
        message["Subject"] = "Redefinição de senha - Estufa da varanda"
        message["From"] = settings.smtp_from_email
        message["To"] = to_email
        message.set_content(
            f"Você solicitou a redefinição da sua senha.\n\nUse o link a seguir:\n{reset_url}\n\n"
            "Se você não solicitou esta alteração, ignore esta mensagem."
        )

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as client:
            if settings.smtp_use_tls:
                client.starttls()
            if settings.smtp_user and settings.smtp_password:
                client.login(settings.smtp_user, settings.smtp_password)
            client.send_message(message)
