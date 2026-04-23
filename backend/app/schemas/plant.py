from __future__ import annotations

from datetime import date, datetime

from pydantic import Field, field_validator

from app.models.base import HealthStatus
from app.schemas.common import InputModel, ORMModel, blank_str_to_none

_ALLOWED_HEALTH_STATUS = {item.value for item in HealthStatus}


class PlantBaseInput(InputModel):
    species_profile_id: int | None = Field(default=None, ge=1)
    nickname: str | None = Field(default=None, max_length=150)
    acquisition_date: date | None = None
    environment: str | None = Field(default=None, max_length=50)
    light_exposure: str | None = Field(default=None, max_length=50)
    ventilation: str | None = Field(default=None, max_length=50)
    vase_description: str | None = Field(default=None, max_length=150)
    substrate_description: str | None = Field(default=None, max_length=150)
    location_label: str | None = Field(default=None, max_length=150)
    city_name: str | None = Field(default=None, max_length=150)
    notes: str | None = None

    @field_validator(
        "nickname",
        "environment",
        "light_exposure",
        "ventilation",
        "vase_description",
        "substrate_description",
        "location_label",
        "city_name",
        "notes",
        mode="before",
    )
    @classmethod
    def _blank_strings_to_none(cls, value):
        return blank_str_to_none(value)


class PlantCreateInput(PlantBaseInput):
    name: str = Field(min_length=1, max_length=150)
    health_status: str = Field(default=HealthStatus.ATTENTION.value, max_length=50)

    @field_validator("health_status")
    @classmethod
    def _validate_health_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in _ALLOWED_HEALTH_STATUS:
            allowed = ", ".join(sorted(_ALLOWED_HEALTH_STATUS))
            raise ValueError(
                f"health_status inválido. Use um dos valores permitidos: {allowed}"
            )
        return normalized


class PlantUpdateInput(PlantBaseInput):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    health_status: str | None = Field(default=None, max_length=50)

    @field_validator("name", mode="before")
    @classmethod
    def _blank_name_to_none(cls, value):
        return blank_str_to_none(value)

    @field_validator("health_status", mode="before")
    @classmethod
    def _normalize_health_status_blank(cls, value):
        return blank_str_to_none(value)

    @field_validator("health_status")
    @classmethod
    def _validate_optional_health_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in _ALLOWED_HEALTH_STATUS:
            allowed = ", ".join(sorted(_ALLOWED_HEALTH_STATUS))
            raise ValueError(
                f"health_status inválido. Use um dos valores permitidos: {allowed}"
            )
        return normalized


class PlantOutput(ORMModel):
    id: int
    user_id: int
    species_profile_id: int | None
    name: str
    nickname: str | None
    acquisition_date: date | None
    environment: str | None
    light_exposure: str | None
    ventilation: str | None
    vase_description: str | None
    substrate_description: str | None
    location_label: str | None
    city_name: str | None
    notes: str | None
    health_status: str
    archived_at: datetime | None = None
