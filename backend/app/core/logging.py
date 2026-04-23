from __future__ import annotations

import logging
import sys
from typing import Any

from flask import has_request_context, request
from pythonjsonlogger.json import JsonFormatter

from app.core.config import Settings

_LOG_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(path)s "
    "%(method)s %(status_code)s %(duration_ms)s %(remote_addr)s %(user_agent)s"
)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        defaults: dict[str, Any] = {
            "request_id": "",
            "path": "",
            "method": "",
            "status_code": "",
            "duration_ms": "",
            "remote_addr": "",
            "user_agent": "",
        }

        for field_name, default_value in defaults.items():
            if not hasattr(record, field_name):
                setattr(record, field_name, default_value)

        if has_request_context():
            record.path = getattr(record, "path", "") or request.path
            record.method = getattr(record, "method", "") or request.method
            record.remote_addr = getattr(record, "remote_addr", "") or (
                request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                or request.remote_addr
                or ""
            )
            record.user_agent = getattr(record, "user_agent", "") or str(
                request.user_agent or ""
            )

        return True


def configure_logging(settings: Settings) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level)
    handler.addFilter(RequestContextFilter())

    if settings.log_json:
        formatter = JsonFormatter(_LOG_FORMAT)
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s %(message)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    logging.captureWarnings(True)
