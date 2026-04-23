from flask import Blueprint, g

from app.core.auth import auth_required
from app.core.response import ok
from app.services import ClimateService, PlantService

climate_bp = Blueprint("climate", __name__)
plants = PlantService()
service = ClimateService()


@climate_bp.get("/plants/<int:plant_id>/climate")
@auth_required
def plant_climate(plant_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    snapshots = service.list_plant_climate(plant_id)
    return ok(
        [
            {
                "id": item.id,
                "recorded_at": item.recorded_at.isoformat(),
                "temperature_c": (
                    float(item.temperature_c)
                    if item.temperature_c is not None
                    else None
                ),
                "humidity_percent": item.humidity_percent,
                "rain_mm": float(item.rain_mm) if item.rain_mm is not None else None,
                "feels_like_c": (
                    float(item.feels_like_c) if item.feels_like_c is not None else None
                ),
                "uv_index": float(item.uv_index) if item.uv_index is not None else None,
                "city_name": item.city_name,
            }
            for item in snapshots
        ]
    )


@climate_bp.get("/climate/summary")
@auth_required
def climate_summary():
    plant_service = PlantService()
    items, _ = plant_service.list_plants(
        current_user=g.current_user,
        include_archived=False,
        health_status=None,
        species_profile_id=None,
        search=None,
        page=1,
        page_size=100,
    )
    return ok(service.summary_for_user(items))
