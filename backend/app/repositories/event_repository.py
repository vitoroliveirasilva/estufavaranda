from __future__ import annotations

from app.extensions import db
from app.models import PlantEvent
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository):
    def list_for_plant(
        self, *, plant_id: int, event_type: str | None, page: int, page_size: int
    ) -> tuple[list[PlantEvent], int]:
        if plant_id <= 0:
            return [], 0

        stmt = (
            db.select(PlantEvent)
            .where(PlantEvent.plant_id == plant_id)
            .order_by(PlantEvent.occurred_at.desc(), PlantEvent.id.desc())
        )

        cleaned_event_type = self.clean_text(event_type)
        if cleaned_event_type is not None:
            stmt = stmt.where(PlantEvent.event_type == cleaned_event_type)

        return self.paginate(stmt, page=page, page_size=page_size)
