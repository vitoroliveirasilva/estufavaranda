from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from flask import send_file

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.utils.files import build_storage_path


class StorageService:
    def _base_path(self) -> Path:
        return Path(get_settings().upload_base_path).resolve()

    def store_plant_photo(
        self, *, plant_id: int, file_storage, original_filename: str
    ) -> str:
        if plant_id <= 0:
            raise ValueError("plant_id inválido para armazenamento de foto.")

        relative_path = build_storage_path(
            plant_id=plant_id,
            original_filename=original_filename,
        )
        destination = self._base_path() / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)

        temp_destination = destination.with_name(
            f"{destination.name}.{uuid4().hex}.tmp"
        )
        try:
            file_storage.stream.seek(0)
            file_storage.save(temp_destination)
            os.replace(temp_destination, destination)
        except Exception:
            try:
                temp_destination.unlink(missing_ok=True)
            except Exception:
                pass
            raise

        return relative_path

    def resolve_path(self, relative_path: str) -> Path:
        cleaned = (relative_path or "").strip().replace("\\", "/")
        if not cleaned:
            raise NotFoundError("Arquivo não encontrado.")

        base_path = self._base_path()
        resolved = (base_path / cleaned).resolve()
        if not resolved.is_relative_to(base_path):
            raise NotFoundError("Arquivo não encontrado.")
        if not resolved.exists() or not resolved.is_file():
            raise NotFoundError("Arquivo não encontrado.")
        return resolved

    def delete_file(self, relative_path: str) -> None:
        try:
            path = self.resolve_path(relative_path)
        except NotFoundError:
            return
        path.unlink(missing_ok=True)

    def send_protected_file(self, relative_path: str, *, mime_type: str | None = None):
        path = self.resolve_path(relative_path)
        return send_file(path, mimetype=mime_type, conditional=True, etag=True)
