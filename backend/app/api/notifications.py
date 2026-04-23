from __future__ import annotations

from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.exceptions import ValidationError
from app.core.response import ok
from app.models import NotificationStatus
from app.services import NotificationService
from app.utils import validate_choice
from app.utils.pagination import build_pagination_meta

notifications_bp = Blueprint("notifications", __name__)
service = NotificationService()

_ALLOWED_STATUS_VALUES = {item.value for item in NotificationStatus}


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


def _optional_status_arg() -> str | None:
    raw_value = request.args.get("status")
    if raw_value is None:
        return None
    value = raw_value.strip().lower()
    if not value:
        return None
    validate_choice(value, _ALLOWED_STATUS_VALUES, "status")
    return value


@notifications_bp.get("/notifications")
@auth_required
def list_notifications():
    page = _parse_positive_int_arg("page", 1, minimum=1)
    page_size = _parse_positive_int_arg("page_size", 20, minimum=1, maximum=100)
    status = _optional_status_arg()
    items, total = service.list_notifications(
        user_id=g.current_user.id, status=status, page=page, page_size=page_size
    )
    return ok(
        [
            {
                "id": item.id,
                "plant_id": item.plant_id,
                "type": item.type,
                "title": item.title,
                "body": item.body,
                "status": item.status,
                "created_at": item.created_at.isoformat(),
                "read_at": item.read_at.isoformat() if item.read_at else None,
                "discarded_at": (
                    item.discarded_at.isoformat() if item.discarded_at else None
                ),
            }
            for item in items
        ],
        meta=build_pagination_meta(page=page, page_size=page_size, total=total),
    )


@notifications_bp.patch("/notifications/<int:notification_id>/read")
@auth_required
def mark_read(notification_id: int):
    item = service.mark_read(user_id=g.current_user.id, notification_id=notification_id)
    return ok(
        {
            "id": item.id,
            "status": item.status,
            "read_at": item.read_at.isoformat() if item.read_at else None,
        }
    )


@notifications_bp.patch("/notifications/<int:notification_id>/discard")
@auth_required
def discard(notification_id: int):
    item = service.discard(user_id=g.current_user.id, notification_id=notification_id)
    return ok(
        {
            "id": item.id,
            "status": item.status,
            "discarded_at": (
                item.discarded_at.isoformat() if item.discarded_at else None
            ),
        }
    )
