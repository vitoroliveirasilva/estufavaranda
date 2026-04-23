from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import (
    InputModel,
    ORMModel,
    blank_str_to_none,
    normalize_datetime_value,
)


class WateringCreateInput(InputModel):
    watered_at: datetime
    quantity_ml: int | None = Field(default=None, ge=0, le=10000)
    notes: str | None = None

    @field_validator("watered_at", mode="before")
    @classmethod
    def _normalize_watered_at(cls, value):
        return normalize_datetime_value(value)

    @field_validator("notes", mode="before")
    @classmethod
    def _blank_notes_to_none(cls, value):
        return blank_str_to_none(value)


class WateringOutput(ORMModel):
    id: int
    plant_id: int
    watered_at: datetime
    quantity_ml: int | None
    notes: str | None
