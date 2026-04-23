from __future__ import annotations

from app.extensions import db
from app.models import ClimateSnapshot
from app.repositories.base import BaseRepository


class ClimateRepository(BaseRepository):
    def list_for_plant(
        self, *, plant_id: int, limit: int = 10
    ) -> list[ClimateSnapshot]:
        stmt = (
            db.select(ClimateSnapshot)
            .where(ClimateSnapshot.plant_id == plant_id)
            .order_by(ClimateSnapshot.recorded_at.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def list_for_city(
        self, *, city_name: str, limit: int = 10
    ) -> list[ClimateSnapshot]:
        stmt = (
            db.select(ClimateSnapshot)
            .where(ClimateSnapshot.city_name == city_name)
            .order_by(ClimateSnapshot.recorded_at.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()
