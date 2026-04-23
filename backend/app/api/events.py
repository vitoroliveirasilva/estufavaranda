from __future__ import annotations

from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.exceptions import ValidationError
from app.core.request import parse_json
from app.core.response import ok
from app.models import PlantEventType
from app.schemas import EventCreateInput
from app.services import EventService, PlantService
from app.utils import validate_choice
from app.utils.pagination import build_pagination_meta

events_bp = Blueprint("events", __name__)
plants = PlantService()
service = EventService()

_ALLOWED_EVENT_TYPES = {item.value for item in PlantEventType}


def _parse_positive_int_arg(
    name: str,
    default: int,
    *,
    minimum: int = 1,
    maximum: int | None = None,
) -> int:
    raw_value = request.args.get(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "Parâmetro de consulta inválido.",
            details={name: "Informe um número inteiro válido."},
        ) from exc

    if value < minimum or (maximum is not None and value > maximum):
        limit_text = (
            f"entre {minimum} e {maximum}" if maximum is not None else f">= {minimum}"
        )
        raise ValidationError(
            "Parâmetro de consulta inválido.",
            details={name: f"Informe um valor {limit_text}."},
        )

    return value


def _optional_event_type_arg() -> str | None:
    raw_value = request.args.get("event_type")
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None
    validate_choice(value, _ALLOWED_EVENT_TYPES, "event_type")
    return value


@events_bp.get("/<int:plant_id>/events")
@auth_required
def list_events(plant_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    page = _parse_positive_int_arg("page", 1, minimum=1)
    page_size = _parse_positive_int_arg("page_size", 20, minimum=1, maximum=100)
    event_type = _optional_event_type_arg()
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
