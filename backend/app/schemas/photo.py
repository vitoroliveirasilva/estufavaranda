from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PhotoCreateInput(BaseModel):
    photo_type: str = Field(default="routine", max_length=30)
    caption: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    taken_at: datetime | None = None


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
