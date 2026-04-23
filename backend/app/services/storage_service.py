from __future__ import annotations

from pathlib import Path

from flask import send_file

from app.core.config import get_settings
from app.utils.files import build_storage_path


class StorageService:
    def store_plant_photo(
        self, *, plant_id: int, file_storage, original_filename: str
    ) -> str:
        settings = get_settings()
        relative_path = build_storage_path(
            plant_id=plant_id, original_filename=original_filename
        )
        destination = Path(settings.upload_base_path) / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        file_storage.save(destination)
        return relative_path

    def resolve_path(self, relative_path: str) -> Path:
        settings = get_settings()
        return Path(settings.upload_base_path) / relative_path

    def send_protected_file(self, relative_path: str, *, mime_type: str | None = None):
        path = self.resolve_path(relative_path)
        return send_file(path, mimetype=mime_type, conditional=True)
