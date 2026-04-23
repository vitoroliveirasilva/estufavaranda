from flask import Blueprint, request

from app.core.auth import admin_required, auth_required
from app.core.request import parse_json
from app.core.response import ok
from app.schemas import SpeciesCreateInput, SpeciesUpdateInput
from app.services import SpeciesService
from app.utils.pagination import build_pagination_meta

species_bp = Blueprint("species", __name__)
service = SpeciesService()


@species_bp.get("")
@auth_required
def list_species():
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(100, max(1, int(request.args.get("page_size", 20))))
    search = request.args.get("search")
    active_only = request.args.get("active_only", "true").lower() != "false"
    items, total = service.list_species(
        page=page, page_size=page_size, search=search, active_only=active_only
    )
    return ok(
        [
            {
                "id": item.id,
                "common_name": item.common_name,
                "scientific_name": item.scientific_name,
                "light_preference": item.light_preference,
                "watering_frequency_days": item.watering_frequency_days,
                "ideal_humidity_min": item.ideal_humidity_min,
                "ideal_humidity_max": item.ideal_humidity_max,
                "ideal_temp_min": (
                    float(item.ideal_temp_min)
                    if item.ideal_temp_min is not None
                    else None
                ),
                "ideal_temp_max": (
                    float(item.ideal_temp_max)
                    if item.ideal_temp_max is not None
                    else None
                ),
                "substrate_notes": item.substrate_notes,
                "general_notes": item.general_notes,
                "common_symptoms": item.common_symptoms,
                "is_active": item.is_active,
            }
            for item in items
        ],
        meta=build_pagination_meta(page=page, page_size=page_size, total=total),
    )


@species_bp.get("/<int:species_id>")
@auth_required
def get_species(species_id: int):
    species = service.get_species(species_id)
    return ok(
        {
            "id": species.id,
            "common_name": species.common_name,
            "scientific_name": species.scientific_name,
            "light_preference": species.light_preference,
            "watering_frequency_days": species.watering_frequency_days,
            "ideal_humidity_min": species.ideal_humidity_min,
            "ideal_humidity_max": species.ideal_humidity_max,
            "ideal_temp_min": (
                float(species.ideal_temp_min)
                if species.ideal_temp_min is not None
                else None
            ),
            "ideal_temp_max": (
                float(species.ideal_temp_max)
                if species.ideal_temp_max is not None
                else None
            ),
            "substrate_notes": species.substrate_notes,
            "general_notes": species.general_notes,
            "common_symptoms": species.common_symptoms,
            "is_active": species.is_active,
        }
    )


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
