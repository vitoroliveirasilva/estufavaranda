from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SpeciesCreateInput(BaseModel):
    common_name: str = Field(min_length=2, max_length=150)
    scientific_name: str | None = Field(default=None, max_length=180)
    light_preference: str | None = Field(default=None, max_length=50)
    watering_frequency_days: int | None = Field(default=None, ge=1, le=90)
    ideal_humidity_min: int | None = Field(default=None, ge=0, le=100)
    ideal_humidity_max: int | None = Field(default=None, ge=0, le=100)
    ideal_temp_min: float | None = None
    ideal_temp_max: float | None = None
    substrate_notes: str | None = None
    general_notes: str | None = None
    common_symptoms: str | None = None
    is_active: bool = True


class SpeciesUpdateInput(BaseModel):
    common_name: str | None = Field(default=None, min_length=2, max_length=150)
    scientific_name: str | None = Field(default=None, max_length=180)
    light_preference: str | None = Field(default=None, max_length=50)
    watering_frequency_days: int | None = Field(default=None, ge=1, le=90)
    ideal_humidity_min: int | None = Field(default=None, ge=0, le=100)
    ideal_humidity_max: int | None = Field(default=None, ge=0, le=100)
    ideal_temp_min: float | None = None
    ideal_temp_max: float | None = None
    substrate_notes: str | None = None
    general_notes: str | None = None
    common_symptoms: str | None = None
    is_active: bool | None = None


class SpeciesOutput(ORMModel):
    id: int
    common_name: str
    scientific_name: str | None
    light_preference: str | None
    watering_frequency_days: int | None
    ideal_humidity_min: int | None
    ideal_humidity_max: int | None
    ideal_temp_min: float | None
    ideal_temp_max: float | None
    substrate_notes: str | None
    general_notes: str | None
    common_symptoms: str | None
    is_active: bool
