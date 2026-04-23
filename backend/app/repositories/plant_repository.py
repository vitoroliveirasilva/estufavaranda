from __future__ import annotations

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import ClimateSnapshot, Plant, PlantEvent, PlantPhoto, WateringLog
from app.repositories.base import BaseRepository


class PlantRepository(BaseRepository):
    def get_by_id(self, plant_id: int) -> Plant | None:
        stmt = (
            db.select(Plant)
            .where(Plant.id == plant_id)
            .options(
                selectinload(Plant.species_profile),
                selectinload(Plant.photos),
                selectinload(Plant.events),
                selectinload(Plant.watering_logs),
            )
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
    ):
        stmt = (
            db.select(Plant)
            .options(selectinload(Plant.species_profile))
            .order_by(Plant.updated_at.desc())
        )
        if user_id is not None:
            stmt = stmt.where(Plant.user_id == user_id)
        if not include_archived:
            stmt = stmt.where(Plant.archived_at.is_(None))
        if health_status:
            stmt = stmt.where(Plant.health_status == health_status)
        if species_profile_id:
            stmt = stmt.where(Plant.species_profile_id == species_profile_id)
        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                db.func.lower(Plant.name).like(pattern)
                | db.func.lower(db.func.coalesce(Plant.nickname, "")).like(pattern)
                | db.func.lower(db.func.coalesce(Plant.location_label, "")).like(
                    pattern
                )
            )
        return self.paginate(stmt, page=page, page_size=page_size)

    def list_active_plants(self) -> list[Plant]:
        stmt = db.select(Plant).where(Plant.archived_at.is_(None))
        return self.session.execute(stmt).scalars().all()

    def list_plants_with_city(self) -> list[Plant]:
        stmt = db.select(Plant).where(
            Plant.archived_at.is_(None), Plant.city_name.is_not(None)
        )
        return self.session.execute(stmt).scalars().all()

    def recent_events(self, plant_id: int, limit: int = 20) -> list[PlantEvent]:
        stmt = (
            db.select(PlantEvent)
            .where(PlantEvent.plant_id == plant_id)
            .order_by(PlantEvent.occurred_at.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def recent_photos(self, plant_id: int, limit: int = 20) -> list[PlantPhoto]:
        stmt = (
            db.select(PlantPhoto)
            .where(PlantPhoto.plant_id == plant_id, PlantPhoto.removed_at.is_(None))
            .order_by(
                db.func.coalesce(PlantPhoto.taken_at, PlantPhoto.uploaded_at).desc()
            )
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def recent_watering_logs(self, plant_id: int, limit: int = 20) -> list[WateringLog]:
        stmt = (
            db.select(WateringLog)
            .where(WateringLog.plant_id == plant_id)
            .order_by(WateringLog.watered_at.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def recent_climate_snapshots(
        self, plant_id: int, limit: int = 20
    ) -> list[ClimateSnapshot]:
        stmt = (
            db.select(ClimateSnapshot)
            .where(ClimateSnapshot.plant_id == plant_id)
            .order_by(ClimateSnapshot.recorded_at.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()
