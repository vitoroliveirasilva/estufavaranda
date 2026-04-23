from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class AdminCreateUserInput(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8)
    is_admin: bool = False
    is_active: bool = True


class AdminUpdateUserInput(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    is_admin: bool | None = None
    is_active: bool | None = None


class AdminResetPasswordInput(BaseModel):
    new_password: str | None = Field(default=None, min_length=8)
