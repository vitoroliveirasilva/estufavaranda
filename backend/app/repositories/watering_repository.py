from __future__ import annotations

from app.extensions import db
from app.models import WateringLog
from app.repositories.base import BaseRepository


class WateringRepository(BaseRepository):
    def list_for_plant(
        self, *, plant_id: int, page: int, page_size: int
    ) -> tuple[list[WateringLog], int]:
        if plant_id <= 0:
            return [], 0
        stmt = (
            db.select(WateringLog)
            .where(WateringLog.plant_id == plant_id)
            .order_by(WateringLog.watered_at.desc(), WateringLog.id.desc())
        )
        return self.paginate(stmt, page=page, page_size=page_size)

    def get_last_for_plant(self, plant_id: int) -> WateringLog | None:
        if plant_id <= 0:
            return None
        stmt = (
            db.select(WateringLog)
            .where(WateringLog.plant_id == plant_id)
            .order_by(WateringLog.watered_at.desc(), WateringLog.id.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()
