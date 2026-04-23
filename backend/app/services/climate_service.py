from __future__ import annotations

from collections import defaultdict

from app.core.security import utcnow
from app.models import ClimateSnapshot
from app.providers.climate import get_climate_provider
from app.repositories import ClimateRepository, PlantRepository


class ClimateService:
    def __init__(self):
        self.repo = ClimateRepository()
        self.plants = PlantRepository()

    def list_plant_climate(self, plant_id: int, *, limit: int = 10):
        return self.repo.list_for_plant(plant_id=plant_id, limit=limit)

    def summary_for_user(self, plants: list) -> dict:
        grouped: dict[str, list] = defaultdict(list)
        for plant in plants:
            if plant.city_name:
                grouped[plant.city_name].append(plant)

        cities = []
        for city_name, city_plants in grouped.items():
            snapshots = self.repo.list_for_city(city_name=city_name, limit=1)
            latest = snapshots[0] if snapshots else None
            cities.append(
                {
                    "city_name": city_name,
                    "plants_count": len(city_plants),
                    "latest_snapshot": (
                        {
                            "recorded_at": latest.recorded_at.isoformat(),
                            "temperature_c": (
                                float(latest.temperature_c)
                                if latest.temperature_c is not None
                                else None
                            ),
                            "humidity_percent": latest.humidity_percent,
                            "rain_mm": (
                                float(latest.rain_mm)
                                if latest.rain_mm is not None
                                else None
                            ),
                            "feels_like_c": (
                                float(latest.feels_like_c)
                                if latest.feels_like_c is not None
                                else None
                            ),
                            "uv_index": (
                                float(latest.uv_index)
                                if latest.uv_index is not None
                                else None
                            ),
                        }
                        if latest
                        else None
                    ),
                }
            )

        return {"cities": cities}

    def refresh_relevant_cities(self) -> dict:
        provider = get_climate_provider()
        plants = self.plants.list_plants_with_city()
        grouped: dict[str, list] = defaultdict(list)
        for plant in plants:
            grouped[plant.city_name].append(plant)

        processed = 0
        failures = 0
        for city_name, city_plants in grouped.items():
            try:
                weather = provider.fetch_by_city(city_name)
                for plant in city_plants:
                    snapshot = ClimateSnapshot(
                        plant_id=plant.id,
                        city_name=weather.city_name,
                        recorded_at=utcnow(),
                        temperature_c=weather.temperature_c,
                        humidity_percent=weather.humidity_percent,
                        rain_mm=weather.rain_mm,
                        feels_like_c=weather.feels_like_c,
                        uv_index=weather.uv_index,
                        raw_payload=weather.raw_payload,
                        created_at=utcnow(),
                    )
                    self.repo.add(snapshot)
                    processed += 1
            except Exception:
                failures += 1
        self.repo.commit()
        return {"processed": processed, "failures": failures, "cities": len(grouped)}
