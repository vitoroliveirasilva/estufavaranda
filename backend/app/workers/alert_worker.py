from __future__ import annotations

import logging

from app.services import NotificationService

logger = logging.getLogger(__name__)


def run() -> dict:
    logger.info("worker.alert.start")
    result = NotificationService().generate_alerts()
    logger.info("worker.alert.finish", extra=result)
    return result
