from __future__ import annotations

from app.models import Plant, PlantEvent, PlantEventType
from app.repositories import EventRepository
from app.utils import parse_datetime, validate_choice


class EventService:
    def __init__(self):
        self.repo = EventRepository()

    def list_events(
        self,
        *,
        plant_id: int,
        event_type: str | None,
        page: int,
        page_size: int,
    ):
        if event_type is not None:
            cleaned_event_type = str(event_type).strip().lower()
            validate_choice(
                cleaned_event_type,
                {item.value for item in PlantEventType},
                "event_type",
            )
            event_type = cleaned_event_type
        return self.repo.list_for_plant(
            plant_id=plant_id,
            event_type=event_type,
            page=page,
            page_size=page_size,
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
        cleaned_event_type = str(event_type).strip().lower()
        validate_choice(
            cleaned_event_type,
            {item.value for item in PlantEventType},
            "event_type",
        )
        event = PlantEvent(
            plant_id=plant.id,
            event_type=cleaned_event_type,
            occurred_at=parse_datetime(occurred_at),
            title=self.repo.clean_text(title),
            description=self.repo.clean_text(description),
            metadata_json=metadata_json or None,
        )
        self.repo.add(event)
        self.repo.commit()
        return event
