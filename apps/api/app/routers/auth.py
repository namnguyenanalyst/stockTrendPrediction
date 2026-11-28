"""Router Xác thực và Quản lý Phiên Người dùng (/api/v1/auth)."""

import uuid
from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.account_actions import consume_action, issue_action, now_utc, rate_limit, send_limits
from app.core.account_mail import send_account_mail
from app.core.config import settings
from app.core.deps import get_current_active_user, get_db
from app.core.persistence import commit_or_conflict
from app.core.security import (
    PASSWORD_HASH_PREFIX,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.core.sessions import (
    COOKIE_PATH,
    add_refresh_session,
    check_cookie_origin,
    consume_refresh_session,
    set_refresh_cookie,
    token_digest,
)
from app.db.models.account_action import AccountAction
from app.db.models.refresh_session import RefreshSession
from app.db.models.user import User, UserRole
from app.schemas.auth import (
    AccountEmailRequest,
    AccountTokenRequest,
    RefreshRequest,
    ResetPasswordRequest,
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
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Đăng ký tài khoản mới với mật khẩu băm Bcrypt và lưu vào CSDL."""
    email_clean = req.email.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(db, f"register:ip:{client_ip}", 10, 60)

    # Kiểm tra tính duy nhất của email (không phân biệt chữ hoa/thường)
    existing_user_result = await db.execute(
        select(User).where(func.lower(User.email) == email_clean)
    )
    if existing_user_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    await send_limits(db, email_clean, client_ip)
    hashed_pwd = await run_in_threadpool(get_password_hash, req.password)
    user_id = uuid.uuid4()

    new_user = User(
        id=user_id,
        email=email_clean,
        hashed_password=hashed_pwd,
        full_name=req.full_name,
        role=UserRole.TRADER,
        is_active=True,
    )
    db.add(new_user)
    await commit_or_conflict(db, "Email already registered")
    await db.refresh(new_user)

    token = await issue_action(db, new_user, "verify")
    await db.commit()
    background_tasks.add_task(send_account_mail, new_user.email, token, "verify")
    return UserResponse.model_validate(new_user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập cấp Access Token và gán Refresh Token Cookie",
)
async def login(
    req: UserLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Xác thực thông tin đăng nhập, cấp JWT Access Token và thiết lập HTTP-only Refresh Cookie."""
    email_clean = req.email.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    await rate_limit(db, f"login:ip:{client_ip}", 20, 60)
    await rate_limit(db, f"login:acct:{client_ip}:{email_clean}", 10, 60)

    result = await db.execute(
        select(User).where(func.lower(User.email) == email_clean).with_for_update()
    )
    user = result.scalar_one_or_none()

    if not user or not await run_in_threadpool(
        verify_password, req.password, user.hashed_password
    ):
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
        extra_claims={"email": user.email, "role": role_str, "auth_version": user.auth_version},
    )
    refresh_token = create_refresh_token(
        subject=str(user.id), extra_claims={"auth_version": user.auth_version}
    )
    if not user.hashed_password.startswith(PASSWORD_HASH_PREFIX):
        user.hashed_password = await run_in_threadpool(get_password_hash, req.password)
    await db.execute(
        delete(RefreshSession).where(
            RefreshSession.user_id == user.id,
            RefreshSession.expires_at <= datetime.now(timezone.utc),
        )
    )
    add_refresh_session(db, refresh_token, user.id)
    await db.commit()
    set_refresh_cookie(response, refresh_token)

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
    response: Response,
    req: RefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> TokenRefreshResponse:
    """Đọc Refresh Token từ HTTP-only cookie hoặc request body, kiểm tra và cấp mới Access Token."""
    token = None
    if req is not None and req.refresh_token:
        token = req.refresh_token
    elif request.cookies.get("refresh_token"):
        check_cookie_origin(request)
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
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
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

    result = await db.execute(select(User).where(User.id == user_uuid).with_for_update())
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("auth_version", 0) != user.auth_version:
        raise HTTPException(401, "Session revoked")
    await consume_refresh_session(db, token, user.id)
    remaining = datetime.fromtimestamp(payload["exp"], timezone.utc) - datetime.now(timezone.utc)
    rotated = create_refresh_token(
        user.id, expires_delta=remaining, extra_claims={"auth_version": user.auth_version}
    )
    add_refresh_session(db, rotated, user.id)
    await db.commit()
    set_refresh_cookie(response, rotated)

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    new_access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email, "role": role_str, "auth_version": user.auth_version},
    )

    return TokenRefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
    )


@router.post(
    "/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Thu hồi phiên refresh hiện tại"
)
async def logout(
    request: Request, req: RefreshRequest | None = None, db: AsyncSession = Depends(get_db)
) -> Response:
    token = (
        req.refresh_token if req and req.refresh_token else request.cookies.get("refresh_token")
    )
    if not (req and req.refresh_token):
        check_cookie_origin(request)
    if token:
        await db.execute(
            delete(RefreshSession).where(RefreshSession.token_hash == token_digest(token))
        )
        await db.commit()
    response = Response(status_code=204)
    response.delete_cookie(
        "refresh_token",
        path=COOKIE_PATH,
        httponly=True,
        secure=settings.ENVIRONMENT.lower() == "production",
        samesite="lax",
    )
    return response


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


@router.post("/forgot-password", status_code=202)
async def forgot_password(
    req: AccountEmailRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    await send_limits(db, req.email, request.client.host if request.client else "unknown")
    user = (
        await db.execute(select(User).where(User.email == req.email).with_for_update())
    ).scalar_one_or_none()
    if user and user.is_active:
        token = await issue_action(db, user, "reset")
        await db.commit()
        background_tasks.add_task(send_account_mail, user.email, token, "reset")
    return {
        "message": "Nếu email phù hợp với tài khoản đang hoạt động, bạn sẽ nhận được hướng dẫn đặt lại mật khẩu."
    }


@router.post("/resend-verification", status_code=202)
async def resend_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if user.email_verified_at is not None:
        return {"message": "Email đã được xác minh."}
    await send_limits(db, user.email, request.client.host if request.client else "unknown")
    user = (
        await db.execute(
            select(User)
            .where(User.id == user.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    if user.is_active and user.email_verified_at is None:
        token = await issue_action(db, user, "verify")
        await db.commit()
        background_tasks.add_task(send_account_mail, user.email, token, "verify")
    return {"message": "Nếu email chưa xác minh, thư xác minh sẽ được gửi."}


@router.post("/verify-email")
async def verify_email(
    req: AccountTokenRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    await rate_limit(db, f"token:{request.client.host if request.client else 'unknown'}", 30, 60)
    user = await consume_action(db, req.token, "verify")
    user.email_verified_at = now_utc()
    await db.commit()
    return {"message": "Email đã được xác minh."}


@router.post("/reset-password")
async def reset_password(
    req: ResetPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    await rate_limit(db, f"token:{request.client.host if request.client else 'unknown'}", 30, 60)
    user = await consume_action(db, req.token, "reset")
    user.hashed_password = await run_in_threadpool(get_password_hash, req.new_password)
    user.auth_version += 1
    await db.execute(delete(RefreshSession).where(RefreshSession.user_id == user.id))
    await db.execute(
        delete(AccountAction).where(
            AccountAction.user_id == user.id, AccountAction.purpose == "reset"
        )
    )
    await db.commit()
    return {"message": "Đã đặt lại mật khẩu. Vui lòng đăng nhập lại."}
