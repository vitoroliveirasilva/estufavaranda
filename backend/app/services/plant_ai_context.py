from __future__ import annotations

from datetime import datetime
from typing import Any

from app.repositories import PlantRepository
from app.services.watering_service import WateringService


class PlantAiContextBuilder:
    def __init__(
        self,
        *,
        plants: PlantRepository | None = None,
        watering: WateringService | None = None,
    ) -> None:
        self.plants = plants or PlantRepository()
        self.watering = watering or WateringService()

    def build(self, plant) -> dict[str, Any]:
        recent_events = self.plants.recent_events(plant.id, limit=12)
        recent_photos = self.plants.recent_photos(plant.id, limit=6)
        recent_climate = self.plants.recent_climate_snapshots(plant.id, limit=8)
        watering_summary = self.watering.get_summary(plant) or {}

        return {
            "plant": {
                "id": plant.id,
                "name": plant.name,
                "nickname": plant.nickname,
                "environment": plant.environment,
                "light_exposure": plant.light_exposure,
                "ventilation": plant.ventilation,
                "vase_description": plant.vase_description,
                "substrate_description": plant.substrate_description,
                "location_label": plant.location_label,
                "city_name": plant.city_name,
                "notes": plant.notes,
                "health_status": plant.health_status,
            },
            "watering_summary": dict(watering_summary),
            "recent_events": [
                {
                    "event_type": str(event.event_type),
                    "occurred_at": self._iso(event.occurred_at),
                    "title": event.title,
                    "description": event.description,
                    "metadata_json": event.metadata_json,
                }
                for event in recent_events
            ],
            "recent_photos": [
                {
                    "photo_type": str(photo.photo_type),
                    "caption": photo.caption,
                    "notes": photo.notes,
                    "ai_summary": photo.ai_summary,
                    "taken_at": self._iso(photo.taken_at or photo.uploaded_at),
                }
                for photo in recent_photos
                if photo.removed_at is None
            ],
            "recent_climate": [
                {
                    "recorded_at": self._iso(snapshot.recorded_at),
                    "temperature_c": self._float_or_none(snapshot.temperature_c),
                    "feels_like_c": self._float_or_none(snapshot.feels_like_c),
                    "humidity_percent": snapshot.humidity_percent,
                    "rain_mm": self._float_or_none(snapshot.rain_mm),
                    "uv_index": self._float_or_none(snapshot.uv_index),
                }
                for snapshot in recent_climate
            ],
        }

    @staticmethod
    def _iso(value: datetime | None) -> str | None:
        return value.isoformat() if value else None

    @staticmethod
    def _float_or_none(value: Any) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None
