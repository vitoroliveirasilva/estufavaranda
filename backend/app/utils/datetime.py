from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        tz = ZoneInfo(get_settings().default_timezone)
        return dt.replace(tzinfo=tz).astimezone(timezone.utc)
    return dt.astimezone(timezone.utc)


def to_local_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    tz = ZoneInfo(get_settings().default_timezone)
    return value.astimezone(tz).isoformat()
