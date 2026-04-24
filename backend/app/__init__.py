from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Mapping

from flask import Flask, jsonify, request
from flask_limiter.errors import RateLimitExceeded
from werkzeug.exceptions import HTTPException

from app.api import register_blueprints
from app.commands import register_commands
from app.core.app_context import register_request_hooks
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.response import error_payload
from app.extensions import cors, db, migrate

logger = logging.getLogger(__name__)


def create_app(settings_override: Settings | None = None) -> Flask:
    settings = settings_override or get_settings()
    configure_logging(settings)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.app_secret_key,
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS=_build_engine_options(settings),
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=settings.max_upload_bytes,
        MAX_FORM_MEMORY_SIZE=settings.max_upload_bytes,
        PROPAGATE_EXCEPTIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=settings.secure_cookies,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    app.settings = settings

    _ensure_upload_path(settings.upload_base_path)
    _init_extensions(app, settings)

    register_request_hooks(app)
    register_commands(app)
    register_blueprints(app)
    register_error_handlers(app)
    _register_response_hooks(app)

    logger.info("app.initialized")
    return app


def _build_engine_options(settings: Settings) -> dict[str, Any]:
    default_options: dict[str, Any] = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "future": True,
    }

    custom_options = getattr(settings, "sqlalchemy_engine_options", None)
    if isinstance(custom_options, Mapping):
        default_options.update(custom_options)

    return default_options


def _ensure_upload_path(upload_base_path: str | Path) -> None:
    path = Path(upload_base_path)
    if path.exists() and not path.is_dir():
        raise RuntimeError(
            f"O caminho de upload configurado não é um diretório válido: {path}"
        )
    path.mkdir(parents=True, exist_ok=True)


def _init_extensions(app: Flask, settings: Settings) -> None:
    db.init_app(app)
    migrate.init_app(app, db, directory="migrations")
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": settings.cors_origins_list or "*"}},
        supports_credentials=False,
    )


def _register_response_hooks(app: Flask) -> None:
    @app.after_request
    def apply_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )

        if request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        if request.endpoint != "static":
            response.headers.setdefault("Cache-Control", "no-store")

        return response


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        _rollback_session_safely()
        return (
            jsonify(error_payload(exc.code, exc.message, exc.details)),
            exc.status_code,
        )

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(exc: RateLimitExceeded):
        _rollback_session_safely()
        return (
            jsonify(
                error_payload(
                    "too_many_requests",
                    getattr(
                        exc,
                        "description",
                        "Muitas tentativas. Tente novamente mais tarde.",
                    ),
                )
            ),
            429,
        )

    @app.errorhandler(404)
    def handle_not_found(_exc):
        return jsonify(error_payload("not_found", "Recurso não encontrado.")), 404

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        _rollback_session_safely()
        return (
            jsonify(
                error_payload(
                    getattr(exc, "name", "http_error").lower().replace(" ", "_"),
                    exc.description or "Erro na requisição.",
                )
            ),
            exc.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        _rollback_session_safely()
        logger.exception(
            "request.failed",
            extra={
                "path": request.path,
                "method": request.method,
            },
            exc_info=exc,
        )
        return (
            jsonify(error_payload("internal_error", "Erro interno do servidor.")),
            500,
        )


def _rollback_session_safely() -> None:
    try:
        db.session.rollback()
    except Exception:
        logger.debug("db.session.rollback_failed", exc_info=True)
