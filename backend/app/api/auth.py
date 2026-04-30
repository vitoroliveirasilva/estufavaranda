from __future__ import annotations

from flask import Blueprint, g

from app.core.auth import auth_required
from app.core.request import parse_json
from app.core.response import no_content, ok
from app.schemas import (
    DeviceRegisterInput,
    ForgotPasswordInput,
    LoginInput,
    LogoutInput,
    RefreshInput,
    ResetPasswordInput,
)
from app.services import AuthService

auth_bp = Blueprint("auth", __name__)
service = AuthService()


@auth_bp.post("/login")
def login():
    payload = parse_json(LoginInput)
    return ok(
        service.login(
            email=payload.email,
            password=payload.password,
            device_name=payload.device_name,
        )
    )


@auth_bp.post("/refresh")
def refresh():
    payload = parse_json(RefreshInput)
    return ok(service.refresh(refresh_token=payload.refresh_token))


@auth_bp.post("/logout")
def logout():
    payload = parse_json(LogoutInput)
    service.logout(refresh_token=payload.refresh_token)
    return no_content()


@auth_bp.get("/me")
@auth_required
def me():
    user = g.current_user
    return ok(
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "last_login_at": (
                user.last_login_at.isoformat() if user.last_login_at else None
            ),
        }
    )


@auth_bp.post("/forgot-password")
def forgot_password():
    payload = parse_json(ForgotPasswordInput)
    service.forgot_password(email=payload.email, captcha_token=payload.captcha_token)
    return ok(
        {
            "message": "Se o e-mail estiver cadastrado, você receberá instruções para redefinir sua senha."
        }
    )


@auth_bp.post("/reset-password")
def reset_password():
    payload = parse_json(ResetPasswordInput)
    service.reset_password(token=payload.token, new_password=payload.new_password)
    return ok({"message": "Senha redefinida com sucesso."})


@auth_bp.post("/devices/register")
@auth_required
def register_device():
    payload = parse_json(DeviceRegisterInput)
    return ok(
        service.register_device(
            user_id=g.current_user.id,
            device_name=payload.device_name,
            platform=payload.platform,
            push_token=payload.push_token,
        )
    )
