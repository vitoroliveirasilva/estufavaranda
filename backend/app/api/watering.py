from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.request import parse_json
from app.core.response import ok
from app.schemas import WateringCreateInput
from app.services import PlantService, WateringService
from app.utils.pagination import build_pagination_meta

watering_bp = Blueprint("watering", __name__)
plants = PlantService()
service = WateringService()


@watering_bp.get("/<int:plant_id>/watering-logs")
@auth_required
def list_watering_logs(plant_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(100, max(1, int(request.args.get("page_size", 20))))
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
