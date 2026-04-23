from __future__ import annotations

import hmac
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError

password_hasher = PasswordHasher()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
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
    return secrets.token_urlsafe(length)


def create_access_token(user_id: int, *, is_admin: bool) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = utcnow() + timedelta(minutes=settings.access_token_expires_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "typ": "access",
        "is_admin": is_admin,
        "exp": expires_at,
        "iat": utcnow(),
    }
    token = jwt.encode(payload, settings.access_token_secret, algorithm="HS256")
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.access_token_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Credenciais inválidas.") from exc

    if payload.get("typ") != "access":
        raise AuthenticationError("Credenciais inválidas.")

    return payload
