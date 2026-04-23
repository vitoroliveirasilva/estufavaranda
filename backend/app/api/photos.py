from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.exceptions import ValidationError
from app.core.response import no_content, ok
from app.services import PhotoService, PlantService
from app.utils.pagination import build_pagination_meta

photos_bp = Blueprint("photos", __name__)
plants = PlantService()
service = PhotoService()


@photos_bp.get("/<int:plant_id>/photos")
@auth_required
def list_photos(plant_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(100, max(1, int(request.args.get("page_size", 20))))
    items, total = service.list_photos(
        plant_id=plant_id, page=page, page_size=page_size
    )
    return ok(
        [
            {
                "id": photo.id,
                "photo_type": photo.photo_type,
                "caption": photo.caption,
                "notes": photo.notes,
                "taken_at": photo.taken_at.isoformat() if photo.taken_at else None,
                "uploaded_at": photo.uploaded_at.isoformat(),
                "download_url": service.build_download_url(plant_id, photo.id),
            }
            for photo in items
        ],
        meta=build_pagination_meta(page=page, page_size=page_size, total=total),
    )


@photos_bp.post("/<int:plant_id>/photos")
@auth_required
def create_photo(plant_id: int):
    plant = plants.get_plant(plant_id, current_user=g.current_user)
    file_storage = request.files.get("file")
    if not file_storage:
        raise ValidationError("Arquivo não enviado.", details={"file": "required"})
    photo_type = request.form.get("photo_type", "routine")
    caption = request.form.get("caption")
    notes = request.form.get("notes")
    taken_at_raw = request.form.get("taken_at")
    taken_at = taken_at_raw or None

    photo = service.create_photo(
        plant=plant,
        file_storage=file_storage,
        photo_type=photo_type,
        caption=caption,
        notes=notes,
        taken_at=taken_at,
    )
    return ok(
        {
            "id": photo.id,
            "download_url": service.build_download_url(plant_id, photo.id),
        },
        status=201,
    )


@photos_bp.delete("/<int:plant_id>/photos/<int:photo_id>")
@auth_required
def delete_photo(plant_id: int, photo_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    photo = service.get_photo(photo_id)
    if photo.plant_id != plant_id or photo.removed_at is not None:
        raise ValidationError("Foto não pertence à planta informada.")
    service.remove_photo(photo=photo)
    return no_content()


@photos_bp.get("/<int:plant_id>/photos/<int:photo_id>/download")
@auth_required
def download_photo(plant_id: int, photo_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    photo = service.get_photo(photo_id)
    if photo.plant_id != plant_id or photo.removed_at is not None:
        raise ValidationError("Foto não pertence à planta informada.")
    return service.storage.send_protected_file(
        photo.file_path, mime_type=photo.mime_type
    )
