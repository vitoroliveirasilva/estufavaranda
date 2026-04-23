from __future__ import annotations

from flask import Blueprint, request

from app.core.auth import admin_required, auth_required
from app.core.exceptions import ValidationError
from app.core.request import parse_json
from app.core.response import ok
from app.schemas import SpeciesCreateInput, SpeciesUpdateInput
from app.services import SpeciesService
from app.utils.pagination import build_pagination_meta

species_bp = Blueprint("species", __name__)
service = SpeciesService()
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


def _optional_search_arg() -> str | None:
    raw_value = request.args.get("search")
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


def _serialize_species(item) -> dict:
    return {
        "id": item.id,
        "common_name": item.common_name,
        "scientific_name": item.scientific_name,
        "light_preference": item.light_preference,
        "watering_frequency_days": item.watering_frequency_days,
        "ideal_humidity_min": item.ideal_humidity_min,
        "ideal_humidity_max": item.ideal_humidity_max,
        "ideal_temp_min": (
            float(item.ideal_temp_min) if item.ideal_temp_min is not None else None
        ),
        "ideal_temp_max": (
            float(item.ideal_temp_max) if item.ideal_temp_max is not None else None
        ),
        "substrate_notes": item.substrate_notes,
        "general_notes": item.general_notes,
        "common_symptoms": item.common_symptoms,
        "is_active": item.is_active,
    }


@species_bp.get("")
@auth_required
def list_species():
    page = _parse_positive_int_arg("page", 1, minimum=1)
    page_size = _parse_positive_int_arg("page_size", 20, minimum=1, maximum=100)
    items, total = service.list_species(
        page=page,
        page_size=page_size,
        search=_optional_search_arg(),
        active_only=_parse_bool_arg("active_only", True),
    )
    return ok(
        [_serialize_species(item) for item in items],
        meta=build_pagination_meta(page=page, page_size=page_size, total=total),
    )


@species_bp.get("/<int:species_id>")
@auth_required
def get_species(species_id: int):
    species = service.get_species(species_id)
    return ok(_serialize_species(species))


@species_bp.post("")
@admin_required
def create_species():
    payload = parse_json(SpeciesCreateInput)
    species = service.create_species(**payload.model_dump())
    return ok({"id": species.id}, status=201)


@species_bp.patch("/<int:species_id>")
@admin_required
def update_species(species_id: int):
    payload = parse_json(SpeciesUpdateInput)
    species = service.update_species(
        species_id, **payload.model_dump(exclude_unset=True)
    )
    return ok(
        {
            "id": species.id,
            "common_name": species.common_name,
            "is_active": species.is_active,
        }
    )
