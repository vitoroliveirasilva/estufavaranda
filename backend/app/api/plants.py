from __future__ import annotations

from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.exceptions import ValidationError
from app.core.request import parse_json
from app.core.response import no_content, ok
from app.models import HealthStatus
from app.schemas import PlantCreateInput, PlantUpdateInput
from app.services import PlantService
from app.utils import validate_choice
from app.utils.pagination import build_pagination_meta

plants_bp = Blueprint("plants", __name__)
service = PlantService()

_ALLOWED_HEALTH_STATUS = {item.value for item in HealthStatus}
_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}


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


def _parse_bool_arg(name: str, default: bool) -> bool:
    raw_value = request.args.get(name)
    if raw_value is None or not raw_value.strip():
        return default

    normalized = raw_value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False

    raise ValidationError(
        "Parâmetro de consulta inválido.",
        details={name: "Use true ou false."},
    )


def _optional_str_arg(name: str) -> str | None:
    raw_value = request.args.get(name)
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


def _optional_health_status_arg() -> str | None:
    value = _optional_str_arg("health_status")
    if value is None:
        return None

    normalized = value.lower()
    validate_choice(normalized, _ALLOWED_HEALTH_STATUS, "health_status")
    return normalized


@plants_bp.get("")
@auth_required
def list_plants():
    page = _parse_positive_int_arg("page", 1, minimum=1)
    page_size = _parse_positive_int_arg("page_size", 20, minimum=1, maximum=100)
    include_archived = _parse_bool_arg(
        "include_archived",
        _parse_bool_arg("archived", False),
    )

    items, total = service.list_plants(
        current_user=g.current_user,
        include_archived=include_archived,
        health_status=_optional_health_status_arg(),
        search=_optional_str_arg("search"),
        page=page,
        page_size=page_size,
    )
    return ok(
        [
            {
                "id": plant.id,
                "name": plant.name,
                "nickname": plant.nickname,
                "health_status": plant.health_status,
                "location_label": plant.location_label,
                "city_name": plant.city_name,
                "archived_at": (
                    plant.archived_at.isoformat() if plant.archived_at else None
                ),
            }
            for plant in items
        ],
        meta=build_pagination_meta(page=page, page_size=page_size, total=total),
    )


@plants_bp.post("")
@auth_required
def create_plant():
    payload = parse_json(PlantCreateInput)
    plant = service.create_plant(current_user=g.current_user, **payload.model_dump())
    return ok({"id": plant.id, "name": plant.name}, status=201)


@plants_bp.get("/<int:plant_id>")
@auth_required
def get_plant(plant_id: int):
    plant = service.get_plant(plant_id, current_user=g.current_user)
    return ok(service.build_detail(plant))


@plants_bp.patch("/<int:plant_id>")
@auth_required
def update_plant(plant_id: int):
    payload = parse_json(PlantUpdateInput)
    plant = service.get_plant(plant_id, current_user=g.current_user)
    updated = service.update_plant(
        plant=plant, **payload.model_dump(exclude_unset=True)
    )
    return ok(
        {
            "id": updated.id,
            "name": updated.name,
            "health_status": updated.health_status,
            "archived_at": (
                updated.archived_at.isoformat() if updated.archived_at else None
            ),
        }
    )


@plants_bp.delete("/<int:plant_id>")
@auth_required
def archive_plant(plant_id: int):
    plant = service.get_plant(plant_id, current_user=g.current_user)
    service.archive_plant(plant=plant)
    return no_content()
