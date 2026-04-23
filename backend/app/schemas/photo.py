from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.models.base import PhotoType
from app.schemas.common import (
    InputModel,
    ORMModel,
    blank_str_to_none,
    normalize_datetime_value,
)

_ALLOWED_PHOTO_TYPES = {item.value for item in PhotoType}


class PhotoCreateInput(InputModel):
    photo_type: str = Field(default=PhotoType.ROUTINE.value, max_length=30)
    caption: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    taken_at: datetime | None = None

    @field_validator("photo_type")
    @classmethod
    def _validate_photo_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in _ALLOWED_PHOTO_TYPES:
            allowed = ", ".join(sorted(_ALLOWED_PHOTO_TYPES))
            raise ValueError(
                f"photo_type inválido. Use um dos valores permitidos: {allowed}"
            )
        return normalized

    @field_validator("caption", "notes", mode="before")
    @classmethod
    def _blank_strings_to_none(cls, value):
        return blank_str_to_none(value)

    @field_validator("taken_at", mode="before")
    @classmethod
    def _normalize_taken_at(cls, value):
        return normalize_datetime_value(value)


class PhotoOutput(ORMModel):
    id: int
    plant_id: int
    file_path: str
    original_file_name: str | None
    mime_type: str | None
    photo_type: str
    caption: str | None
    notes: str | None
    taken_at: datetime | None
    uploaded_at: datetime
    ai_summary: str | None
