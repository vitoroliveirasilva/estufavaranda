from __future__ import annotations

from typing import TypeVar

from flask import request
from pydantic import BaseModel, ValidationError as PydanticValidationError
from werkzeug.exceptions import BadRequest

from app.core.exceptions import ValidationError

ModelT = TypeVar("ModelT", bound=BaseModel)


def parse_json(model_class: type[ModelT]) -> ModelT:
    if not issubclass(model_class, BaseModel):
        raise TypeError("model_class deve ser uma subclasse de BaseModel.")

    if not request.is_json:
        raise ValidationError(
            "Corpo JSON inválido.",
            details={"body": "Envie um corpo JSON com Content-Type application/json."},
        )

    try:
        payload = request.get_json(silent=False)
    except BadRequest as exc:
        raise ValidationError("Corpo JSON inválido.") from exc

    if payload is None:
        raise ValidationError("Corpo JSON inválido.")

    try:
        return model_class.model_validate(payload)
    except PydanticValidationError as exc:
        details: dict[str, str] = {}
        for error in exc.errors():
            location = error.get("loc") or ("body",)
            field = ".".join(str(item) for item in location) or "body"
            details.setdefault(field, error.get("msg", "Valor inválido."))
        raise ValidationError(details=details) from exc
