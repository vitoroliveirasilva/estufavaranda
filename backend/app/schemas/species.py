from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.schemas.common import InputModel, ORMModel, blank_str_to_none


class SpeciesBaseInput(InputModel):
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

    @field_validator(
        "scientific_name",
        "light_preference",
        "substrate_notes",
        "general_notes",
        "common_symptoms",
        mode="before",
    )
    @classmethod
    def _blank_strings_to_none(cls, value):
        return blank_str_to_none(value)

    @model_validator(mode="after")
    def _validate_ranges(self):
        humidity_min = self.ideal_humidity_min
        humidity_max = self.ideal_humidity_max
        if (
            humidity_min is not None
            and humidity_max is not None
            and humidity_min > humidity_max
        ):
            raise ValueError(
                "ideal_humidity_min não pode ser maior que ideal_humidity_max."
            )

        temp_min = self.ideal_temp_min
        temp_max = self.ideal_temp_max
        if temp_min is not None and temp_max is not None and temp_min > temp_max:
            raise ValueError("ideal_temp_min não pode ser maior que ideal_temp_max.")
        return self


class SpeciesCreateInput(SpeciesBaseInput):
    common_name: str = Field(min_length=2, max_length=150)
    is_active: bool = True


class SpeciesUpdateInput(SpeciesBaseInput):
    common_name: str | None = Field(default=None, min_length=2, max_length=150)

    @field_validator("common_name", mode="before")
    @classmethod
    def _blank_common_name_to_none(cls, value):
        return blank_str_to_none(value)


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
