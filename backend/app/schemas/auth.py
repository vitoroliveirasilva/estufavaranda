from __future__ import annotations

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import (
    InputModel,
    ORMModel,
    blank_str_to_none,
    normalize_email_value,
)


class LoginInput(InputModel):
    email: EmailStr
    password: str = Field(min_length=1)
    device_name: str | None = Field(default=None, max_length=120)

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value):
        return normalize_email_value(value)

    @field_validator("device_name", mode="before")
    @classmethod
    def _blank_device_name_to_none(cls, value):
        return blank_str_to_none(value)


class RefreshInput(InputModel):
    refresh_token: str = Field(min_length=24)

    @field_validator("refresh_token", mode="before")
    @classmethod
    def _normalize_refresh_token(cls, value):
        normalized = blank_str_to_none(value)
        if normalized is None:
            raise ValueError("refresh_token é obrigatório.")
        return normalized


class LogoutInput(InputModel):
    refresh_token: str = Field(min_length=24)

    @field_validator("refresh_token", mode="before")
    @classmethod
    def _normalize_refresh_token(cls, value):
        normalized = blank_str_to_none(value)
        if normalized is None:
            raise ValueError("refresh_token é obrigatório.")
        return normalized


class ForgotPasswordInput(InputModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value):
        return normalize_email_value(value)


class ResetPasswordInput(InputModel):
    token: str = Field(min_length=24)
    new_password: str = Field(min_length=8)

    @field_validator("token", mode="before")
    @classmethod
    def _normalize_reset_token(cls, value):
        normalized = blank_str_to_none(value)
        if normalized is None:
            raise ValueError("token é obrigatório.")
        return normalized


class DeviceRegisterInput(InputModel):
    device_name: str | None = Field(default=None, max_length=120)
    platform: str = Field(min_length=2, max_length=30)
    push_token: str | None = Field(default=None, max_length=500)

    @field_validator("device_name", "push_token", mode="before")
    @classmethod
    def _blank_optional_strings_to_none(cls, value):
        return blank_str_to_none(value)

    @field_validator("platform")
    @classmethod
    def _normalize_platform(cls, value: str) -> str:
        return value.strip().lower()


class UserOutput(ORMModel):
    id: int
    name: str
    email: str
    is_admin: bool
    is_active: bool
