from __future__ import annotations

import os
import secrets
import warnings
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.core.config import get_settings
from app.core.exceptions import ValidationError

_ALLOWED_FORMAT_EXTENSIONS = {
    "JPEG": {"jpg", "jpeg"},
    "PNG": {"png"},
    "WEBP": {"webp"},
}
_ALLOWED_FORMAT_MIME_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
_DEFAULT_EXTENSION = "jpg"
_SAFE_MAX_IMAGE_PIXELS = 40_000_000


def sanitize_filename(filename: str | None) -> str:
    if not filename:
        return "arquivo"

    sanitized = secure_filename(Path(str(filename)).name)
    return sanitized or "arquivo"


def _normalize_allowed_extensions(raw_values: set[str]) -> set[str]:
    return {
        str(value).lower().lstrip(".") for value in raw_values if str(value).strip()
    }


def _normalize_allowed_mime_types(raw_values: set[str]) -> set[str]:
    return {str(value).lower() for value in raw_values if str(value).strip()}


def _get_stream_size(file_storage: FileStorage) -> int:
    stream = file_storage.stream
    try:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(0)
    except (AttributeError, OSError) as exc:
        raise ValidationError(
            "Arquivo de imagem inválido.",
            details={"file": "Não foi possível processar o arquivo enviado."},
        ) from exc

    if size <= 0:
        raise ValidationError(
            "Arquivo de imagem inválido.",
            details={"file": "O arquivo enviado está vazio."},
        )
    return size


def validate_image_file(file_storage: FileStorage) -> tuple[str, str]:
    if not isinstance(file_storage, FileStorage):
        raise ValidationError(
            "Arquivo de imagem inválido.",
            details={"file": "Arquivo ausente ou inválido."},
        )

    settings = get_settings()
    allowed_extensions = _normalize_allowed_extensions(
        settings.allowed_image_extensions_set
    )
    allowed_mime_types = _normalize_allowed_mime_types(
        settings.allowed_image_mime_types_set
    )

    filename = sanitize_filename(file_storage.filename)
    extension = Path(filename).suffix.lower().lstrip(".")
    if not extension or extension not in allowed_extensions:
        raise ValidationError(
            "Tipo de arquivo não permitido.",
            details={"file": "Extensão inválida."},
        )

    declared_mime_type = (file_storage.mimetype or "").strip().lower()
    if not declared_mime_type or declared_mime_type not in allowed_mime_types:
        raise ValidationError(
            "Tipo de arquivo não permitido.",
            details={"file": "MIME inválido."},
        )

    file_size = _get_stream_size(file_storage)
    max_upload_bytes = int(getattr(settings, "max_upload_bytes", 0) or 0)
    if max_upload_bytes and file_size > max_upload_bytes:
        raise ValidationError(
            "Arquivo excede o tamanho máximo permitido.",
            details={"file": "O arquivo enviado é maior que o limite permitido."},
        )

    original_max_pixels = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = _SAFE_MAX_IMAGE_PIXELS
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(file_storage.stream) as image:
                image.verify()

        file_storage.stream.seek(0)
        with Image.open(file_storage.stream) as image:
            image.load()
            detected_format = (image.format or "").upper()
            if image.width <= 0 or image.height <= 0:
                raise ValidationError(
                    "Arquivo de imagem inválido.",
                    details={"file": "A imagem possui dimensões inválidas."},
                )
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ValidationError(
            "Arquivo de imagem inválido.",
            details={"file": "Não foi possível validar a imagem."},
        ) from exc
    finally:
        Image.MAX_IMAGE_PIXELS = original_max_pixels
        file_storage.stream.seek(0)

    expected_extensions = _ALLOWED_FORMAT_EXTENSIONS.get(detected_format)
    detected_mime_type = _ALLOWED_FORMAT_MIME_TYPES.get(detected_format)
    if not expected_extensions or not detected_mime_type:
        raise ValidationError(
            "Tipo de arquivo não permitido.",
            details={"file": "Conteúdo inválido."},
        )

    if extension not in expected_extensions:
        raise ValidationError(
            "Tipo de arquivo não permitido.",
            details={"file": "A extensão não corresponde ao conteúdo do arquivo."},
        )

    if detected_mime_type not in allowed_mime_types:
        raise ValidationError(
            "Tipo de arquivo não permitido.",
            details={"file": "O conteúdo do arquivo não é aceito."},
        )

    return filename, detected_mime_type


def build_storage_path(*, plant_id: int, original_filename: str) -> str:
    try:
        normalized_plant_id = int(plant_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "Identificador inválido informado.",
            details={"plant_id": "Informe um identificador válido."},
        ) from exc

    if normalized_plant_id <= 0:
        raise ValidationError(
            "Identificador inválido informado.",
            details={"plant_id": "Informe um identificador válido."},
        )

    sanitized_filename = sanitize_filename(original_filename)
    extension = (
        Path(sanitized_filename).suffix.lower().lstrip(".") or _DEFAULT_EXTENSION
    )
    if extension not in {
        item for values in _ALLOWED_FORMAT_EXTENSIONS.values() for item in values
    }:
        extension = _DEFAULT_EXTENSION

    token = secrets.token_hex(16)
    relative_path = Path(str(normalized_plant_id)) / token[:2] / f"{token}.{extension}"
    return os.fspath(relative_path)
