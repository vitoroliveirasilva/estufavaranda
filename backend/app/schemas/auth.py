from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    device_name: str | None = Field(default=None, max_length=120)


class RefreshInput(BaseModel):
    refresh_token: str = Field(min_length=24)


class LogoutInput(BaseModel):
    refresh_token: str = Field(min_length=24)


class ForgotPasswordInput(BaseModel):
    email: EmailStr


class ResetPasswordInput(BaseModel):
    token: str = Field(min_length=24)
    new_password: str = Field(min_length=8)


class DeviceRegisterInput(BaseModel):
    device_name: str | None = Field(default=None, max_length=120)
    platform: str = Field(min_length=2, max_length=30)
    push_token: str | None = Field(default=None, max_length=500)


class UserOutput(ORMModel):
    id: int
    name: str
    email: str
    is_admin: bool
    is_active: bool
