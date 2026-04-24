from __future__ import annotations

import hashlib
from datetime import timedelta

from flask import request
from sqlalchemy import delete

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    TooManyRequestsError,
    ValidationError,
)
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
    AuthRateLimitRepository,
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
        self.rate_limits = AuthRateLimitRepository()
        self.mailer = MailService()

    @staticmethod
    def _client_ip() -> str | None:
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            first_ip = forwarded_for.split(",", 1)[0].strip()
            if first_ip:
                return first_ip
        return request.remote_addr

    @staticmethod
    def _user_agent() -> str | None:
        user_agent = request.headers.get("User-Agent", "").strip()
        return user_agent or None

    @staticmethod
    def _hash_scope_value(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _build_action_scopes(
        self,
        *,
        client_ip: str | None,
        email: str | None = None,
        token: str | None = None,
    ) -> list[str]:
        scopes: list[str] = []

        if client_ip:
            scopes.append(f"ip:{client_ip.strip()}")

        if email:
            scopes.append(f"email:{self._hash_scope_value(normalize_email(email))}")

        if token:
            cleaned_token = token.strip()
            if cleaned_token:
                scopes.append(f"token:{self._hash_scope_value(cleaned_token)}")

        return list(dict.fromkeys(scope for scope in scopes if scope))

    def _enforce_action_rate_limit(
        self,
        *,
        action: str,
        limit: int,
        window_minutes: int,
        scopes: list[str],
    ) -> None:
        clean_scopes = list(dict.fromkeys(scope for scope in scopes if scope))
        if limit <= 0 or window_minutes <= 0 or not clean_scopes:
            return

        now = utcnow()
        window_start = now - timedelta(minutes=window_minutes)

        for scope in clean_scopes:
            if (
                self.rate_limits.count_recent(
                    action=action,
                    scope_key=scope,
                    window_start=window_start,
                )
                >= limit
            ):
                raise TooManyRequestsError(
                    "Muitas tentativas. Tente novamente mais tarde."
                )

        self.rate_limits.register_hits(
            action=action,
            scope_keys=clean_scopes,
            created_at=now,
        )

        retention_hours = max(get_settings().auth_rate_limit_retention_hours, 1)
        self.rate_limits.delete_older_than(
            older_than=now - timedelta(hours=retention_hours)
        )
        self.rate_limits.commit()

    def login(self, *, email: str, password: str, device_name: str | None) -> dict:
        settings = get_settings()
        now = utcnow()
        normalized_email = normalize_email(email)
        client_ip = self._client_ip()
        user_agent = self._user_agent()

        if self.attempts.is_temporarily_blocked(email=normalized_email, ip=client_ip):
            raise TooManyRequestsError("Muitas tentativas. Tente novamente mais tarde.")

        user = self.users.get_by_email(normalized_email)
        password_matches = False
        if user and user.is_active:
            try:
                password_matches = verify_password(password, user.password_hash)
            except Exception:
                password_matches = False

        if not user or not user.is_active or not password_matches:
            self.attempts.register_attempt(
                email=normalized_email,
                ip=client_ip,
                user_agent=user_agent,
                success=False,
            )
            self.attempts.commit()
            raise AuthenticationError("Credenciais inválidas.")

        access_token, access_expires_at = create_access_token(
            user.id,
            is_admin=user.is_admin,
        )
        refresh_token_plain = generate_opaque_token()
        refresh_expires_at = now + timedelta(days=settings.refresh_token_expires_days)

        self.tokens.create_refresh_token(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token(refresh_token_plain),
                device_name=self.tokens.clean_text(device_name),
                expires_at=refresh_expires_at,
                revoked_at=None,
                created_at=now,
            )
        )
        self.attempts.register_attempt(
            email=normalized_email,
            ip=client_ip,
            user_agent=user_agent,
            success=True,
        )
        user.last_login_at = now
        self.tokens.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_plain,
            "token_type": "bearer",
            "expires_in": max(0, int((access_expires_at - now).total_seconds())),
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
            },
        }

    def refresh(self, *, refresh_token: str) -> dict:
        settings = get_settings()
        now = utcnow()
        cleaned_refresh_token = (refresh_token or "").strip()
        client_ip = self._client_ip()

        self._enforce_action_rate_limit(
            action="auth_refresh",
            limit=settings.auth_refresh_limit_attempts,
            window_minutes=settings.auth_rate_limit_window_minutes,
            scopes=self._build_action_scopes(
                client_ip=client_ip,
                token=cleaned_refresh_token or None,
            ),
        )

        if not cleaned_refresh_token:
            raise AuthenticationError("Credenciais inválidas.")

        token = self.tokens.get_active_refresh_token(
            hash_refresh_token(cleaned_refresh_token)
        )
        if not token or not token.user or not token.user.is_active:
            raise AuthenticationError("Credenciais inválidas.")

        access_token, access_expires_at = create_access_token(
            token.user_id,
            is_admin=token.user.is_admin,
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": max(0, int((access_expires_at - now).total_seconds())),
        }

    def logout(self, *, refresh_token: str) -> None:
        self.tokens.revoke_refresh_token(hash_refresh_token(refresh_token))
        self.tokens.commit()

    def forgot_password(self, *, email: str) -> None:
        settings = get_settings()
        normalized_email = normalize_email(email)
        client_ip = self._client_ip()

        self._enforce_action_rate_limit(
            action="auth_forgot_password",
            limit=settings.auth_forgot_password_limit_attempts,
            window_minutes=settings.auth_rate_limit_window_minutes,
            scopes=self._build_action_scopes(
                client_ip=client_ip,
                email=normalized_email,
            ),
        )

        user = self.users.get_by_email(normalized_email)
        if not user or not user.is_active:
            return

        now = utcnow()
        raw_token = generate_opaque_token()
        expires_at = now + timedelta(minutes=settings.password_reset_expires_minutes)

        self.tokens.session.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
        )
        self.tokens.create_password_reset_token(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_reset_token(raw_token),
                expires_at=expires_at,
                used_at=None,
                created_at=now,
            )
        )
        self.tokens.commit()

        reset_url = (
            f"{settings.frontend_base_url.rstrip('/')}/reset-password?token={raw_token}"
        )
        self.mailer.send_password_reset(to_email=user.email, reset_url=reset_url)

    def reset_password(self, *, token: str, new_password: str) -> None:
        settings = get_settings()
        cleaned_token = (token or "").strip()
        client_ip = self._client_ip()

        self._enforce_action_rate_limit(
            action="auth_reset_password",
            limit=settings.auth_reset_password_limit_attempts,
            window_minutes=settings.auth_rate_limit_window_minutes,
            scopes=self._build_action_scopes(
                client_ip=client_ip,
                token=cleaned_token or None,
            ),
        )

        if not cleaned_token:
            raise AuthenticationError("Token inválido ou expirado.")

        validate_password_strength(new_password)
        token_entity = self.tokens.get_valid_password_reset_token(
            hash_reset_token(cleaned_token)
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
        cleaned_platform = (platform or "").strip().lower()
        if not cleaned_platform:
            raise ValidationError(
                "Dados inválidos.",
                details={"platform": "Informe a plataforma do dispositivo."},
            )

        device = self.devices.upsert_device(
            user_id=user_id,
            device_name=device_name,
            platform=cleaned_platform,
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
        self,
        *,
        name: str,
        email: str,
        password: str,
        is_admin: bool,
        is_active: bool,
    ) -> User:
        cleaned_name = (name or "").strip()
        if not cleaned_name:
            raise ValidationError(
                "Dados inválidos.",
                details={"name": "Informe um nome válido."},
            )

        normalized_email = normalize_email(email)
        validate_password_strength(password)
        if self.users.get_by_email(normalized_email):
            raise ConflictError(
                "Já existe usuário com esse e-mail.",
                details={"email": "duplicated"},
            )

        user = User(
            name=cleaned_name,
            email=normalized_email,
            password_hash=hash_password(password),
            is_admin=bool(is_admin),
            is_active=bool(is_active),
        )
        self.users.add(user)
        self.users.commit()
        return user
