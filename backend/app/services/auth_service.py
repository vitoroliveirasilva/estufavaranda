from __future__ import annotations

from datetime import timedelta

from flask import request

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError, TooManyRequestsError
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_refresh_token,
    hash_reset_token,
    utcnow,
    verify_password,
)
from app.models import PasswordResetToken, RefreshToken, User
from app.repositories import (
    DeviceRepository,
    LoginAttemptRepository,
    TokenRepository,
    UserRepository,
)
from app.services.mail_service import MailService
from app.utils.validators import normalize_email, validate_password_strength


class AuthService:
    def __init__(self):
        self.users = UserRepository()
        self.tokens = TokenRepository()
        self.attempts = LoginAttemptRepository()
        self.devices = DeviceRepository()
        self.mailer = MailService()

    def login(self, *, email: str, password: str, device_name: str | None) -> dict:
        normalized_email = normalize_email(email)
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        user_agent = request.headers.get("User-Agent")

        if self.attempts.is_temporarily_blocked(email=normalized_email, ip=client_ip):
            self.attempts.register_attempt(
                email=normalized_email,
                ip=client_ip,
                user_agent=user_agent,
                success=False,
            )
            self.attempts.commit()
            raise TooManyRequestsError("Muitas tentativas. Tente novamente mais tarde.")

        user = self.users.get_by_email(normalized_email)
        if (
            not user
            or not user.is_active
            or not verify_password(password, user.password_hash)
        ):
            self.attempts.register_attempt(
                email=normalized_email,
                ip=client_ip,
                user_agent=user_agent,
                success=False,
            )
            self.attempts.commit()
            raise AuthenticationError("Credenciais inválidas.")

        access_token, access_expires_at = create_access_token(
            user.id, is_admin=user.is_admin
        )
        refresh_token_plain = generate_opaque_token()
        refresh_expires_at = utcnow() + timedelta(
            days=get_settings().refresh_token_expires_days
        )

        self.tokens.create_refresh_token(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token(refresh_token_plain),
                device_name=device_name,
                expires_at=refresh_expires_at,
                revoked_at=None,
                created_at=utcnow(),
            )
        )
        self.attempts.register_attempt(
            email=normalized_email, ip=client_ip, user_agent=user_agent, success=True
        )
        user.last_login_at = utcnow()
        self.tokens.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_plain,
            "token_type": "bearer",
            "expires_in": int((access_expires_at - utcnow()).total_seconds()),
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
            },
        }

    def refresh(self, *, refresh_token: str) -> dict:
        token = self.tokens.get_active_refresh_token(hash_refresh_token(refresh_token))
        if not token or not token.user or not token.user.is_active:
            raise AuthenticationError("Credenciais inválidas.")

        access_token, access_expires_at = create_access_token(
            token.user_id, is_admin=token.user.is_admin
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int((access_expires_at - utcnow()).total_seconds()),
        }

    def logout(self, *, refresh_token: str) -> None:
        self.tokens.revoke_refresh_token(hash_refresh_token(refresh_token))
        self.tokens.commit()

    def forgot_password(self, *, email: str) -> None:
        normalized_email = normalize_email(email)
        user = self.users.get_by_email(normalized_email)
        if not user or not user.is_active:
            return

        raw_token = generate_opaque_token()
        expires_at = utcnow() + timedelta(
            minutes=get_settings().password_reset_expires_minutes
        )
        self.tokens.create_password_reset_token(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_reset_token(raw_token),
                expires_at=expires_at,
                used_at=None,
                created_at=utcnow(),
            )
        )
        self.tokens.commit()

        reset_url = f"{get_settings().frontend_base_url.rstrip('/')}/reset-password?token={raw_token}"
        self.mailer.send_password_reset(to_email=user.email, reset_url=reset_url)

    def reset_password(self, *, token: str, new_password: str) -> None:
        validate_password_strength(new_password)
        token_entity = self.tokens.get_valid_password_reset_token(
            hash_reset_token(token)
        )
        if not token_entity or not token_entity.user or not token_entity.user.is_active:
            raise AuthenticationError("Token inválido ou expirado.")

        token_entity.user.password_hash = hash_password(new_password)
        self.tokens.consume_password_reset_token(token_entity.id)
        self.tokens.revoke_all_user_tokens(token_entity.user_id)
        self.tokens.commit()

    def register_device(
        self,
        *,
        user_id: int,
        device_name: str | None,
        platform: str,
        push_token: str | None,
    ) -> dict:
        device = self.devices.upsert_device(
            user_id=user_id,
            device_name=device_name,
            platform=platform,
            push_token=push_token,
        )
        self.devices.commit()
        return {
            "id": device.id,
            "device_name": device.device_name,
            "platform": device.platform,
            "push_token": device.push_token,
            "notifications_enabled": device.notifications_enabled,
        }

    def admin_create_user(
        self, *, name: str, email: str, password: str, is_admin: bool, is_active: bool
    ) -> User:
        normalized_email = normalize_email(email)
        validate_password_strength(password)
        if self.users.get_by_email(normalized_email):
            raise ConflictError(
                "Já existe usuário com esse e-mail.", details={"email": "duplicated"}
            )

        user = User(
            name=name.strip(),
            email=normalized_email,
            password_hash=hash_password(password),
            is_admin=is_admin,
            is_active=is_active,
        )
        self.users.add(user)
        self.users.commit()
        return user
