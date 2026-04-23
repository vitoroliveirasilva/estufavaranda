from __future__ import annotations

import re

from app.core.exceptions import ValidationError

PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_password_strength(password: str) -> None:
    if not PASSWORD_PATTERN.match(password):
        raise ValidationError(
            "A senha não atende aos requisitos mínimos.",
            details={
                "new_password": "Use ao menos 8 caracteres, com pelo menos 1 letra e 1 número."
            },
        )


def validate_choice(value: str, allowed: set[str], field_name: str) -> None:
    if value not in allowed:
        raise ValidationError(
            "Valor inválido informado.",
            details={
                field_name: f"Use um dos valores permitidos: {', '.join(sorted(allowed))}"
            },
        )
