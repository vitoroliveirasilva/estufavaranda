from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class EventCreateInput(BaseModel):
    event_type: str = Field(min_length=3, max_length=50)
    occurred_at: datetime
    title: str | None = Field(default=None, max_length=150)
    description: str | None = None
    metadata_json: dict | None = None


class EventOutput(ORMModel):
    id: int
    plant_id: int
    event_type: str
    occurred_at: datetime
    title: str | None
    description: str | None
    metadata_json: dict | None
