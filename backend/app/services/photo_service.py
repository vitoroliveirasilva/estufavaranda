from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.security import utcnow
from app.models import PhotoType, Plant, PlantEvent, PlantPhoto
from app.models.base import PlantEventType
from app.repositories import PhotoRepository
from app.services.storage_service import StorageService
from app.utils import parse_datetime, validate_choice
from app.utils.files import validate_image_file


class PhotoService:
    def __init__(self):
        self.repo = PhotoRepository()
        self.storage = StorageService()

    def list_photos(self, *, plant_id: int, page: int, page_size: int):
        return self.repo.list_for_plant(
            plant_id=plant_id, page=page, page_size=page_size
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
        validate_choice(photo_type, {item.value for item in PhotoType}, "photo_type")
        original_filename, mime_type = validate_image_file(file_storage)
        relative_path = self.storage.store_plant_photo(
            plant_id=plant.id,
            file_storage=file_storage,
            original_filename=original_filename,
        )
        normalized_taken_at = parse_datetime(taken_at) if taken_at else None
        photo = PlantPhoto(
            plant_id=plant.id,
            file_path=relative_path,
            original_file_name=original_filename,
            mime_type=mime_type,
            photo_type=photo_type,
            caption=caption,
            notes=notes,
            taken_at=normalized_taken_at,
            uploaded_at=utcnow(),
        )
        self.repo.add(photo)
        self.repo.add(
            PlantEvent(
                plant_id=plant.id,
                event_type=PlantEventType.PHOTO_ADDED.value,
                occurred_at=normalized_taken_at or utcnow(),
                title="Foto adicionada",
                description=caption or notes,
                metadata_json={"photo_type": photo_type},
            )
        )
        self.repo.commit()
        return photo

    def remove_photo(self, *, photo: PlantPhoto) -> None:
        photo.removed_at = utcnow()
        self.repo.commit()

    def get_photo(self, photo_id: int) -> PlantPhoto:
        photo = self.repo.get_by_id(photo_id)
        if not photo:
            raise NotFoundError("Foto não encontrada.")
        return photo

    def build_download_url(self, plant_id: int, photo_id: int) -> str:
        return f"/api/v1/plants/{plant_id}/photos/{photo_id}/download"
