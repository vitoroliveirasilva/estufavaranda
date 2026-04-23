from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from app.extensions import db
from app.services import NotificationService

logger = logging.getLogger(__name__)


def _log_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, Mapping):
        return {"worker_result": dict(result)}
    return {"worker_result": result}


def run() -> dict[str, Any]:
    logger.info("worker.notification.start")
    try:
        result = NotificationService().dispatch_pending_notifications()
        logger.info("worker.notification.finish", extra=_log_payload(result))
        return dict(result) if isinstance(result, Mapping) else {"result": result}
    except Exception:
        db.session.rollback()
        logger.exception("worker.notification.failed")
        raise
    finally:
        db.session.remove()
