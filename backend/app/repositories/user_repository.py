from __future__ import annotations

from datetime import timedelta

from sqlalchemy import desc, or_

from app.core.config import get_settings
from app.core.security import utcnow
from app.extensions import db
from app.models import Device, LoginAttempt, PasswordResetToken, RefreshToken, User
from app.repositories.base import BaseRepository
from app.utils.validators import normalize_email


class UserRepository(BaseRepository):
    def get_by_id(self, user_id: int) -> User | None:
        if user_id <= 0:
            return None
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        normalized_email = normalize_email(email)
        stmt = db.select(User).where(User.email == normalized_email)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_users(
        self, *, page: int, page_size: int, search: str | None = None
    ) -> tuple[list[User], int]:
        stmt = db.select(User).order_by(User.created_at.desc(), User.id.desc())
        pattern = self.build_like_pattern(search)
        if pattern is not None:
            stmt = stmt.where(
                or_(
                    db.func.lower(User.name).like(pattern, escape="\\"),
                    db.func.lower(User.email).like(pattern, escape="\\"),
                )
            )
        return self.paginate(stmt, page=page, page_size=page_size)


class TokenRepository(BaseRepository):
    def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        return self.add(token)

    def get_active_refresh_token(self, token_hash: str) -> RefreshToken | None:
        cleaned_token_hash = self.clean_text(token_hash)
        if cleaned_token_hash is None:
            return None
        stmt = db.select(RefreshToken).where(
            RefreshToken.token_hash == cleaned_token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > utcnow(),
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def revoke_refresh_token(self, token_hash: str) -> int:
        cleaned_token_hash = self.clean_text(token_hash)
        if cleaned_token_hash is None:
            return 0
        stmt = (
            db.update(RefreshToken)
            .where(
                RefreshToken.token_hash == cleaned_token_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=utcnow())
            .execution_options(synchronize_session=False)
        )
        result = self.session.execute(stmt)
        return result.rowcount or 0

    def revoke_all_user_tokens(self, user_id: int) -> int:
        if user_id <= 0:
            return 0
        stmt = (
            db.update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=utcnow())
            .execution_options(synchronize_session=False)
        )
        result = self.session.execute(stmt)
        return result.rowcount or 0

    def create_password_reset_token(
        self, token: PasswordResetToken
    ) -> PasswordResetToken:
        return self.add(token)

    def get_valid_password_reset_token(
        self, token_hash: str
    ) -> PasswordResetToken | None:
        cleaned_token_hash = self.clean_text(token_hash)
        if cleaned_token_hash is None:
            return None
        stmt = db.select(PasswordResetToken).where(
            PasswordResetToken.token_hash == cleaned_token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > utcnow(),
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def consume_password_reset_token(self, token_id: int) -> None:
        if token_id <= 0:
            return
        stmt = (
            db.update(PasswordResetToken)
            .where(
                PasswordResetToken.id == token_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=utcnow())
            .execution_options(synchronize_session=False)
        )
        self.session.execute(stmt)

    def cleanup_expired_tokens(self) -> dict[str, int]:
        now = utcnow()
        expired_refresh = (
            self.session.execute(
                db.delete(RefreshToken)
                .where(
                    (RefreshToken.expires_at < now)
                    | (RefreshToken.revoked_at.is_not(None))
                )
                .execution_options(synchronize_session=False)
            ).rowcount
            or 0
        )
        expired_resets = (
            self.session.execute(
                db.delete(PasswordResetToken)
                .where(
                    (PasswordResetToken.expires_at < now)
                    | (PasswordResetToken.used_at.is_not(None))
                )
                .execution_options(synchronize_session=False)
            ).rowcount
            or 0
        )
        return {
            "refresh_tokens": expired_refresh,
            "password_reset_tokens": expired_resets,
        }


class LoginAttemptRepository(BaseRepository):
    def register_attempt(
        self, *, email: str, ip: str | None, user_agent: str | None, success: bool
    ) -> LoginAttempt:
        attempt = LoginAttempt(
            email=normalize_email(email),
            ip=(self.clean_text(ip) or None),
            user_agent=(self.clean_text(user_agent) or "")[:255] or None,
            success=success,
            created_at=utcnow(),
        )
        return self.add(attempt)

    def is_temporarily_blocked(self, *, email: str, ip: str | None) -> bool:
        normalized_email = normalize_email(email)
        cleaned_ip = self.clean_text(ip)
        settings = get_settings()
        window_start = utcnow() - timedelta(
            minutes=settings.rate_limit_login_window_minutes
        )
        conditions = [
            LoginAttempt.created_at >= window_start,
            LoginAttempt.success.is_(False),
        ]
        email_stmt = db.select(db.func.count(LoginAttempt.id)).where(
            LoginAttempt.email == normalized_email,
            *conditions,
        )
        email_failures = int(self.session.execute(email_stmt).scalar_one())
        ip_failures = 0
        if cleaned_ip is not None:
            ip_stmt = db.select(db.func.count(LoginAttempt.id)).where(
                LoginAttempt.ip == cleaned_ip,
                *conditions,
            )
            ip_failures = int(self.session.execute(ip_stmt).scalar_one())
        return max(email_failures, ip_failures) >= settings.rate_limit_login_attempts

    def recent_attempts(
        self, *, page: int, page_size: int
    ) -> tuple[list[LoginAttempt], int]:
        stmt = db.select(LoginAttempt).order_by(
            desc(LoginAttempt.created_at), desc(LoginAttempt.id)
        )
        return self.paginate(stmt, page=page, page_size=page_size)


class DeviceRepository(BaseRepository):
    def upsert_device(
        self,
        *,
        user_id: int,
        device_name: str | None,
        platform: str,
        push_token: str | None,
    ) -> Device:
        cleaned_platform = self.clean_text(platform)
        cleaned_device_name = self.clean_text(device_name)
        cleaned_push_token = self.clean_text(push_token)
        if user_id <= 0 or cleaned_platform is None:
            raise ValueError("Parâmetros inválidos para registrar dispositivo.")

        stmt = db.select(Device).where(
            Device.user_id == user_id,
            Device.platform == cleaned_platform,
        )
        if cleaned_push_token is not None:
            stmt = stmt.where(Device.push_token == cleaned_push_token)
        elif cleaned_device_name is not None:
            stmt = stmt.where(Device.device_name == cleaned_device_name)
        else:
            stmt = stmt.where(Device.push_token.is_(None), Device.device_name.is_(None))

        device = self.session.execute(stmt).scalar_one_or_none()
        now = utcnow()

        if device is None:
            device = Device(
                user_id=user_id,
                device_name=cleaned_device_name,
                platform=cleaned_platform,
                push_token=cleaned_push_token,
                notifications_enabled=True,
                last_seen_at=now,
            )
            return self.add(device)

        device.device_name = cleaned_device_name
        device.platform = cleaned_platform
        device.push_token = cleaned_push_token
        device.last_seen_at = now
        device.notifications_enabled = True
        return device

    def list_enabled_devices_for_user(self, user_id: int) -> list[Device]:
        if user_id <= 0:
            return []
        stmt = (
            db.select(Device)
            .where(
                Device.user_id == user_id,
                Device.notifications_enabled.is_(True),
                Device.push_token.is_not(None),
                db.func.length(db.func.trim(Device.push_token)) > 0,
            )
            .order_by(
                db.func.coalesce(Device.last_seen_at, Device.created_at).desc(),
                Device.id.desc(),
            )
        )
        return self.session.execute(stmt).scalars().all()
