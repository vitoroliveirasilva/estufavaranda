from __future__ import annotations

import logging

from app.services import NotificationService

logger = logging.getLogger(__name__)


def run() -> dict:
    logger.info("worker.notification.start")
    result = NotificationService().dispatch_pending_notifications()
    logger.info("worker.notification.finish", extra=result)
    return result
