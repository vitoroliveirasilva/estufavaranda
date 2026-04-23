from __future__ import annotations

import re
from collections.abc import Collection

from app.core.exceptions import ValidationError

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 256
_PASSWORD_HAS_LETTER_RE = re.compile(r"[A-Za-z]")
_PASSWORD_HAS_DIGIT_RE = re.compile(r"\d")


def normalize_email(email: str) -> str:
    if not isinstance(email, str):
        raise ValidationError(
            "E-mail inválido informado.",
            details={"email": "Informe um e-mail válido."},
        )

    normalized = re.sub(r"\s+", "", email).lower()
    return normalized.strip()


def validate_password_strength(password: str) -> None:
    if not isinstance(password, str):
        raise ValidationError(
            "A senha não atende aos requisitos mínimos.",
            details={
                "new_password": "Use ao menos 8 caracteres, com pelo menos 1 letra e 1 número."
            },
        )

    if len(password) < PASSWORD_MIN_LENGTH or len(password) > PASSWORD_MAX_LENGTH:
        raise ValidationError(
            "A senha não atende aos requisitos mínimos.",
            details={
                "new_password": f"Use entre {PASSWORD_MIN_LENGTH} e {PASSWORD_MAX_LENGTH} caracteres."
            },
        )

    if not _PASSWORD_HAS_LETTER_RE.search(
        password
    ) or not _PASSWORD_HAS_DIGIT_RE.search(password):
        raise ValidationError(
            "A senha não atende aos requisitos mínimos.",
            details={
                "new_password": "Use ao menos 8 caracteres, com pelo menos 1 letra e 1 número."
            },
        )


def validate_choice(value: str, allowed: Collection[str], field_name: str) -> None:
    if not isinstance(field_name, str) or not field_name.strip():
        raise ValueError("field_name deve ser uma string não vazia.")
    if not isinstance(allowed, Collection) or not allowed:
        raise ValueError("allowed deve conter ao menos um valor permitido.")

    normalized_value = value.strip() if isinstance(value, str) else value
    if normalized_value not in allowed:
        allowed_values = ", ".join(sorted(str(item) for item in allowed))
        raise ValidationError(
            "Valor inválido informado.",
            details={field_name: f"Use um dos valores permitidos: {allowed_values}"},
        )
