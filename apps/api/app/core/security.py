"""Bảo mật, băm mật khẩu Bcrypt và tạo/giải mã JWT Authentication."""

import base64
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

PASSWORD_HASH_PREFIX = "bcrypt-sha256-v1$"


def _password_material(password: str) -> bytes:
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())


def get_password_hash(password: str) -> str:
    """Versioned bcrypt of a base64 SHA-256 digest: all UTF-8 bytes participate."""
    return PASSWORD_HASH_PREFIX + bcrypt.hashpw(_password_material(password), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu plain-text với chuỗi hash bcrypt đã lưu."""
    try:
        if hashed_password.startswith(PASSWORD_HASH_PREFIX):
            plain_bytes = _password_material(plain_password)
            hashed_password = hashed_password[len(PASSWORD_HASH_PREFIX):]
        else:
            plain_bytes = plain_password.encode("utf-8")
            if len(plain_bytes) > 72:
                return False  # Legacy truncated hashes cannot authenticate an unambiguous long secret.
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except (ValueError, TypeError, RuntimeError, AttributeError):
        return False


def create_access_token(
    subject: str | uuid.UUID,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Tạo JWT Access Token ngắn hạn với claim phân biệt type='access'."""
    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        to_encode = {**extra_claims, **to_encode}

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    subject: str | uuid.UUID,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Tạo JWT Refresh Token dài hạn với claim phân biệt type='refresh'."""
    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        to_encode = {**extra_claims, **to_encode}

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Giải mã và xác thực chữ ký JWT token bằng khóa bí mật.

    Ném ra jwt.PyJWTError (hoặc jwt.ExpiredSignatureError, jwt.InvalidTokenError)
    nếu token không hợp lệ hoặc đã hết hạn.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "type", "iat", "exp"]},
    )
