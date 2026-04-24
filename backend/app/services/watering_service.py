from __future__ import annotations

from datetime import datetime, timezone
from math import floor

from app.core.exceptions import ValidationError
from app.core.security import utcnow
from app.models import Plant, PlantEvent, WateringLog
from app.models.base import PlantEventType
from app.repositories import PlantRepository, WateringRepository
from app.utils import parse_datetime


def _coerce_aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class WateringScoringService:
    DEFAULT_BASE_FREQUENCY_DAYS = 4

    def calculate(
        self,
        *,
        plant: Plant,
        latest_watering: WateringLog | None,
        recent_events: list,
        recent_climate: list,
    ) -> dict:
        now = utcnow()
        latest_watering_at = _coerce_aware_utc(
            latest_watering.watered_at if latest_watering is not None else None
        )

        days_since_watering = None
        if latest_watering_at is not None:
            delta = now - latest_watering_at
            days_since_watering = max(0, delta.days)

        base_frequency = (
            plant.species_profile.watering_frequency_days
            if plant.species_profile is not None
            else self.DEFAULT_BASE_FREQUENCY_DAYS
        )
        base_frequency = max(int(base_frequency or self.DEFAULT_BASE_FREQUENCY_DAYS), 1)

        score = 15
        if days_since_watering is not None:
            ratio = days_since_watering / base_frequency
            score += min(60, floor(ratio * 45))
        else:
            score += 35

        recent_heat = False
        if recent_climate:
            latest_climate = recent_climate[0]
            if (
                latest_climate.temperature_c is not None
                and float(latest_climate.temperature_c) >= 30
            ):
                score += 15
                recent_heat = True
            if (
                latest_climate.humidity_percent is not None
                and latest_climate.humidity_percent <= 40
            ):
                score += 10
            if (
                latest_climate.rain_mm is not None
                and float(latest_climate.rain_mm) >= 10
                and (plant.environment or "").strip().lower() == "outdoor"
            ):
                score -= 10

        if (plant.light_exposure or "").strip().lower() in {
            "afternoon_sun",
            "full_sun",
        }:
            score += 10
        if (plant.environment or "").strip().lower() == "outdoor":
            score += 5

        recent_wilt = any(
            event.event_type == PlantEventType.WILT.value for event in recent_events[:5]
        )
        if recent_wilt:
            score += 12

        score = max(0, min(100, int(score)))
        if score >= 80:
            risk_level = "high"
            suggestion = "revisar hoje"
        elif score >= 60:
            risk_level = "attention"
            suggestion = "revisar nas próximas 24h"
        elif score >= 30:
            risk_level = "moderate"
            suggestion = "acompanhar nos próximos 2 dias"
        else:
            risk_level = "low"
            suggestion = "sem urgência"

        return {
            "score": score,
            "risk_level": risk_level,
            "suggestion_window": suggestion,
            "days_since_last_watering": days_since_watering,
            "recent_heat": recent_heat,
            "recent_wilt": recent_wilt,
            "base_frequency_days": base_frequency,
        }


class WateringService:
    def __init__(self):
        self.repo = WateringRepository()
        self.plants = PlantRepository()
        self.scoring = WateringScoringService()

    def list_logs(self, *, plant_id: int, page: int, page_size: int):
        return self.repo.list_for_plant(
            plant_id=plant_id,
            page=page,
            page_size=page_size,
        )

    def create_log(
        self,
        *,
        plant: Plant,
        watered_at,
        quantity_ml: int | None,
        notes: str | None,
    ) -> WateringLog:
        normalized_watered_at = parse_datetime(watered_at)
        normalized_watered_at = _coerce_aware_utc(normalized_watered_at)
        if normalized_watered_at is None:
            raise ValidationError(
                "Dados inválidos.",
                details={"watered_at": "Informe uma data de rega válida."},
            )

        if normalized_watered_at > utcnow():
            raise ValidationError(
                "Dados inválidos.",
                details={"watered_at": "A data de rega não pode estar no futuro."},
            )

        cleaned_quantity = None if quantity_ml is None else int(quantity_ml)
        if cleaned_quantity is not None and cleaned_quantity < 0:
            raise ValidationError(
                "Dados inválidos.",
                details={"quantity_ml": "A quantidade não pode ser negativa."},
            )

        cleaned_notes = self.repo.clean_text(notes)
        log = WateringLog(
            plant_id=plant.id,
            watered_at=normalized_watered_at,
            quantity_ml=cleaned_quantity,
            notes=cleaned_notes,
        )
        self.repo.add(log)
        self.repo.add(
            PlantEvent(
                plant_id=plant.id,
                event_type=PlantEventType.WATERING.value,
                occurred_at=normalized_watered_at,
                title="Rega registrada",
                description=cleaned_notes,
                metadata_json=(
                    {"quantity_ml": cleaned_quantity}
                    if cleaned_quantity is not None
                    else None
                ),
            )
        )
        self.repo.commit()
        return log

    def get_summary(self, plant: Plant) -> dict:
        latest_watering = self.repo.get_last_for_plant(plant.id)
        recent_events = self.plants.recent_events(plant.id, limit=10)
        recent_climate = self.plants.recent_climate_snapshots(plant.id, limit=5)
        summary = self.scoring.calculate(
            plant=plant,
            latest_watering=latest_watering,
            recent_events=recent_events,
            recent_climate=recent_climate,
        )
        summary["last_watering"] = (
            {
                "id": latest_watering.id,
                "watered_at": _coerce_aware_utc(latest_watering.watered_at).isoformat(),
                "quantity_ml": latest_watering.quantity_ml,
                "notes": latest_watering.notes,
            }
            if latest_watering
            else None
        )
        return summary
