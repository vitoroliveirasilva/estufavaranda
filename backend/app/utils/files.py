from __future__ import annotations

import imghdr
import os
import secrets
from pathlib import Path

from PIL import Image

from app.core.config import get_settings
from app.core.exceptions import ValidationError


def sanitize_filename(filename: str | None) -> str:
    if not filename:
        return "arquivo"
    return Path(filename).name.strip().replace(" ", "_")


def validate_image_file(file_storage) -> tuple[str, str]:
    settings = get_settings()
    filename = sanitize_filename(file_storage.filename)
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in settings.allowed_image_extensions_set:
        raise ValidationError(
            "Tipo de arquivo não permitido.", details={"file": "Extensão inválida."}
        )

    mime_type = (file_storage.mimetype or "").lower()
    if mime_type not in settings.allowed_image_mime_types_set:
        raise ValidationError(
            "Tipo de arquivo não permitido.", details={"file": "MIME inválido."}
        )

    current_position = file_storage.stream.tell()
    raw_bytes = file_storage.stream.read()
    file_storage.stream.seek(current_position)
    kind = imghdr.what(None, h=raw_bytes)
    if kind not in {"jpeg", "png", "webp"}:
        raise ValidationError(
            "Tipo de arquivo não permitido.", details={"file": "Conteúdo inválido."}
        )

    try:
        image = Image.open(file_storage.stream)
        image.verify()
    except Exception as exc:
        raise ValidationError(
            "Arquivo de imagem inválido.",
            details={"file": "Não foi possível validar a imagem."},
        ) from exc
    finally:
        file_storage.stream.seek(0)

    return filename, mime_type


def build_storage_path(*, plant_id: int, original_filename: str) -> str:
    extension = Path(original_filename).suffix.lower() or ".jpg"
    token = secrets.token_hex(16)
    relative = Path(str(plant_id)) / token[:2] / f"{token}{extension}"
    return os.fspath(relative)
