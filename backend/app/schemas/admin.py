from __future__ import annotations

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import InputModel, blank_str_to_none, normalize_email_value


class AdminCreateUserInput(InputModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8)
    is_admin: bool = False
    is_active: bool = True

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value):
        return normalize_email_value(value)


class AdminUpdateUserInput(InputModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    is_admin: bool | None = None
    is_active: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _blank_name_to_none(cls, value):
        return blank_str_to_none(value)

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value):
        return normalize_email_value(value)


class AdminResetPasswordInput(InputModel):
    new_password: str | None = Field(default=None, min_length=8)

    @field_validator("new_password", mode="before")
    @classmethod
    def _blank_password_to_none(cls, value):
        return blank_str_to_none(value)
