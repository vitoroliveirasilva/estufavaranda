from __future__ import annotations

from functools import wraps

from flask import g, request

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository


def _extract_bearer_token() -> str:
    header = request.headers.get("Authorization", "").strip()
    if not header.startswith("Bearer "):
        raise AuthenticationError("Credenciais inválidas.")
    return header.removeprefix("Bearer ").strip()


def auth_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = _extract_bearer_token()
        payload = decode_access_token(token)
        user = UserRepository().get_by_id(int(payload["sub"]))
        if not user or not user.is_active:
            raise AuthenticationError("Credenciais inválidas.")
        g.current_user = user
        g.access_token_payload = payload
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @auth_required
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.current_user.is_admin:
            raise AuthorizationError("Acesso negado.")
        return view(*args, **kwargs)

    return wrapped
