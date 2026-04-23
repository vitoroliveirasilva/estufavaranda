from __future__ import annotations

from sqlalchemy import func, or_

from app.extensions import db
from app.models import SpeciesProfile
from app.repositories.base import BaseRepository


class SpeciesRepository(BaseRepository):
    def get_by_id(self, species_id: int) -> SpeciesProfile | None:
        if species_id <= 0:
            return None
        return self.session.get(SpeciesProfile, species_id)

    def list_species(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        active_only: bool = True,
    ) -> tuple[list[SpeciesProfile], int]:
        stmt = db.select(SpeciesProfile).order_by(
            SpeciesProfile.common_name.asc(), SpeciesProfile.id.asc()
        )
        if active_only:
            stmt = stmt.where(SpeciesProfile.is_active.is_(True))

        pattern = self.build_like_pattern(search)
        if pattern is not None:
            stmt = stmt.where(
                or_(
                    func.lower(SpeciesProfile.common_name).like(pattern, escape="\\"),
                    func.lower(func.coalesce(SpeciesProfile.scientific_name, "")).like(
                        pattern, escape="\\"
                    ),
                )
            )

        return self.paginate(stmt, page=page, page_size=page_size)
