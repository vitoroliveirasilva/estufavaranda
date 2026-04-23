from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from flask import g, request

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository

ViewFunc = TypeVar("ViewFunc", bound=Callable[..., Any])


def _extract_bearer_token() -> str:
    header = (request.headers.get("Authorization") or "").strip()
    if not header:
        raise AuthenticationError("Credenciais inválidas.")

    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthenticationError("Credenciais inválidas.")

    return token.strip()


def auth_required(view: ViewFunc) -> ViewFunc:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        token = _extract_bearer_token()
        payload = decode_access_token(token)

        try:
            user_id = int(payload["sub"])
        except (KeyError, TypeError, ValueError) as exc:
            raise AuthenticationError("Credenciais inválidas.") from exc

        user = UserRepository().get_by_id(user_id)
        if not user or not getattr(user, "is_active", False):
            raise AuthenticationError("Credenciais inválidas.")

        g.current_user = user
        g.current_user_id = user_id
        g.access_token_payload = payload
        return view(*args, **kwargs)

    return wrapped


def admin_required(view: ViewFunc) -> ViewFunc:
    @auth_required
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if not getattr(g.current_user, "is_admin", False):
            raise AuthorizationError("Acesso negado.")
        return view(*args, **kwargs)

    return wrapped
