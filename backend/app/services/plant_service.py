from __future__ import annotations

import re

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import utcnow
from app.models import HealthStatus, Plant
from app.repositories import PlantRepository
from app.services.watering_service import WateringService
from app.utils import validate_choice


class PlantService:
    TEXT_FIELDS = {
        "name",
        "nickname",
        "environment",
        "light_exposure",
        "ventilation",
        "vase_description",
        "substrate_description",
        "location_label",
        "city_name",
        "notes",
    }
    IGNORED_FIELDS = {
        "species_profile_id",
        "species_profile",
    }

    def __init__(self):
        self.repo = PlantRepository()
        self.watering = WateringService()

    @staticmethod
    def _normalize_city_name(value: str | None) -> str | None:
        if value is None:
            return None
        collapsed = re.sub(r"\s+", " ", value.strip())
        if not collapsed:
            return None
        return collapsed.title()

    def _normalize_payload(self, payload: dict, *, partial: bool) -> dict:
        normalized = dict(payload)

        for field in self.IGNORED_FIELDS:
            normalized.pop(field, None)

        for field in self.TEXT_FIELDS:
            if field in normalized:
                value = self.repo.clean_text(normalized.get(field))
                normalized[field] = value

        if "city_name" in normalized:
            normalized["city_name"] = self._normalize_city_name(
                normalized.get("city_name")
            )

        if not partial and normalized.get("name") is None:
            raise ValidationError(
                "Dados inválidos.",
                details={"name": "Informe um nome válido para a planta."},
            )

        if normalized.get("health_status") is not None:
            normalized["health_status"] = (
                str(normalized["health_status"]).strip().lower()
            )
            validate_choice(
                normalized["health_status"],
                {item.value for item in HealthStatus},
                "health_status",
            )

        return normalized

    def list_plants(
        self,
        *,
        current_user,
        include_archived: bool,
        health_status: str | None,
        search: str | None,
        page: int,
        page_size: int,
    ):
        if health_status is not None:
            cleaned_health_status = str(health_status).strip().lower()
            validate_choice(
                cleaned_health_status,
                {item.value for item in HealthStatus},
                "health_status",
            )
            health_status = cleaned_health_status

        user_id = (
            None
            if (current_user.is_admin and get_settings().enable_admin_read_all_plants)
            else current_user.id
        )
        return self.repo.list_plants(
            user_id=user_id,
            include_archived=include_archived,
            health_status=health_status,
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
        normalized = self._normalize_payload(payload, partial=False)
        normalized.setdefault("health_status", HealthStatus.ATTENTION.value)
        plant = Plant(user_id=current_user.id, **normalized)
        self.repo.add(plant)
        self.repo.commit()
        return plant

    def update_plant(self, *, plant: Plant, **payload) -> Plant:
        normalized = self._normalize_payload(payload, partial=True)
        for field, value in normalized.items():
            setattr(plant, field, value)
        self.repo.commit()
        return plant

    def archive_plant(self, *, plant: Plant) -> None:
        if plant.archived_at is None:
            plant.archived_at = utcnow()
            self.repo.commit()

    def build_detail(self, plant: Plant) -> dict:
        summary = self.watering.get_summary(plant)
        photos = sorted(
            [photo for photo in plant.photos if photo.removed_at is None],
            key=lambda item: ((item.taken_at or item.uploaded_at), item.id),
            reverse=True,
        )[:5]
        events = sorted(
            plant.events,
            key=lambda item: (item.occurred_at, item.id),
            reverse=True,
        )[:10]
        return {
            "id": plant.id,
            "user_id": plant.user_id,
            "name": plant.name,
            "nickname": plant.nickname,
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
