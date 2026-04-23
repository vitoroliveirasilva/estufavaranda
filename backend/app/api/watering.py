from __future__ import annotations

from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.exceptions import ValidationError
from app.core.request import parse_json
from app.core.response import ok
from app.schemas import WateringCreateInput
from app.services import PlantService, WateringService
from app.utils.pagination import build_pagination_meta

watering_bp = Blueprint("watering", __name__)
plants = PlantService()
service = WateringService()


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


@watering_bp.get("/<int:plant_id>/watering-logs")
@auth_required
def list_watering_logs(plant_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    page = _parse_positive_int_arg("page", 1, minimum=1)
    page_size = _parse_positive_int_arg("page_size", 20, minimum=1, maximum=100)
    items, total = service.list_logs(plant_id=plant_id, page=page, page_size=page_size)
    return ok(
        [
            {
                "id": item.id,
                "watered_at": item.watered_at.isoformat(),
                "quantity_ml": item.quantity_ml,
                "notes": item.notes,
            }
            for item in items
        ],
        meta=build_pagination_meta(page=page, page_size=page_size, total=total),
    )


@watering_bp.post("/<int:plant_id>/watering-logs")
@auth_required
def create_watering_log(plant_id: int):
    payload = parse_json(WateringCreateInput)
    plant = plants.get_plant(plant_id, current_user=g.current_user)
    log = service.create_log(plant=plant, **payload.model_dump())
    return ok({"id": log.id}, status=201)


@watering_bp.get("/<int:plant_id>/watering-summary")
@auth_required
def watering_summary(plant_id: int):
    plant = plants.get_plant(plant_id, current_user=g.current_user)
    return ok(service.get_summary(plant))
