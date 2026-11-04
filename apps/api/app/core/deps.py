"""FastAPI dependencies cho xác thực người dùng và kết nối CSDL."""

import hmac
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.models.user import User, UserRole
from app.db.session import get_db

__all__ = [
    "get_current_active_user",
    "get_current_admin_user",
    "get_current_user",
    "get_db",
    "verify_internal_worker_secret",
]


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Trích xuất và xác thực Bearer token từ Authorization header.

    Giải mã claim JWT, tìm kiếm người dùng trong CSDL và trả về đối tượng User.
    Ném ra HTTP 401 Unauthorized nếu token thiếu, sai định dạng, hết hạn hoặc không tìm thấy user.
    """
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc!s}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Đảm bảo token được cung cấp là Access Token chứ không phải Refresh Token
    token_type = payload.get("type")
    if token_type and token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(str(user_id_str))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier format in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Cập nhật có điều kiện last_seen_at ở tầng CSDL (throttle tối đa 1 lần/phút/user)
    # Không dùng biến bộ nhớ tiến trình, điều kiện WHERE giải quyết hoàn toàn tại CSDL
    now_utc = datetime.now(timezone.utc)
    cutoff_60s = now_utc - timedelta(seconds=60)
    await db.execute(
        update(User)
        .where(
            User.id == user.id,
            or_(
                User.last_seen_at.is_(None),
                User.last_seen_at < cutoff_60s,
            ),
        )
        .values(last_seen_at=func.now())
        .execution_options(synchronize_session=False)
    )
    await db.commit()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Xác thực người dùng hiện tại đang trong trạng thái hoạt động (is_active)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Xác thực người dùng hiện tại có vai trò ADMIN."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin role required",
        )
    return current_user


async def verify_internal_worker_secret(
    x_internal_worker_secret: str | None = Header(None, alias="X-Internal-Worker-Secret"),
) -> None:
    """Xác thực secret nội bộ cho các tác vụ worker tự trị (fail-closed)."""
    expected = settings.INTERNAL_WORKER_SECRET
    if not expected or not x_internal_worker_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or missing internal worker secret",
        )
    if not hmac.compare_digest(x_internal_worker_secret.strip(), expected.strip()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or missing internal worker secret",
        )
