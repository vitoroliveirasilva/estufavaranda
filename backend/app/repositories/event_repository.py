from __future__ import annotations

from app.extensions import db
from app.models import PlantEvent
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository):
    def list_for_plant(
        self, *, plant_id: int, event_type: str | None, page: int, page_size: int
    ):
        stmt = (
            db.select(PlantEvent)
            .where(PlantEvent.plant_id == plant_id)
            .order_by(PlantEvent.occurred_at.desc())
        )
        if event_type:
            stmt = stmt.where(PlantEvent.event_type == event_type)
        return self.paginate(stmt, page=page, page_size=page_size)
