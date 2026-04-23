from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PlantCreateInput(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    species_profile_id: int | None = None
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
    health_status: str = Field(default="attention", max_length=50)


class PlantUpdateInput(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    species_profile_id: int | None = None
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
    health_status: str | None = Field(default=None, max_length=50)


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
    archived_at: str | None = None
