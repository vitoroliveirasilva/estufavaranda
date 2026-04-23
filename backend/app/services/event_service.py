from __future__ import annotations

from app.models import Plant, PlantEvent, PlantEventType
from app.utils import parse_datetime, validate_choice
from app.repositories import EventRepository


class EventService:
    def __init__(self):
        self.repo = EventRepository()

    def list_events(
        self, *, plant_id: int, event_type: str | None, page: int, page_size: int
    ):
        return self.repo.list_for_plant(
            plant_id=plant_id, event_type=event_type, page=page, page_size=page_size
        )

    def create_event(
        self,
        *,
        plant: Plant,
        event_type: str,
        occurred_at,
        title: str | None,
        description: str | None,
        metadata_json: dict | None,
    ) -> PlantEvent:
        validate_choice(
            event_type, {item.value for item in PlantEventType}, "event_type"
        )
        event = PlantEvent(
            plant_id=plant.id,
            event_type=event_type,
            occurred_at=parse_datetime(occurred_at),
            title=title,
            description=description,
            metadata_json=metadata_json,
        )
        self.repo.add(event)
        self.repo.commit()
        return event
