from __future__ import annotations

from http import HTTPStatus
from typing import Any

ErrorDetails = dict[str, Any]


class AppError(Exception):
    status_code = HTTPStatus.BAD_REQUEST
    code = "app_error"
    message = "Não foi possível concluir a operação."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: ErrorDetails | None = None,
    ) -> None:
        resolved_message = message or self.message
        super().__init__(resolved_message)
        self.message = resolved_message
        self.details: ErrorDetails = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    code = "validation_error"
    message = "Dados inválidos."


class AuthenticationError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "authentication_error"
    message = "Credenciais inválidas."


class AuthorizationError(AppError):
    status_code = HTTPStatus.FORBIDDEN
    code = "authorization_error"
    message = "Acesso negado."


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "not_found"
    message = "Recurso não encontrado."


class ConflictError(AppError):
    status_code = HTTPStatus.CONFLICT
    code = "conflict"
    message = "Conflito de dados."


class TooManyRequestsError(AppError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    code = "too_many_requests"
    message = "Muitas tentativas. Tente novamente mais tarde."
