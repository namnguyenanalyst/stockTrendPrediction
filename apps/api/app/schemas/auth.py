"""Pydantic V2 Schemas cho xác thực và quản lý phiên (Authentication)."""

import re

from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserResponse

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserRegisterRequest(BaseModel):
    """Payload đăng ký tài khoản người dùng mới."""

    email: str
    password: str = Field(..., min_length=8, description="Mật khẩu tối thiểu 8 ký tự")
    full_name: str | None = None
    risk_profile: str | None = Field(
        default="balanced", description="conservative | balanced | aggressive"
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format")
        return cleaned

    @field_validator("risk_profile")
    @classmethod
    def validate_risk_profile(cls, v: str | None) -> str:
        if v is None:
            return "balanced"
        cleaned = v.strip().lower()
        if cleaned not in ("conservative", "balanced", "aggressive"):
            raise ValueError(
                "Invalid risk profile. Must be one of: conservative, balanced, aggressive"
            )
        return cleaned


class UserLoginRequest(BaseModel):
    """Payload đăng nhập tài khoản."""

    email: str
    password: str


class RefreshRequest(BaseModel):
    """Payload cấp mới access token từ refresh token."""

    refresh_token: str | None = None


class TokenResponse(BaseModel):
    """Kết quả đăng nhập thành công chứa access token và thông tin người dùng."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse | None = None


class TokenRefreshResponse(BaseModel):
    """Kết quả cấp mới access token."""

    access_token: str
    token_type: str = "bearer"
