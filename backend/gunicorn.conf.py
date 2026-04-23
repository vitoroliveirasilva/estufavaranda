from __future__ import annotations

import multiprocessing
import os
from pathlib import Path


_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default

    value = value.strip()
    return value or default


def _env_int(
    name: str,
    default: int,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        value = default
    else:
        try:
            value = int(raw_value)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"Invalid integer for {name}: {raw_value!r}") from exc

    if minimum is not None and value < minimum:
        value = minimum
    if maximum is not None and value > maximum:
        value = maximum

    return value


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    normalized = raw_value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False

    raise RuntimeError(f"Invalid boolean for {name}: {raw_value!r}")


_CPU_COUNT = max(multiprocessing.cpu_count(), 1)
_DEFAULT_WORKERS = max(2, min((_CPU_COUNT * 2) + 1, 8))

bind = _env_str("GUNICORN_BIND", os.getenv("BIND", "0.0.0.0:8000"))
backlog = _env_int("GUNICORN_BACKLOG", 2048, minimum=64)
workers = _env_int(
    "GUNICORN_WORKERS",
    _env_int("WEB_CONCURRENCY", _DEFAULT_WORKERS, minimum=1),
    minimum=1,
)
worker_class = _env_str("GUNICORN_WORKER_CLASS", "gthread")
threads = _env_int("GUNICORN_THREADS", 2, minimum=1)
timeout = _env_int("GUNICORN_TIMEOUT", 60, minimum=1)
graceful_timeout = _env_int("GUNICORN_GRACEFUL_TIMEOUT", 30, minimum=1)
keepalive = _env_int("GUNICORN_KEEPALIVE", 5, minimum=1)
max_requests = _env_int("GUNICORN_MAX_REQUESTS", 1000, minimum=0)
max_requests_jitter = _env_int("GUNICORN_MAX_REQUESTS_JITTER", 100, minimum=0)
preload_app = _env_bool("GUNICORN_PRELOAD", False)
reload = _env_bool("GUNICORN_RELOAD", False)
accesslog = _env_str("GUNICORN_ACCESSLOG", "-")
errorlog = _env_str("GUNICORN_ERRORLOG", "-")
loglevel = _env_str("GUNICORN_LOG_LEVEL", "info").lower()
capture_output = _env_bool("GUNICORN_CAPTURE_OUTPUT", True)
access_log_format = _env_str(
    "GUNICORN_ACCESS_LOG_FORMAT",
    '%(h)s %(l)s %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s',
)

_dev_shm = Path("/dev/shm")
if _dev_shm.is_dir():
    worker_tmp_dir = str(_dev_shm)
