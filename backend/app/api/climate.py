from __future__ import annotations

from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.exceptions import ValidationError
from app.core.response import ok
from app.services import ClimateService, PlantService

climate_bp = Blueprint("climate", __name__)
plants = PlantService()
service = ClimateService()


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


def _serialize_snapshot(item) -> dict:
    return {
        "id": item.id,
        "recorded_at": item.recorded_at.isoformat(),
        "temperature_c": (
            float(item.temperature_c) if item.temperature_c is not None else None
        ),
        "humidity_percent": item.humidity_percent,
        "rain_mm": float(item.rain_mm) if item.rain_mm is not None else None,
        "feels_like_c": (
            float(item.feels_like_c) if item.feels_like_c is not None else None
        ),
        "uv_index": float(item.uv_index) if item.uv_index is not None else None,
        "city_name": item.city_name,
    }


def _collect_user_plants(*, current_user) -> list:
    page_size = 100
    page = 1
    items: list = []

    while True:
        current_items, total = plants.list_plants(
            current_user=current_user,
            include_archived=False,
            health_status=None,
            species_profile_id=None,
            search=None,
            page=page,
            page_size=page_size,
        )
        items.extend(current_items)
        if len(items) >= total or not current_items:
            break
        page += 1

    return items


@climate_bp.get("/plants/<int:plant_id>/climate")
@auth_required
def plant_climate(plant_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    limit = _parse_positive_int_arg("limit", 10, minimum=1, maximum=100)
    snapshots = service.list_plant_climate(plant_id, limit=limit)
    return ok([_serialize_snapshot(item) for item in snapshots])


@climate_bp.get("/climate/summary")
@auth_required
def climate_summary():
    items = _collect_user_plants(current_user=g.current_user)
    return ok(service.summary_for_user(items))
