from flask import Blueprint, g, request

from app.core.auth import auth_required
from app.core.response import ok
from app.services import NotificationService
from app.utils.pagination import build_pagination_meta

notifications_bp = Blueprint("notifications", __name__)
service = NotificationService()


@notifications_bp.get("/notifications")
@auth_required
def list_notifications():
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(100, max(1, int(request.args.get("page_size", 20))))
    status = request.args.get("status")
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
    return ok({"id": item.id, "status": item.status})


@notifications_bp.patch("/notifications/<int:notification_id>/discard")
@auth_required
def discard(notification_id: int):
    item = service.discard(user_id=g.current_user.id, notification_id=notification_id)
    return ok({"id": item.id, "status": item.status})
