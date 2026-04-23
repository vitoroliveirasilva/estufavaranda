from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.models.base import PlantEventType
from app.schemas.common import (
    InputModel,
    ORMModel,
    blank_str_to_none,
    normalize_datetime_value,
)

_ALLOWED_EVENT_TYPES = {item.value for item in PlantEventType}


class EventCreateInput(InputModel):
    event_type: str = Field(min_length=3, max_length=50)
    occurred_at: datetime
    title: str | None = Field(default=None, max_length=150)
    description: str | None = None
    metadata_json: dict[str, Any] | None = None

    @field_validator("event_type")
    @classmethod
    def _validate_event_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in _ALLOWED_EVENT_TYPES:
            allowed = ", ".join(sorted(_ALLOWED_EVENT_TYPES))
            raise ValueError(
                f"event_type inválido. Use um dos valores permitidos: {allowed}"
            )
        return normalized

    @field_validator("occurred_at", mode="before")
    @classmethod
    def _normalize_occurred_at(cls, value):
        return normalize_datetime_value(value)

    @field_validator("title", "description", mode="before")
    @classmethod
    def _blank_strings_to_none(cls, value):
        return blank_str_to_none(value)


class EventOutput(ORMModel):
    id: int
    plant_id: int
    event_type: str
    occurred_at: datetime
    title: str | None
    description: str | None
    metadata_json: dict[str, Any] | None
