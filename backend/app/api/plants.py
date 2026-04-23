from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.request import parse_json
from app.core.response import no_content, ok
from app.schemas import PlantCreateInput, PlantUpdateInput
from app.services import PlantService
from app.utils.pagination import build_pagination_meta

plants_bp = Blueprint("plants", __name__)
service = PlantService()


@plants_bp.get("")
@auth_required
def list_plants():
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(100, max(1, int(request.args.get("page_size", 20))))
    search = request.args.get("search")
    health_status = request.args.get("health_status")
    species_profile_id = (
        int(request.args["species_profile_id"])
        if request.args.get("species_profile_id")
        else None
    )
    include_archived = request.args.get("archived", "false").lower() == "true"

    items, total = service.list_plants(
        current_user=g.current_user,
        include_archived=include_archived,
        health_status=health_status,
        species_profile_id=species_profile_id,
        search=search,
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
                "species_profile": (
                    {
                        "id": plant.species_profile.id,
                        "common_name": plant.species_profile.common_name,
                    }
                    if plant.species_profile
                    else None
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
        {"id": updated.id, "name": updated.name, "health_status": updated.health_status}
    )


@plants_bp.delete("/<int:plant_id>")
@auth_required
def archive_plant(plant_id: int):
    plant = service.get_plant(plant_id, current_user=g.current_user)
    service.archive_plant(plant=plant)
    return no_content()
