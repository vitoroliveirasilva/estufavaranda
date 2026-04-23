from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from app import create_app
from app.workers.alert_worker import run as run_alert_worker
from app.workers.cleanup_worker import run as run_cleanup_worker
from app.workers.climate_worker import run as run_climate_worker
from app.workers.notification_worker import run as run_notification_worker


def main():
    app = create_app()
    scheduler = BlockingScheduler(timezone=app.settings.default_timezone)

    def _run_with_context(fn):
        def wrapper():
            with app.app_context():
                fn()

        return wrapper

    scheduler.add_job(
        _run_with_context(run_climate_worker),
        "interval",
        hours=3,
        id="climate_worker",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_with_context(run_alert_worker),
        "interval",
        hours=2,
        id="alert_worker",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_with_context(run_notification_worker),
        "interval",
        minutes=5,
        id="notification_worker",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_with_context(run_cleanup_worker),
        "interval",
        days=1,
        id="cleanup_worker",
        replace_existing=True,
    )

    scheduler.start()


if __name__ == "__main__":
    main()
