from __future__ import annotations

from app.core.exceptions import NotFoundError, ValidationError
from app.models import SpeciesProfile
from app.repositories import SpeciesRepository


class SpeciesService:
    TEXT_FIELDS = {
        "common_name",
        "scientific_name",
        "light_preference",
        "substrate_notes",
        "general_notes",
        "common_symptoms",
    }

    def __init__(self):
        self.repo = SpeciesRepository()

    def list_species(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        active_only: bool = True,
    ):
        return self.repo.list_species(
            page=page,
            page_size=page_size,
            search=search,
            active_only=active_only,
        )

    def get_species(self, species_id: int) -> SpeciesProfile:
        species = self.repo.get_by_id(species_id)
        if not species:
            raise NotFoundError("Perfil de espécie não encontrado.")
        return species

    def _normalize_payload(self, payload: dict) -> dict:
        normalized = dict(payload)
        for field in self.TEXT_FIELDS:
            if field in normalized:
                normalized[field] = self.repo.clean_text(normalized.get(field))

        if "common_name" in normalized and normalized["common_name"] is None:
            raise ValidationError(
                "Dados inválidos.",
                details={"common_name": "Informe um nome comum válido."},
            )

        humidity_min = normalized.get("ideal_humidity_min")
        humidity_max = normalized.get("ideal_humidity_max")
        if (
            humidity_min is not None
            and humidity_max is not None
            and humidity_min > humidity_max
        ):
            raise ValidationError(
                "Dados inválidos.",
                details={
                    "ideal_humidity_min": "Não pode ser maior que a umidade máxima.",
                    "ideal_humidity_max": "Não pode ser menor que a umidade mínima.",
                },
            )

        temp_min = normalized.get("ideal_temp_min")
        temp_max = normalized.get("ideal_temp_max")
        if temp_min is not None and temp_max is not None and temp_min > temp_max:
            raise ValidationError(
                "Dados inválidos.",
                details={
                    "ideal_temp_min": "Não pode ser maior que a temperatura máxima.",
                    "ideal_temp_max": "Não pode ser menor que a temperatura mínima.",
                },
            )

        return normalized

    def create_species(self, **payload) -> SpeciesProfile:
        species = SpeciesProfile(**self._normalize_payload(payload))
        self.repo.add(species)
        self.repo.commit()
        return species

    def update_species(self, species_id: int, **payload) -> SpeciesProfile:
        species = self.get_species(species_id)
        normalized = self._normalize_payload(payload)
        for field, value in normalized.items():
            if value is None and field == "common_name":
                continue
            setattr(species, field, value)
        self.repo.commit()
        return species
