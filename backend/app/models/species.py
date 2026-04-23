from __future__ import annotations

from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BIGINT_SQL, Base, TimestampMixin


class SpeciesProfile(Base, TimestampMixin):
    __tablename__ = "species_profiles"

    id: Mapped[int] = mapped_column(BIGINT_SQL, primary_key=True, autoincrement=True)
    common_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    scientific_name: Mapped[str | None] = mapped_column(
        String(180), nullable=True, index=True
    )
    light_preference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    watering_frequency_days: Mapped[int | None] = mapped_column(nullable=True)
    ideal_humidity_min: Mapped[int | None] = mapped_column(nullable=True)
    ideal_humidity_max: Mapped[int | None] = mapped_column(nullable=True)
    ideal_temp_min: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    ideal_temp_max: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    substrate_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    general_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    common_symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    plants = relationship("Plant", back_populates="species_profile")
