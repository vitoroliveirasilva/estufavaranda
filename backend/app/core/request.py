from __future__ import annotations

from flask import request
from pydantic import BaseModel, ValidationError as PydanticValidationError

from app.core.exceptions import ValidationError


def parse_json(model_class: type[BaseModel]) -> BaseModel:
    payload = request.get_json(silent=True)
    if payload is None:
        raise ValidationError("Corpo JSON inválido.")
    try:
        return model_class.model_validate(payload)
    except PydanticValidationError as exc:
        details = {}
        for error in exc.errors():
            field = ".".join(str(item) for item in error["loc"])
            details[field] = error["msg"]
        raise ValidationError(details=details) from exc
