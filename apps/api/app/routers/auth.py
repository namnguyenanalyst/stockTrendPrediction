"""Router Xác thực và Quản lý Phiên Người dùng (/api/v1/auth)."""

import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_active_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.models.user import RiskProfile, User, UserRole
from app.schemas.auth import (
    RefreshRequest,
    TokenRefreshResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.user import UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản người dùng mới",
)
async def register(
    req: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Đăng ký tài khoản mới với mật khẩu băm Bcrypt và lưu vào CSDL."""
    email_clean = req.email.strip().lower()

    # Kiểm tra tính duy nhất của email (không phân biệt chữ hoa/thường)
    existing_user_result = await db.execute(
        select(User).where(func.lower(User.email) == email_clean)
    )
    if existing_user_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Chuyển đổi khẩu vị rủi ro sang enum
    profile_str = (req.risk_profile or "balanced").strip().lower()
    try:
        risk_enum = RiskProfile(profile_str)
    except ValueError:
        risk_enum = RiskProfile.BALANCED

    hashed_pwd = get_password_hash(req.password)
    user_id = uuid.uuid4()

    new_user = User(
        id=user_id,
        email=email_clean,
        hashed_password=hashed_pwd,
        full_name=req.full_name,
        role=UserRole.TRADER,
        risk_profile=risk_enum,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse.model_validate(new_user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập cấp Access Token và gán Refresh Token Cookie",
)
async def login(
    req: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Xác thực thông tin đăng nhập, cấp JWT Access Token và thiết lập HTTP-only Refresh Cookie."""
    email_clean = req.email.strip().lower()

    result = await db.execute(select(User).where(func.lower(User.email) == email_clean))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email, "role": role_str},
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    # Gán Refresh Token vào HTTP-only cookie bảo mật
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        path="/api/v1/auth",
        samesite="lax",
        max_age=86400 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Cấp mới Access Token từ Refresh Token",
)
async def refresh_token_endpoint(
    request: Request,
    req: RefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> TokenRefreshResponse:
    """Đọc Refresh Token từ HTTP-only cookie hoặc request body, kiểm tra và cấp mới Access Token."""
    token = None
    if req is not None and req.refresh_token:
        token = req.refresh_token
    elif request.cookies.get("refresh_token"):
        token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired refresh token: {exc!s}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(str(user_id_str))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    new_access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email, "role": role_str},
    )

    return TokenRefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy thông tin tài khoản người dùng hiện tại",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Trả về thông tin hồ sơ của người dùng đang đăng nhập."""
    return UserResponse.model_validate(current_user)
