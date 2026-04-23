from __future__ import annotations

from datetime import timedelta

from sqlalchemy import desc

from app.core.config import get_settings
from app.core.security import utcnow
from app.extensions import db
from app.models import Device, LoginAttempt, PasswordResetToken, RefreshToken, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = db.select(User).where(User.email == email)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_users(self, *, page: int, page_size: int, search: str | None = None):
        stmt = db.select(User).order_by(User.created_at.desc())
        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                db.func.lower(User.name).like(pattern)
                | db.func.lower(User.email).like(pattern)
            )
        return self.paginate(stmt, page=page, page_size=page_size)


class TokenRepository(BaseRepository):
    def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self.add(token)
        return token

    def get_active_refresh_token(self, token_hash: str) -> RefreshToken | None:
        stmt = db.select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > utcnow(),
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def revoke_refresh_token(self, token_hash: str) -> int:
        stmt = (
            db.update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=utcnow())
        )
        result = self.session.execute(stmt)
        return result.rowcount or 0

    def revoke_all_user_tokens(self, user_id: int) -> int:
        stmt = (
            db.update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=utcnow())
        )
        result = self.session.execute(stmt)
        return result.rowcount or 0

    def create_password_reset_token(
        self, token: PasswordResetToken
    ) -> PasswordResetToken:
        self.add(token)
        return token

    def get_valid_password_reset_token(
        self, token_hash: str
    ) -> PasswordResetToken | None:
        stmt = db.select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > utcnow(),
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def consume_password_reset_token(self, token_id: int) -> None:
        token = self.session.get(PasswordResetToken, token_id)
        if token:
            token.used_at = utcnow()

    def cleanup_expired_tokens(self) -> dict[str, int]:
        now = utcnow()
        expired_refresh = (
            self.session.execute(
                db.delete(RefreshToken).where(
                    (RefreshToken.expires_at < now)
                    | (RefreshToken.revoked_at.is_not(None))
                )
            ).rowcount
            or 0
        )
        expired_resets = (
            self.session.execute(
                db.delete(PasswordResetToken).where(
                    (PasswordResetToken.expires_at < now)
                    | (PasswordResetToken.used_at.is_not(None))
                )
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
            email=email,
            ip=ip,
            user_agent=user_agent,
            success=success,
            created_at=utcnow(),
        )
        self.add(attempt)
        return attempt

    def is_temporarily_blocked(self, *, email: str, ip: str | None) -> bool:
        settings = get_settings()
        window_start = utcnow() - timedelta(
            minutes=settings.rate_limit_login_window_minutes
        )
        conditions = [
            LoginAttempt.created_at >= window_start,
            LoginAttempt.success.is_(False),
        ]
        email_stmt = db.select(db.func.count(LoginAttempt.id)).where(
            LoginAttempt.email == email, *conditions
        )
        email_failures = self.session.execute(email_stmt).scalar_one()
        ip_failures = 0
        if ip:
            ip_stmt = db.select(db.func.count(LoginAttempt.id)).where(
                LoginAttempt.ip == ip, *conditions
            )
            ip_failures = self.session.execute(ip_stmt).scalar_one()
        return max(email_failures, ip_failures) >= settings.rate_limit_login_attempts

    def recent_attempts(self, *, page: int, page_size: int):
        stmt = db.select(LoginAttempt).order_by(desc(LoginAttempt.created_at))
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
        stmt = db.select(Device).where(
            Device.user_id == user_id,
            Device.platform == platform,
            Device.push_token == push_token,
        )
        device = self.session.execute(stmt).scalar_one_or_none()
        if device is None:
            device = Device(
                user_id=user_id,
                device_name=device_name,
                platform=platform,
                push_token=push_token,
                last_seen_at=utcnow(),
            )
            self.add(device)
            return device

        device.device_name = device_name
        device.last_seen_at = utcnow()
        device.notifications_enabled = True
        return device

    def list_enabled_devices_for_user(self, user_id: int) -> list[Device]:
        stmt = db.select(Device).where(
            Device.user_id == user_id,
            Device.notifications_enabled.is_(True),
        )
        return self.session.execute(stmt).scalars().all()
