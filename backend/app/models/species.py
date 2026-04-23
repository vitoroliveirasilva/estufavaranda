from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Numeric, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BIGINT_SQL, Base, TimestampMixin


class SpeciesProfile(Base, TimestampMixin):
    __tablename__ = "species_profiles"
    __table_args__ = (
        CheckConstraint(
            "watering_frequency_days IS NULL OR watering_frequency_days > 0",
            name="ck_species_profiles_watering_frequency_days_positive",
        ),
        CheckConstraint(
            "ideal_humidity_min IS NULL OR (ideal_humidity_min >= 0 AND ideal_humidity_min <= 100)",
            name="ck_species_profiles_ideal_humidity_min_range",
        ),
        CheckConstraint(
            "ideal_humidity_max IS NULL OR (ideal_humidity_max >= 0 AND ideal_humidity_max <= 100)",
            name="ck_species_profiles_ideal_humidity_max_range",
        ),
        CheckConstraint(
            "ideal_humidity_min IS NULL OR ideal_humidity_max IS NULL OR ideal_humidity_min <= ideal_humidity_max",
            name="ck_species_profiles_ideal_humidity_bounds",
        ),
        CheckConstraint(
            "ideal_temp_min IS NULL OR ideal_temp_max IS NULL OR ideal_temp_min <= ideal_temp_max",
            name="ck_species_profiles_ideal_temp_bounds",
        ),
    )

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
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    plants = relationship(
        "Plant",
        back_populates="species_profile",
        passive_deletes=True,
    )
