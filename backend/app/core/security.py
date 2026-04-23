from __future__ import annotations

import hmac
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError

password_hasher = PasswordHasher()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("password deve ser uma string não vazia.")
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if not isinstance(password, str) or not password:
        return False
    if not isinstance(password_hash, str) or not password_hash:
        return False
    try:
        password_hasher.verify(password_hash, password)
        return True
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        return False


def _hmac_hash(secret_key: str, value: str) -> str:
    return hmac.new(
        secret_key.encode("utf-8"), value.encode("utf-8"), sha256
    ).hexdigest()


def hash_refresh_token(token: str) -> str:
    settings = get_settings()
    return _hmac_hash(settings.refresh_token_secret, token)


def hash_reset_token(token: str) -> str:
    settings = get_settings()
    return _hmac_hash(settings.app_secret_key, token)


def generate_opaque_token(length: int = 48) -> str:
    if length <= 0:
        raise ValueError("length deve ser maior que zero.")
    return secrets.token_urlsafe(length)


def create_access_token(user_id: int, *, is_admin: bool) -> tuple[str, datetime]:
    if int(user_id) <= 0:
        raise ValueError("user_id deve ser um inteiro positivo.")

    settings = get_settings()
    issued_at = utcnow()
    expires_at = issued_at + timedelta(minutes=settings.access_token_expires_minutes)
    payload: dict[str, Any] = {
        "sub": str(int(user_id)),
        "typ": "access",
        "is_admin": bool(is_admin),
        "jti": secrets.token_hex(16),
        "iat": issued_at,
        "nbf": issued_at,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.access_token_secret, algorithm="HS256")
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    if not isinstance(token, str) or not token.strip():
        raise AuthenticationError("Credenciais inválidas.")

    settings = get_settings()
    try:
        payload = jwt.decode(
            token.strip(),
            settings.access_token_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "nbf", "sub", "typ"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Credenciais inválidas.") from exc

    if payload.get("typ") != "access":
        raise AuthenticationError("Credenciais inválidas.")

    try:
        user_id = int(str(payload["sub"]).strip())
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError("Credenciais inválidas.") from exc

    if user_id <= 0:
        raise AuthenticationError("Credenciais inválidas.")

    payload["sub"] = str(user_id)
    payload["is_admin"] = bool(payload.get("is_admin", False))
    return payload
