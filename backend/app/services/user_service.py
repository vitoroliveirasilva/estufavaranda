from __future__ import annotations

import secrets

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models import User
from app.repositories import LoginAttemptRepository, TokenRepository, UserRepository
from app.utils.validators import normalize_email, validate_password_strength


class UserService:
    def __init__(self):
        self.users = UserRepository()
        self.tokens = TokenRepository()
        self.login_attempts = LoginAttemptRepository()

    def list_users(self, *, page: int, page_size: int, search: str | None):
        return self.users.list_users(page=page, page_size=page_size, search=search)

    def get_user(self, user_id: int) -> User:
        user = self.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado.")
        return user

    def update_user(self, user_id: int, **changes) -> User:
        user = self.get_user(user_id)
        if "email" in changes and changes["email"] is not None:
            normalized_email = normalize_email(changes["email"])
            existing = self.users.get_by_email(normalized_email)
            if existing and existing.id != user.id:
                raise ConflictError(
                    "Já existe usuário com esse e-mail.",
                    details={"email": "duplicated"},
                )
            user.email = normalized_email
        if "name" in changes and changes["name"] is not None:
            user.name = changes["name"].strip()
        if "is_admin" in changes:
            user.is_admin = changes["is_admin"]
        if "is_active" in changes:
            user.is_active = changes["is_active"]
        self.users.commit()
        return user

    def activate_user(self, user_id: int) -> User:
        return self.update_user(user_id, is_active=True)

    def deactivate_user(self, user_id: int) -> User:
        return self.update_user(user_id, is_active=False)

    def revoke_sessions(self, user_id: int) -> int:
        self.get_user(user_id)
        count = self.tokens.revoke_all_user_tokens(user_id)
        self.tokens.commit()
        return count

    def admin_reset_password(
        self, user_id: int, new_password: str | None = None
    ) -> dict:
        user = self.get_user(user_id)
        temp_password = new_password or f"Tmp{secrets.token_urlsafe(10)}9"
        validate_password_strength(temp_password)
        user.password_hash = hash_password(temp_password)
        self.tokens.revoke_all_user_tokens(user_id)
        self.users.commit()
        return {"temporary_password": temp_password, "user_id": user.id}

    def list_login_attempts(self, *, page: int, page_size: int):
        return self.login_attempts.recent_attempts(page=page, page_size=page_size)
