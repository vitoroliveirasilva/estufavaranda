from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class WateringCreateInput(BaseModel):
    watered_at: datetime
    quantity_ml: int | None = Field(default=None, ge=0, le=10000)
    notes: str | None = None


class WateringOutput(ORMModel):
    id: int
    plant_id: int
    watered_at: datetime
    quantity_ml: int | None
    notes: str | None
