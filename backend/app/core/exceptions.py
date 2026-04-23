from http import HTTPStatus


class AppError(Exception):
    status_code = HTTPStatus.BAD_REQUEST
    code = "app_error"
    message = "Não foi possível concluir a operação."

    def __init__(self, message: str | None = None, *, details: dict | None = None):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details or {}


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
