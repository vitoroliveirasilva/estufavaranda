from __future__ import annotations

from flask import Blueprint

from app.core.response import ok

health_bp = Blueprint("health", __name__)


@health_bp.get("/api/v1/health")
def healthcheck():
    return ok({"status": "ok"})
