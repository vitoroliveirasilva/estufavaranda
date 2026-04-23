from __future__ import annotations

import os

from app import create_app


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


app = create_app()
application = app


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=_env_int("FLASK_PORT", 5000),
        debug=_env_bool("FLASK_DEBUG", False),
    )
