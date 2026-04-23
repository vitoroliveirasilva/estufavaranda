from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.request import parse_json
from app.core.response import ok
from app.schemas import EventCreateInput
from app.services import EventService, PlantService
from app.utils.pagination import build_pagination_meta

events_bp = Blueprint("events", __name__)
plants = PlantService()
service = EventService()


@events_bp.get("/<int:plant_id>/events")
@auth_required
def list_events(plant_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(100, max(1, int(request.args.get("page_size", 20))))
    event_type = request.args.get("event_type")
    items, total = service.list_events(
        plant_id=plant_id, event_type=event_type, page=page, page_size=page_size
    )
    return ok(
        [
            {
                "id": event.id,
                "event_type": event.event_type,
                "occurred_at": event.occurred_at.isoformat(),
                "title": event.title,
                "description": event.description,
                "metadata_json": event.metadata_json,
            }
            for event in items
        ],
        meta=build_pagination_meta(page=page, page_size=page_size, total=total),
    )


@events_bp.post("/<int:plant_id>/events")
@auth_required
def create_event(plant_id: int):
    payload = parse_json(EventCreateInput)
    plant = plants.get_plant(plant_id, current_user=g.current_user)
    event = service.create_event(plant=plant, **payload.model_dump())
    return ok({"id": event.id}, status=201)
