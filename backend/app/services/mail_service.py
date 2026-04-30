from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from html import escape

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_APP_NAME = "Estufa da Varanda"
_RESET_PASSWORD_SUBJECT = "Redefinição de senha | Estufa da Varanda"


class MailService:
    def send_password_reset(self, *, to_email: str, reset_url: str) -> None:
        settings = get_settings()

        destination = (to_email or "").strip()
        cleaned_reset_url = (reset_url or "").strip()

        if not destination:
            raise ValueError(
                "to_email é obrigatório para envio de redefinição de senha."
            )

        if not cleaned_reset_url:
            raise ValueError(
                "reset_url é obrigatório para envio de redefinição de senha."
            )

        if not settings.smtp_host or not settings.smtp_from_email:
            logger.info(
                "mail.reset_password.skipped",
                extra={"to_email": destination, "reason": "smtp_not_configured"},
            )
            return

        expires_minutes = max(1, int(settings.password_reset_expires_minutes))

        message = EmailMessage()
        message["Subject"] = _RESET_PASSWORD_SUBJECT
        message["From"] = formataddr((_APP_NAME, settings.smtp_from_email))
        message["To"] = destination

        message.set_content(
            _build_password_reset_text(
                reset_url=cleaned_reset_url,
                expires_minutes=expires_minutes,
            )
        )

        message.add_alternative(
            _build_password_reset_html(
                reset_url=cleaned_reset_url,
                expires_minutes=expires_minutes,
            ),
            subtype="html",
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


def _build_password_reset_text(*, reset_url: str, expires_minutes: int) -> str:
    return (
        "Olá!\n\n"
        "Recebemos uma solicitação para redefinir a senha da sua conta "
        "no Estufa da Varanda.\n\n"
        f"Para criar uma nova senha, acesse o link abaixo:\n{reset_url}\n\n"
        f"Este link é válido por {expires_minutes} minutos.\n\n"
        "Se você não solicitou essa alteração, pode ignorar este e-mail com segurança. "
        "Sua senha atual continuará a mesma.\n\n"
        "Por segurança, nunca compartilhe este link com outras pessoas.\n\n"
        "Com carinho,\n"
        "Equipe Estufa da Varanda"
    )


def _build_password_reset_html(*, reset_url: str, expires_minutes: int) -> str:
    safe_reset_url = escape(reset_url, quote=True)
    safe_expires_minutes = escape(str(expires_minutes), quote=True)

    return f"""\
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Redefinição de senha</title>
</head>
<body style="margin:0; padding:0; background:#f3f7f1; font-family:Arial, Helvetica, sans-serif; color:#1f2933;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f7f1; margin:0; padding:32px 16px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px; background:#ffffff; border-radius:24px; overflow:hidden; border:1px solid #dfe8dc; box-shadow:0 18px 48px rgba(31, 41, 51, 0.10);">
                    <tr>
                        <td style="padding:28px 28px 20px; background:#166534;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td>
                                        <div style="font-size:14px; line-height:20px; color:#dcfce7; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;">
                                            Estufa da Varanda
                                        </div>

                                        <h1 style="margin:10px 0 0; font-size:26px; line-height:34px; color:#ffffff; font-weight:800;">
                                            Vamos cuidar da sua senha
                                        </h1>

                                        <p style="margin:10px 0 0; font-size:15px; line-height:24px; color:#e8f7eb;">
                                            Recebemos uma solicitação para redefinir o acesso da sua conta.
                                        </p>
                                    </td>

                                    <td align="right" width="72" style="vertical-align:top;">
                                        <div style="width:56px; height:56px; border-radius:18px; background:#ffffff; color:#166534; text-align:center; line-height:56px; font-size:30px; font-weight:700;">
                                            🌱
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:30px 28px 10px;">
                            <p style="margin:0; font-size:16px; line-height:26px; color:#334155;">
                                Olá! Para criar uma nova senha, clique no botão abaixo.
                                O link é exclusivo para sua conta e expira em
                                <strong style="color:#166534;">{safe_expires_minutes} minutos</strong>.
                            </p>
                        </td>
                    </tr>

                    <tr>
                        <td align="center" style="padding:22px 28px 18px;">
                            <a href="{safe_reset_url}" target="_blank" rel="noopener noreferrer" style="display:inline-block; background:#166534; color:#ffffff; text-decoration:none; font-size:16px; font-weight:700; padding:14px 26px; border-radius:999px; box-shadow:0 10px 24px rgba(22, 101, 52, 0.25);">
                                Redefinir minha senha
                            </a>
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:0 28px 24px;">
                            <div style="background:#f8faf7; border:1px solid #dfe8dc; border-radius:18px; padding:16px 18px;">
                                <p style="margin:0; font-size:14px; line-height:22px; color:#52616b;">
                                    Se o botão não funcionar, copie e cole este link no navegador:
                                </p>

                                <p style="margin:10px 0 0; font-size:13px; line-height:20px; word-break:break-all;">
                                    <a href="{safe_reset_url}" target="_blank" rel="noopener noreferrer" style="color:#166534; text-decoration:underline;">
                                        {safe_reset_url}
                                    </a>
                                </p>
                            </div>
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:0 28px 28px;">
                            <div style="background:#fff7ed; border:1px solid #fed7aa; border-radius:18px; padding:16px 18px;">
                                <p style="margin:0; font-size:14px; line-height:22px; color:#7c2d12;">
                                    <strong>Não foi você?</strong>
                                    Pode ignorar este e-mail com segurança. Sua senha atual continuará a mesma.
                                </p>
                            </div>
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:22px 28px; background:#f8faf7; border-top:1px solid #e5eee2;">
                            <p style="margin:0; font-size:13px; line-height:21px; color:#64748b;">
                                Por segurança, nunca compartilhe este link com outras pessoas.
                            </p>

                            <p style="margin:12px 0 0; font-size:13px; line-height:21px; color:#64748b;">
                                Com carinho,<br>
                                <strong style="color:#166534;">Equipe Estufa da Varanda</strong>
                            </p>
                        </td>
                    </tr>
                </table>

                <p style="max-width:560px; margin:18px auto 0; font-size:12px; line-height:18px; color:#718096; text-align:center;">
                    Este é um e-mail automático. Não é necessário responder.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
"""
