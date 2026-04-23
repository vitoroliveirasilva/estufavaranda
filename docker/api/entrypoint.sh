#!/bin/sh
set -eu

cd /app/backend
umask 027

log() {
    printf '%s\n' "$*" >&2
}

bool_true() {
    value="${1:-}"
    case "$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]')" in
        1|true|t|yes|y|on) return 0 ;;
        *) return 1 ;;
    esac
}

wait_for_database() {
    max_attempts="${DB_WAIT_MAX_ATTEMPTS:-30}"
    delay_seconds="${DB_WAIT_DELAY_SECONDS:-2}"

    python - <<'PY'
import os
import sys
import time

from sqlalchemy import create_engine, text

from app.core.config import get_settings

attempts = int(os.getenv("DB_WAIT_MAX_ATTEMPTS", "30"))
delay = float(os.getenv("DB_WAIT_DELAY_SECONDS", "2"))
settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

for attempt in range(1, attempts + 1):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
        sys.exit(0)
    except Exception as exc:
        if attempt >= attempts:
            engine.dispose()
            print(f"Database unavailable after {attempts} attempts: {exc}", file=sys.stderr)
            sys.exit(1)
        print(
            f"Database unavailable (attempt {attempt}/{attempts}). Retrying in {delay:.1f}s...",
            file=sys.stderr,
        )
        time.sleep(delay)
PY
}

run_migrations() {
    if bool_true "${RUN_DB_MIGRATIONS:-true}"; then
        log "Applying database migrations..."
        python -m flask --app manage.py db upgrade
    fi
}

mkdir -p "${UPLOAD_BASE_PATH:-/data/uploads}"

if bool_true "${WAIT_FOR_DB:-true}"; then
    log "Waiting for database..."
    wait_for_database
fi

run_migrations

if [ "$#" -eq 0 ]; then
    set -- gunicorn --config gunicorn.conf.py wsgi:application
fi

exec "$@"
