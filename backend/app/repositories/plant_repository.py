from __future__ import annotations

from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import ClimateSnapshot, Plant, PlantEvent, PlantPhoto, WateringLog
from app.repositories.base import BaseRepository


class PlantRepository(BaseRepository):
    def get_by_id(self, plant_id: int) -> Plant | None:
        if plant_id <= 0:
            return None
        stmt = (
            db.select(Plant)
            .where(Plant.id == plant_id)
            .options(selectinload(Plant.species_profile))
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_plants(
        self,
        *,
        user_id: int | None,
        include_archived: bool,
        health_status: str | None,
        species_profile_id: int | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Plant], int]:
        stmt = (
            db.select(Plant)
            .options(selectinload(Plant.species_profile))
            .order_by(Plant.updated_at.desc(), Plant.id.desc())
        )

        if user_id is not None:
            stmt = stmt.where(Plant.user_id == user_id)
        if not include_archived:
            stmt = stmt.where(Plant.archived_at.is_(None))

        cleaned_health_status = self.clean_text(health_status)
        if cleaned_health_status is not None:
            stmt = stmt.where(Plant.health_status == cleaned_health_status)

        if species_profile_id is not None:
            stmt = stmt.where(Plant.species_profile_id == species_profile_id)

        pattern = self.build_like_pattern(search)
        if pattern is not None:
            stmt = stmt.where(
                or_(
                    func.lower(Plant.name).like(pattern, escape="\\"),
                    func.lower(func.coalesce(Plant.nickname, "")).like(
                        pattern, escape="\\"
                    ),
                    func.lower(func.coalesce(Plant.location_label, "")).like(
                        pattern, escape="\\"
                    ),
                    func.lower(func.coalesce(Plant.city_name, "")).like(
                        pattern, escape="\\"
                    ),
                )
            )

        return self.paginate(stmt, page=page, page_size=page_size)

    def list_active_plants(self) -> list[Plant]:
        stmt = (
            db.select(Plant)
            .where(Plant.archived_at.is_(None))
            .order_by(Plant.updated_at.desc(), Plant.id.desc())
        )
        return self.session.execute(stmt).scalars().all()

    def list_plants_with_city(self) -> list[Plant]:
        stmt = (
            db.select(Plant)
            .where(
                Plant.archived_at.is_(None),
                Plant.city_name.is_not(None),
                func.length(func.trim(Plant.city_name)) > 0,
            )
            .order_by(Plant.city_name.asc(), Plant.id.asc())
        )
        return self.session.execute(stmt).scalars().all()

    def recent_events(self, plant_id: int, limit: int = 20) -> list[PlantEvent]:
        if plant_id <= 0:
            return []
        stmt = (
            db.select(PlantEvent)
            .where(PlantEvent.plant_id == plant_id)
            .order_by(PlantEvent.occurred_at.desc(), PlantEvent.id.desc())
            .limit(self.normalize_limit(limit, default=20, max_value=200))
        )
        return self.session.execute(stmt).scalars().all()

    def recent_photos(self, plant_id: int, limit: int = 20) -> list[PlantPhoto]:
        if plant_id <= 0:
            return []
        stmt = (
            db.select(PlantPhoto)
            .where(PlantPhoto.plant_id == plant_id, PlantPhoto.removed_at.is_(None))
            .order_by(
                db.func.coalesce(PlantPhoto.taken_at, PlantPhoto.uploaded_at).desc(),
                PlantPhoto.id.desc(),
            )
            .limit(self.normalize_limit(limit, default=20, max_value=200))
        )
        return self.session.execute(stmt).scalars().all()

    def recent_watering_logs(self, plant_id: int, limit: int = 20) -> list[WateringLog]:
        if plant_id <= 0:
            return []
        stmt = (
            db.select(WateringLog)
            .where(WateringLog.plant_id == plant_id)
            .order_by(WateringLog.watered_at.desc(), WateringLog.id.desc())
            .limit(self.normalize_limit(limit, default=20, max_value=200))
        )
        return self.session.execute(stmt).scalars().all()

    def recent_climate_snapshots(
        self, plant_id: int, limit: int = 20
    ) -> list[ClimateSnapshot]:
        if plant_id <= 0:
            return []
        stmt = (
            db.select(ClimateSnapshot)
            .where(ClimateSnapshot.plant_id == plant_id)
            .order_by(ClimateSnapshot.recorded_at.desc(), ClimateSnapshot.id.desc())
            .limit(self.normalize_limit(limit, default=20, max_value=200))
        )
        return self.session.execute(stmt).scalars().all()
