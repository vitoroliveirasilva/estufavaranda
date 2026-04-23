from __future__ import annotations

from sqlalchemy import func

from app.extensions import db
from app.models import ClimateSnapshot
from app.repositories.base import BaseRepository


class ClimateRepository(BaseRepository):
    def list_for_plant(
        self, *, plant_id: int, limit: int = 10
    ) -> list[ClimateSnapshot]:
        if plant_id <= 0:
            return []
        stmt = (
            db.select(ClimateSnapshot)
            .where(ClimateSnapshot.plant_id == plant_id)
            .order_by(ClimateSnapshot.recorded_at.desc(), ClimateSnapshot.id.desc())
            .limit(self.normalize_limit(limit, default=10, max_value=500))
        )
        return self.session.execute(stmt).scalars().all()

    def list_for_city(
        self, *, city_name: str, limit: int = 10
    ) -> list[ClimateSnapshot]:
        cleaned_city = self.clean_text(city_name)
        if cleaned_city is None:
            return []
        stmt = (
            db.select(ClimateSnapshot)
            .where(func.lower(ClimateSnapshot.city_name) == cleaned_city.lower())
            .order_by(ClimateSnapshot.recorded_at.desc(), ClimateSnapshot.id.desc())
            .limit(self.normalize_limit(limit, default=10, max_value=500))
        )
        return self.session.execute(stmt).scalars().all()
