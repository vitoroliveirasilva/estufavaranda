from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.models import SpeciesProfile
from app.repositories import SpeciesRepository


class SpeciesService:
    def __init__(self):
        self.repo = SpeciesRepository()

    def list_species(
        self, *, page: int, page_size: int, search: str | None, active_only: bool = True
    ):
        return self.repo.list_species(
            page=page, page_size=page_size, search=search, active_only=active_only
        )

    def get_species(self, species_id: int) -> SpeciesProfile:
        species = self.repo.get_by_id(species_id)
        if not species:
            raise NotFoundError("Perfil de espécie não encontrado.")
        return species

    def create_species(self, **payload) -> SpeciesProfile:
        species = SpeciesProfile(**payload)
        self.repo.add(species)
        self.repo.commit()
        return species

    def update_species(self, species_id: int, **payload) -> SpeciesProfile:
        species = self.get_species(species_id)
        for field, value in payload.items():
            setattr(species, field, value)
        self.repo.commit()
        return species
