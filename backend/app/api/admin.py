from flask import Blueprint, request

from app.core.auth import admin_required
from app.core.request import parse_json
from app.core.response import ok
from app.schemas import (
    AdminCreateUserInput,
    AdminResetPasswordInput,
    AdminUpdateUserInput,
)
from app.services import AuthService, UserService
from app.utils.pagination import build_pagination_meta

admin_bp = Blueprint("admin", __name__)
auth_service = AuthService()
user_service = UserService()


@admin_bp.get("/users")
@admin_required
def list_users():
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(100, max(1, int(request.args.get("page_size", 20))))
    search = request.args.get("search")
    users, total = user_service.list_users(
        page=page, page_size=page_size, search=search
    )
    return ok(
        [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "last_login_at": (
                    user.last_login_at.isoformat() if user.last_login_at else None
                ),
                "created_at": user.created_at.isoformat(),
            }
            for user in users
        ],
        meta=build_pagination_meta(page=page, page_size=page_size, total=total),
    )


@admin_bp.post("/users")
@admin_required
def create_user():
    payload = parse_json(AdminCreateUserInput)
    user = auth_service.admin_create_user(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        is_admin=payload.is_admin,
        is_active=payload.is_active,
    )
    return ok(
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
        },
        status=201,
    )


@admin_bp.patch("/users/<int:user_id>")
@admin_required
def update_user(user_id: int):
    payload = parse_json(AdminUpdateUserInput)
    user = user_service.update_user(user_id, **payload.model_dump(exclude_unset=True))
    return ok(
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
        }
    )


@admin_bp.patch("/users/<int:user_id>/activate")
@admin_required
def activate_user(user_id: int):
    user = user_service.activate_user(user_id)
    return ok({"id": user.id, "is_active": user.is_active})


@admin_bp.patch("/users/<int:user_id>/deactivate")
@admin_required
def deactivate_user(user_id: int):
    user = user_service.deactivate_user(user_id)
    return ok({"id": user.id, "is_active": user.is_active})


@admin_bp.post("/users/<int:user_id>/reset-password")
@admin_required
def reset_user_password(user_id: int):
    payload = parse_json(AdminResetPasswordInput)
    result = user_service.admin_reset_password(
        user_id, new_password=payload.new_password
    )
    return ok(result)


@admin_bp.post("/users/<int:user_id>/revoke-sessions")
@admin_required
def revoke_sessions(user_id: int):
    revoked = user_service.revoke_sessions(user_id)
    return ok({"revoked_sessions": revoked})


@admin_bp.get("/login-attempts")
@admin_required
def login_attempts():
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(100, max(1, int(request.args.get("page_size", 20))))
    items, total = user_service.list_login_attempts(page=page, page_size=page_size)
    return ok(
        [
            {
                "id": item.id,
                "email": item.email,
                "ip": item.ip,
                "user_agent": item.user_agent,
                "success": item.success,
                "created_at": item.created_at.isoformat(),
            }
            for item in items
        ],
        meta=build_pagination_meta(page=page, page_size=page_size, total=total),
    )
