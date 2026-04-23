from __future__ import annotations

import os

from app import create_app
from app.core.config import get_settings


_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}


def _env_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    normalized = raw_value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False

    raise RuntimeError(f"Invalid boolean for {name}: {raw_value!r}")


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        return int(raw_value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Invalid integer for {name}: {raw_value!r}") from exc


def build_app():
    return create_app()


app = build_app()
application = app


def main() -> None:
    settings = get_settings()
    app.run(
        host=os.getenv("FLASK_HOST", settings.app_host),
        port=_env_int("FLASK_PORT", settings.app_port),
        debug=_env_bool("FLASK_DEBUG", settings.app_debug),
    )


if __name__ == "__main__":
    main()
