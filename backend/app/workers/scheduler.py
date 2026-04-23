from __future__ import annotations

import logging
import os
import signal
from collections.abc import Callable
from functools import wraps
from typing import Any

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.schedulers.blocking import BlockingScheduler

from app import create_app
from app.extensions import db
from app.workers.alert_worker import run as run_alert_worker
from app.workers.cleanup_worker import run as run_cleanup_worker
from app.workers.climate_worker import run as run_climate_worker
from app.workers.notification_worker import run as run_notification_worker

logger = logging.getLogger(__name__)

JobFn = Callable[[], Any]


def _get_positive_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        logger.warning(
            "scheduler.invalid_env",
            extra={"env_name": name, "env_value": raw_value, "fallback_value": default},
        )
        return default
    if value <= 0:
        logger.warning(
            "scheduler.non_positive_env",
            extra={"env_name": name, "env_value": raw_value, "fallback_value": default},
        )
        return default
    return value


def _job_wrapper(app, job_id: str, fn: JobFn) -> JobFn:
    @wraps(fn)
    def wrapper() -> Any:
        logger.info("scheduler.job.start", extra={"job_id": job_id})
        with app.app_context():
            try:
                result = fn()
                logger.info(
                    "scheduler.job.finish",
                    extra={"job_id": job_id, "worker_result": result},
                )
                return result
            except Exception:
                db.session.rollback()
                logger.exception("scheduler.job.failed", extra={"job_id": job_id})
                raise
            finally:
                db.session.remove()

    return wrapper


def _register_job(
    scheduler: BlockingScheduler,
    *,
    job_id: str,
    fn: JobFn,
    trigger_kwargs: dict[str, int],
) -> None:
    scheduler.add_job(
        fn,
        "interval",
        id=job_id,
        replace_existing=True,
        **trigger_kwargs,
    )


def _log_job_event(event: JobExecutionEvent) -> None:
    if event.exception:
        logger.error(
            "scheduler.job.event_error",
            extra={
                "job_id": event.job_id,
                "scheduled_run_time": str(event.scheduled_run_time),
            },
        )
        return

    logger.info(
        "scheduler.job.event_success",
        extra={
            "job_id": event.job_id,
            "scheduled_run_time": str(event.scheduled_run_time),
        },
    )


def main() -> None:
    app = create_app()
    timezone = getattr(app.settings, "default_timezone", None) or "UTC"
    scheduler = BlockingScheduler(
        timezone=timezone,
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 300,
        },
    )
    scheduler.add_listener(_log_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    jobs = (
        (
            "climate_worker",
            _job_wrapper(app, "climate_worker", run_climate_worker),
            {"hours": _get_positive_int_env("ESTUFA_CLIMATE_WORKER_INTERVAL_HOURS", 3)},
        ),
        (
            "alert_worker",
            _job_wrapper(app, "alert_worker", run_alert_worker),
            {"hours": _get_positive_int_env("ESTUFA_ALERT_WORKER_INTERVAL_HOURS", 2)},
        ),
        (
            "notification_worker",
            _job_wrapper(app, "notification_worker", run_notification_worker),
            {
                "minutes": _get_positive_int_env(
                    "ESTUFA_NOTIFICATION_WORKER_INTERVAL_MINUTES", 5
                )
            },
        ),
        (
            "cleanup_worker",
            _job_wrapper(app, "cleanup_worker", run_cleanup_worker),
            {"days": _get_positive_int_env("ESTUFA_CLEANUP_WORKER_INTERVAL_DAYS", 1)},
        ),
    )

    for job_id, fn, trigger_kwargs in jobs:
        _register_job(
            scheduler,
            job_id=job_id,
            fn=fn,
            trigger_kwargs=trigger_kwargs,
        )

    logger.info(
        "scheduler.initialized",
        extra={
            "timezone": timezone,
            "job_ids": [job_id for job_id, _, _ in jobs],
        },
    )

    def _shutdown(signum: int, _frame: Any) -> None:
        logger.info("scheduler.shutdown_signal", extra={"signal": signum})
        if scheduler.running:
            scheduler.shutdown(wait=False)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _shutdown)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("scheduler.stopped")
        if scheduler.running:
            scheduler.shutdown(wait=False)
        raise


if __name__ == "__main__":
    main()
