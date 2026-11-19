"""Pydantic V2 Schemas cho xác thực và quản lý phiên (Authentication)."""

import re

from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserResponse

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserRegisterRequest(BaseModel):
    """Payload đăng ký tài khoản người dùng mới."""

    email: str = Field(max_length=255)
    password: str = Field(..., min_length=8, max_length=1024, description="Mật khẩu từ 8 đến 1024 ký tự")
    full_name: str | None = Field(default=None, max_length=255)
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format")
        return cleaned


class UserLoginRequest(BaseModel):
    """Payload đăng nhập tài khoản."""

    email: str = Field(max_length=255)
    password: str = Field(max_length=1024)


class RefreshRequest(BaseModel):
    """Payload cấp mới access token từ refresh token."""

    refresh_token: str | None = Field(default=None, max_length=4096)


class TokenResponse(BaseModel):
    """Kết quả đăng nhập thành công chứa access token và thông tin người dùng."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse | None = None


class TokenRefreshResponse(BaseModel):
    """Kết quả cấp mới access token."""

    access_token: str
    token_type: str = "bearer"


class AccountEmailRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_REGEX.fullmatch(value):
            raise ValueError("Invalid email format")
        return value


class AccountTokenRequest(BaseModel):
    token: str = Field(min_length=1, max_length=256)


class ResetPasswordRequest(AccountTokenRequest):
    new_password: str = Field(min_length=8, max_length=1024)
