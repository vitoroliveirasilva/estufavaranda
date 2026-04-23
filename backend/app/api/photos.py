from __future__ import annotations

from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.exceptions import NotFoundError, ValidationError
from app.core.response import no_content, ok
from app.services import PhotoService, PlantService
from app.utils.pagination import build_pagination_meta

photos_bp = Blueprint("photos", __name__)
plants = PlantService()
service = PhotoService()


def _parse_positive_int_arg(
    name: str,
    default: int,
    *,
    minimum: int = 1,
    maximum: int | None = None,
) -> int:
    raw_value = request.args.get(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "Parâmetro de consulta inválido.",
            details={name: "Informe um número inteiro válido."},
        ) from exc

    if value < minimum or (maximum is not None and value > maximum):
        limit_text = (
            f"entre {minimum} e {maximum}" if maximum is not None else f">= {minimum}"
        )
        raise ValidationError(
            "Parâmetro de consulta inválido.",
            details={name: f"Informe um valor {limit_text}."},
        )

    return value


def _normalize_optional_form_value(name: str) -> str | None:
    raw_value = request.form.get(name)
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


def _get_owned_photo(*, plant_id: int, photo_id: int):
    photo = service.get_photo(photo_id)
    if photo.plant_id != plant_id or photo.removed_at is not None:
        raise NotFoundError("Foto não encontrada.")
    return photo


@photos_bp.get("/<int:plant_id>/photos")
@auth_required
def list_photos(plant_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    page = _parse_positive_int_arg("page", 1, minimum=1)
    page_size = _parse_positive_int_arg("page_size", 20, minimum=1, maximum=100)
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
    if not file_storage or not getattr(file_storage, "filename", "").strip():
        raise ValidationError("Arquivo não enviado.", details={"file": "required"})

    photo = service.create_photo(
        plant=plant,
        file_storage=file_storage,
        photo_type=_normalize_optional_form_value("photo_type") or "routine",
        caption=_normalize_optional_form_value("caption"),
        notes=_normalize_optional_form_value("notes"),
        taken_at=_normalize_optional_form_value("taken_at"),
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
    photo = _get_owned_photo(plant_id=plant_id, photo_id=photo_id)
    service.remove_photo(photo=photo)
    return no_content()


@photos_bp.get("/<int:plant_id>/photos/<int:photo_id>/download")
@auth_required
def download_photo(plant_id: int, photo_id: int):
    plants.get_plant(plant_id, current_user=g.current_user)
    photo = _get_owned_photo(plant_id=plant_id, photo_id=photo_id)
    return service.storage.send_protected_file(
        photo.file_path, mime_type=photo.mime_type
    )
