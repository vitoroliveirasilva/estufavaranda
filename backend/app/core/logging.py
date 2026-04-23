import logging
import sys
from pythonjsonlogger.json import JsonFormatter

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler(sys.stdout)

    if settings.log_json:
        formatter = JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(path)s %(method)s %(status_code)s %(duration_ms)s"
        )
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s %(message)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
