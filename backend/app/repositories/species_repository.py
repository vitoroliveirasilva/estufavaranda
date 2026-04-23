from __future__ import annotations

from app.extensions import db
from app.models import SpeciesProfile
from app.repositories.base import BaseRepository


class SpeciesRepository(BaseRepository):
    def get_by_id(self, species_id: int) -> SpeciesProfile | None:
        return self.session.get(SpeciesProfile, species_id)

    def list_species(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        active_only: bool = True,
    ):
        stmt = db.select(SpeciesProfile).order_by(SpeciesProfile.common_name.asc())
        if active_only:
            stmt = stmt.where(SpeciesProfile.is_active.is_(True))
        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                db.func.lower(SpeciesProfile.common_name).like(pattern)
                | db.func.lower(
                    db.func.coalesce(SpeciesProfile.scientific_name, "")
                ).like(pattern)
            )
        return self.paginate(stmt, page=page, page_size=page_size)
