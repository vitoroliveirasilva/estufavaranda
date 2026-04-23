from __future__ import annotations

from app.extensions import db
from app.models import PlantPhoto
from app.repositories.base import BaseRepository


class PhotoRepository(BaseRepository):
    def get_by_id(self, photo_id: int) -> PlantPhoto | None:
        return self.session.get(PlantPhoto, photo_id)

    def list_for_plant(self, *, plant_id: int, page: int, page_size: int):
        stmt = (
            db.select(PlantPhoto)
            .where(PlantPhoto.plant_id == plant_id, PlantPhoto.removed_at.is_(None))
            .order_by(
                db.func.coalesce(PlantPhoto.taken_at, PlantPhoto.uploaded_at).desc()
            )
        )
        return self.paginate(stmt, page=page, page_size=page_size)
