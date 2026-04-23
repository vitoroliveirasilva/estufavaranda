from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.utils.datetime import parse_datetime


def blank_str_to_none(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def normalize_email_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    return value


def normalize_datetime_value(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (str, datetime)):
        try:
            return parse_datetime(value)
        except Exception as exc:
            raise ValueError(
                "Informe uma data/hora válida em formato ISO 8601."
            ) from exc
    return value


class InputModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
    )


class ORMModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
    )


class PaginationQuery(InputModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
