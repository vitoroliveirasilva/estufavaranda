from __future__ import annotations

import secrets

from sqlalchemy import func, select

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.security import hash_password
from app.models import User
from app.repositories import LoginAttemptRepository, TokenRepository, UserRepository
from app.utils.validators import normalize_email, validate_password_strength


class UserService:
    def __init__(self):
        self.users = UserRepository()
        self.tokens = TokenRepository()
        self.login_attempts = LoginAttemptRepository()

    def _active_admins_count(self) -> int:
        stmt = select(func.count(User.id)).where(
            User.is_admin.is_(True),
            User.is_active.is_(True),
        )
        return int(self.users.session.execute(stmt).scalar_one())

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
            cleaned_name = (changes["name"] or "").strip()
            if not cleaned_name:
                raise ValidationError(
                    "Dados inválidos.",
                    details={"name": "Informe um nome válido."},
                )
            user.name = cleaned_name

        requested_is_admin = changes.get("is_admin")
        if (
            requested_is_admin is not None
            and requested_is_admin is False
            and user.is_admin
        ):
            if self._active_admins_count() <= 1 and user.is_active:
                raise ValidationError(
                    "Dados inválidos.",
                    details={
                        "is_admin": "Não é permitido remover o último administrador ativo."
                    },
                )
            user.is_admin = False
        elif requested_is_admin is not None:
            user.is_admin = bool(requested_is_admin)

        requested_is_active = changes.get("is_active")
        if (
            requested_is_active is not None
            and requested_is_active is False
            and user.is_admin
        ):
            if self._active_admins_count() <= 1:
                raise ValidationError(
                    "Dados inválidos.",
                    details={
                        "is_active": "Não é permitido desativar o último administrador ativo."
                    },
                )
            user.is_active = False
        elif requested_is_active is not None:
            user.is_active = bool(requested_is_active)

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
        self,
        user_id: int,
        new_password: str | None = None,
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
