from __future__ import annotations

import logging

from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import utcnow
from app.models import PhotoType, Plant, PlantEvent, PlantPhoto
from app.models.base import PlantEventType
from app.repositories import PhotoRepository
from app.services.storage_service import StorageService
from app.utils import parse_datetime, validate_choice
from app.utils.files import validate_image_file

logger = logging.getLogger(__name__)


class PhotoService:
    def __init__(self):
        self.repo = PhotoRepository()
        self.storage = StorageService()

    def list_photos(self, *, plant_id: int, page: int, page_size: int):
        return self.repo.list_for_plant(
            plant_id=plant_id,
            page=page,
            page_size=page_size,
        )

    def create_photo(
        self,
        *,
        plant: Plant,
        file_storage,
        photo_type: str,
        caption: str | None,
        notes: str | None,
        taken_at,
    ) -> PlantPhoto:
        if file_storage is None or not getattr(file_storage, "filename", ""):
            raise ValidationError(
                "Dados inválidos.",
                details={"file": "Envie um arquivo de imagem válido."},
            )

        validate_choice(
            str(photo_type).strip().lower(),
            {item.value for item in PhotoType},
            "photo_type",
        )
        original_filename, mime_type = validate_image_file(file_storage)
        normalized_taken_at = parse_datetime(taken_at) if taken_at else None
        uploaded_at = utcnow()
        relative_path = self.storage.store_plant_photo(
            plant_id=plant.id,
            file_storage=file_storage,
            original_filename=original_filename,
        )

        try:
            photo = PlantPhoto(
                plant_id=plant.id,
                file_path=relative_path,
                original_file_name=original_filename,
                mime_type=mime_type,
                photo_type=str(photo_type).strip().lower(),
                caption=self.repo.clean_text(caption),
                notes=self.repo.clean_text(notes),
                taken_at=normalized_taken_at,
                uploaded_at=uploaded_at,
            )
            self.repo.add(photo)
            self.repo.add(
                PlantEvent(
                    plant_id=plant.id,
                    event_type=PlantEventType.PHOTO_ADDED.value,
                    occurred_at=normalized_taken_at or uploaded_at,
                    title="Foto adicionada",
                    description=self.repo.clean_text(caption)
                    or self.repo.clean_text(notes),
                    metadata_json={"photo_type": photo.photo_type},
                )
            )
            self.repo.commit()
            return photo
        except Exception:
            logger.exception(
                "photo.create.failed",
                extra={"plant_id": plant.id, "file_path": relative_path},
            )
            self.storage.delete_file(relative_path)
            raise

    def remove_photo(self, *, photo: PlantPhoto) -> None:
        if photo.removed_at is None:
            photo.removed_at = utcnow()
            self.repo.commit()

    def get_photo(self, photo_id: int) -> PlantPhoto:
        photo = self.repo.get_by_id(photo_id)
        if not photo or photo.removed_at is not None:
            raise NotFoundError("Foto não encontrada.")
        return photo

    def build_download_url(self, plant_id: int, photo_id: int) -> str:
        if plant_id <= 0 or photo_id <= 0:
            raise ValueError("IDs inválidos para geração da URL de download.")
        return f"/api/v1/plants/{plant_id}/photos/{photo_id}/download"
