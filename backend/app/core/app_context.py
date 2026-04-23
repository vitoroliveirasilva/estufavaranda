from __future__ import annotations

import logging
import time
import uuid

from flask import Flask, g, request

logger = logging.getLogger(__name__)
_MAX_REQUEST_ID_LENGTH = 128


def _build_request_id() -> str:
    header_value = (request.headers.get("X-Request-Id") or "").strip()
    if header_value:
        sanitized = "".join(ch for ch in header_value if ch.isprintable()).strip()
        if sanitized:
            return sanitized[:_MAX_REQUEST_ID_LENGTH]
    return str(uuid.uuid4())


def register_request_hooks(app: Flask) -> None:
    @app.before_request
    def start_request() -> None:
        g.request_id = _build_request_id()
        g.request_started_at = time.perf_counter()

    @app.after_request
    def finish_request(response):
        started_at = getattr(g, "request_started_at", None)
        duration_ms = 0
        if isinstance(started_at, (int, float)):
            duration_ms = max(0, int((time.perf_counter() - started_at) * 1000))

        request_id = getattr(g, "request_id", "")
        response.headers.setdefault("X-Request-Id", request_id)
        logger.info(
            "request.finished",
            extra={
                "request_id": request_id,
                "path": request.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
