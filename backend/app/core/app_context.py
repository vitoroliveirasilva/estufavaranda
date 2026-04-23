from __future__ import annotations

import logging
import time
import uuid

from flask import Flask, g, request

logger = logging.getLogger(__name__)


def register_request_hooks(app: Flask) -> None:
    @app.before_request
    def start_request():
        g.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        g.request_started_at = time.perf_counter()

    @app.after_request
    def finish_request(response):
        duration_ms = int(
            (time.perf_counter() - g.get("request_started_at", time.perf_counter()))
            * 1000
        )
        response.headers["X-Request-Id"] = g.get("request_id", "")
        logger.info(
            "request.finished",
            extra={
                "request_id": g.get("request_id"),
                "path": request.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
