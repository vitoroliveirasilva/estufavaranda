from __future__ import annotations

import logging
import uuid
from typing import Any

import requests

from app.core.config import get_settings
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

_MAX_TURNSTILE_TOKEN_LENGTH = 2048
_GENERIC_CAPTCHA_MESSAGE = (
    "Não foi possível confirmar a verificação de segurança. Tente novamente."
)


class CaptchaService:
    def verify_forgot_password(
        self,
        *,
        token: str | None,
        remote_ip: str | None,
    ) -> None:
        settings = get_settings()
        if not settings.turnstile_enabled:
            return

        self.verify_turnstile(
            token=token,
            remote_ip=remote_ip,
            expected_action=settings.turnstile_expected_action,
            expected_hostname=settings.turnstile_expected_hostname,
        )

    def verify_turnstile(
        self,
        *,
        token: str | None,
        remote_ip: str | None = None,
        expected_action: str | None = None,
        expected_hostname: str | None = None,
    ) -> None:
        settings = get_settings()
        secret_key = settings.turnstile_secret_key

        if not secret_key:
            logger.error("captcha.turnstile.missing_secret")
            raise ValidationError(
                "Verificação de segurança indisponível no momento.",
                details={"captcha_token": "Configuração de segurança indisponível."},
            )

        cleaned_token = self._clean_token(token)
        payload: dict[str, str] = {
            "secret": secret_key,
            "response": cleaned_token,
            "idempotency_key": str(uuid.uuid4()),
        }

        cleaned_remote_ip = (remote_ip or "").strip()
        if cleaned_remote_ip:
            payload["remoteip"] = cleaned_remote_ip

        try:
            response = requests.post(
                settings.turnstile_verify_url,
                data=payload,
                timeout=settings.turnstile_request_timeout_seconds,
            )
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as exc:
            logger.warning("captcha.turnstile.request_failed", exc_info=exc)
            raise ValidationError(
                _GENERIC_CAPTCHA_MESSAGE,
                details={"captcha_token": "Falha temporária na verificação."},
            ) from exc
        except ValueError as exc:
            logger.warning("captcha.turnstile.invalid_json", exc_info=exc)
            raise ValidationError(
                _GENERIC_CAPTCHA_MESSAGE,
                details={"captcha_token": "Resposta inválida da verificação."},
            ) from exc

        if not isinstance(result, dict):
            logger.warning("captcha.turnstile.invalid_payload_type")
            raise ValidationError(
                _GENERIC_CAPTCHA_MESSAGE,
                details={"captcha_token": "Resposta inválida da verificação."},
            )

        if not result.get("success"):
            logger.info(
                "captcha.turnstile.rejected",
                extra={
                    "error_codes": self._error_codes(result),
                    "hostname": result.get("hostname"),
                    "action": result.get("action"),
                },
            )
            raise ValidationError(
                _GENERIC_CAPTCHA_MESSAGE,
                details={"captcha_token": "Verificação inválida ou expirada."},
            )

        self._validate_expected_action(result, expected_action)
        self._validate_expected_hostname(result, expected_hostname)

        logger.info(
            "captcha.turnstile.accepted",
            extra={
                "hostname": result.get("hostname"),
                "action": result.get("action"),
            },
        )

    @staticmethod
    def _clean_token(token: str | None) -> str:
        cleaned_token = (token or "").strip()

        if not cleaned_token:
            raise ValidationError(
                _GENERIC_CAPTCHA_MESSAGE,
                details={"captcha_token": "Confirme a verificação de segurança."},
            )

        if len(cleaned_token) > _MAX_TURNSTILE_TOKEN_LENGTH:
            raise ValidationError(
                _GENERIC_CAPTCHA_MESSAGE,
                details={"captcha_token": "Token de verificação muito longo."},
            )

        return cleaned_token

    @staticmethod
    def _error_codes(result: dict[str, Any]) -> list[str]:
        raw_error_codes = result.get("error-codes") or []
        if not isinstance(raw_error_codes, list):
            return []
        return [str(item) for item in raw_error_codes if item]

    @staticmethod
    def _validate_expected_action(
        result: dict[str, Any], expected_action: str | None
    ) -> None:
        clean_expected_action = (expected_action or "").strip()
        if not clean_expected_action:
            return

        received_action = (str(result.get("action") or "")).strip()
        if received_action != clean_expected_action:
            logger.info(
                "captcha.turnstile.action_mismatch",
                extra={
                    "expected_action": clean_expected_action,
                    "received_action": received_action,
                },
            )
            raise ValidationError(
                _GENERIC_CAPTCHA_MESSAGE,
                details={"captcha_token": "Ação de verificação inválida."},
            )

    @staticmethod
    def _validate_expected_hostname(
        result: dict[str, Any], expected_hostname: str | None
    ) -> None:
        clean_expected_hostname = (expected_hostname or "").strip().lower()
        if not clean_expected_hostname:
            return

        received_hostname = (str(result.get("hostname") or "")).strip().lower()
        if received_hostname != clean_expected_hostname:
            logger.info(
                "captcha.turnstile.hostname_mismatch",
                extra={
                    "expected_hostname": clean_expected_hostname,
                    "received_hostname": received_hostname,
                },
            )
            raise ValidationError(
                _GENERIC_CAPTCHA_MESSAGE,
                details={"captcha_token": "Origem da verificação inválida."},
            )
