from __future__ import annotations

import logging

from app.repositories import TokenRepository

logger = logging.getLogger(__name__)


def run() -> dict:
    logger.info("worker.cleanup.start")
    result = TokenRepository().cleanup_expired_tokens()
    TokenRepository().commit()
    logger.info("worker.cleanup.finish", extra=result)
    return result
