from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.security import utcnow
from app.models import HealthStatus, Plant
from app.repositories import PlantRepository
from app.services.watering_service import WateringService
from app.utils import validate_choice


class PlantService:
    def __init__(self):
        self.repo = PlantRepository()
        self.watering = WateringService()

    def list_plants(
        self,
        *,
        current_user,
        include_archived: bool,
        health_status: str | None,
        species_profile_id: int | None,
        search: str | None,
        page: int,
        page_size: int,
    ):
        user_id = (
            None
            if (current_user.is_admin and get_settings().enable_admin_read_all_plants)
            else current_user.id
        )
        return self.repo.list_plants(
            user_id=user_id,
            include_archived=include_archived,
            health_status=health_status,
            species_profile_id=species_profile_id,
            search=search,
            page=page,
            page_size=page_size,
        )

    def get_plant(self, plant_id: int, *, current_user) -> Plant:
        plant = self.repo.get_by_id(plant_id)
        if not plant:
            raise NotFoundError("Planta não encontrada.")
        if not current_user.is_admin or not get_settings().enable_admin_read_all_plants:
            if plant.user_id != current_user.id:
                raise NotFoundError("Planta não encontrada.")
        return plant

    def create_plant(self, *, current_user, **payload) -> Plant:
        validate_choice(
            payload.get("health_status", HealthStatus.ATTENTION.value),
            {item.value for item in HealthStatus},
            "health_status",
        )
        plant = Plant(user_id=current_user.id, **payload)
        self.repo.add(plant)
        self.repo.commit()
        return plant

    def update_plant(self, *, plant: Plant, **payload) -> Plant:
        if "health_status" in payload and payload["health_status"] is not None:
            validate_choice(
                payload["health_status"],
                {item.value for item in HealthStatus},
                "health_status",
            )
        for field, value in payload.items():
            setattr(plant, field, value)
        self.repo.commit()
        return plant

    def archive_plant(self, *, plant: Plant) -> None:
        plant.archived_at = utcnow()
        self.repo.commit()

    def build_detail(self, plant: Plant) -> dict:
        summary = self.watering.get_summary(plant)
        photos = sorted(
            [photo for photo in plant.photos if photo.removed_at is None],
            key=lambda item: item.taken_at or item.uploaded_at,
            reverse=True,
        )[:5]
        events = sorted(plant.events, key=lambda item: item.occurred_at, reverse=True)[
            :10
        ]
        return {
            "id": plant.id,
            "user_id": plant.user_id,
            "name": plant.name,
            "nickname": plant.nickname,
            "species_profile_id": plant.species_profile_id,
            "species_profile": (
                {
                    "id": plant.species_profile.id,
                    "common_name": plant.species_profile.common_name,
                    "scientific_name": plant.species_profile.scientific_name,
                }
                if plant.species_profile
                else None
            ),
            "acquisition_date": (
                plant.acquisition_date.isoformat() if plant.acquisition_date else None
            ),
            "environment": plant.environment,
            "light_exposure": plant.light_exposure,
            "ventilation": plant.ventilation,
            "vase_description": plant.vase_description,
            "substrate_description": plant.substrate_description,
            "location_label": plant.location_label,
            "city_name": plant.city_name,
            "notes": plant.notes,
            "health_status": plant.health_status,
            "archived_at": plant.archived_at.isoformat() if plant.archived_at else None,
            "watering_summary": summary,
            "recent_photos": [
                {
                    "id": photo.id,
                    "photo_type": photo.photo_type,
                    "caption": photo.caption,
                    "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
                    "uploaded_at": photo.uploaded_at.isoformat(),
                }
                for photo in photos
            ],
            "recent_events": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "occurred_at": event.occurred_at.isoformat(),
                    "title": event.title,
                    "description": event.description,
                }
                for event in events
            ],
        }
