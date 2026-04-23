from __future__ import annotations

import logging

from app.services import ClimateService

logger = logging.getLogger(__name__)


def run() -> dict:
    logger.info("worker.climate.start")
    result = ClimateService().refresh_relevant_cities()
    logger.info("worker.climate.finish", extra=result)
    return result
