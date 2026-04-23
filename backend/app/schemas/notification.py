from __future__ import annotations

from datetime import datetime

from app.schemas.common import ORMModel


class NotificationOutput(ORMModel):
    id: int
    user_id: int
    plant_id: int | None
    type: str
    title: str
    body: str
    status: str
    dedupe_key: str | None
    created_at: datetime
    read_at: datetime | None
    discarded_at: datetime | None
