from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from app.extensions import db
from app.services import ClimateService

logger = logging.getLogger(__name__)


def _log_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, Mapping):
        return {"worker_result": dict(result)}
    return {"worker_result": result}


def run() -> dict[str, Any]:
    logger.info("worker.climate.start")
    try:
        result = ClimateService().refresh_relevant_cities()
        logger.info("worker.climate.finish", extra=_log_payload(result))
        return dict(result) if isinstance(result, Mapping) else {"result": result}
    except Exception:
        db.session.rollback()
        logger.exception("worker.climate.failed")
        raise
    finally:
        db.session.remove()
