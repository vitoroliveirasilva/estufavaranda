from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify
from flask_limiter.errors import RateLimitExceeded

from app.api import register_blueprints
from app.commands import register_commands
from app.core.app_context import register_request_hooks
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.response import error_payload
from app.extensions import cors, db, limiter, migrate


def create_app(settings_override: Settings | None = None) -> Flask:
    settings = settings_override or get_settings()
    configure_logging(settings)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.app_secret_key,
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_pre_ping": True,
            "pool_recycle": 1800,
            "future": True,
        },
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=settings.max_upload_bytes,
        PROPAGATE_EXCEPTIONS=False,
    )
    app.settings = settings

    Path(settings.upload_base_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db, directory="migrations")
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": settings.cors_origins_list or "*"}},
        supports_credentials=False,
    )
    limiter.init_app(app, default_limits=[settings.rate_limit_default])
    register_request_hooks(app)
    register_commands(app)
    register_blueprints(app)
    register_error_handlers(app)

    @app.after_request
    def apply_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    logging.getLogger(__name__).info("app.initialized")
    return app


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        return (
            jsonify(error_payload(exc.code, exc.message, exc.details)),
            exc.status_code,
        )

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(exc: RateLimitExceeded):
        return (
            jsonify(
                error_payload(
                    "too_many_requests",
                    "Muitas tentativas. Tente novamente mais tarde.",
                )
            ),
            429,
        )

    @app.errorhandler(404)
    def handle_not_found(_):
        return jsonify(error_payload("not_found", "Recurso não encontrado.")), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        logging.getLogger(__name__).exception("request.failed", exc_info=exc)
        return (
            jsonify(error_payload("internal_error", "Erro interno do servidor.")),
            500,
        )
