from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import get_settings
from app.core.exceptions import ValidationError


@lru_cache(maxsize=1)
def _get_default_timezone() -> ZoneInfo:
    timezone_name = (getattr(get_settings(), "default_timezone", None) or "UTC").strip()
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        raw_value = value.strip()
        if not raw_value:
            raise ValidationError(
                "Data/hora inválida.",
                details={
                    "datetime": "Informe uma data/hora válida em formato ISO 8601."
                },
            )
        if raw_value.endswith("Z"):
            raw_value = f"{raw_value[:-1]}+00:00"
        try:
            dt = datetime.fromisoformat(raw_value)
        except ValueError as exc:
            raise ValidationError(
                "Data/hora inválida.",
                details={
                    "datetime": "Informe uma data/hora válida em formato ISO 8601."
                },
            ) from exc
    else:
        raise ValidationError(
            "Data/hora inválida.",
            details={"datetime": "Informe uma data/hora válida em formato ISO 8601."},
        )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_get_default_timezone())

    return dt.astimezone(timezone.utc)


def to_local_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError("value deve ser datetime ou None.")

    dt = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return dt.astimezone(_get_default_timezone()).isoformat()
