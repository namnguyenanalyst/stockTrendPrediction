"""Router quản trị hệ thống (/api/v1/admin) dành cho vai trò ADMIN.

Nguyên tắc bảo mật:
- Yêu cầu quyền ADMIN (TRADER bị từ chối với HTTP 403 Forbidden).
- Quản lý danh sách người dùng (tìm kiếm, phân quyền, khóa/mở khóa tài khoản).
- Bảo vệ tài khoản quản trị: Chặn Admin tự khóa hoặc tự hạ quyền của chính mình.
- Nhật ký hoạt động & kiểm toán hệ thống (Activity stream & Prediction audit).
- Tính toán mốc thời gian theo múi giờ Việt Nam (UTC+7, 0h00 ICT).
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user, get_db
from app.db.models.audit import PredictionAudit
from app.db.models.backtest import BacktestHistory
from app.db.models.user import RiskProfile, User, UserRole

router = APIRouter(tags=["Admin"])

VN_TZ = timezone(timedelta(hours=7))


# --- Schemas ---

class AdminStatsResponse(BaseModel):
    total_users: int
    new_users_today: int
    new_users_7d: int
    new_users_30d: int
    online_users: int


class AdminUserItem(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None = None
    role: UserRole
    risk_profile: RiskProfile
    is_active: bool
    created_at: datetime
    last_seen_at: datetime | None = None
    total_backtests: int = 0

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    items: list[AdminUserItem]
    total: int
    page: int
    page_size: int


class AdminUpdateUserRequest(BaseModel):
    is_active: bool | None = None
    role: UserRole | None = None


class AdminActivityItem(BaseModel):
    id: str
    timestamp: datetime
    event_type: str  # "backtest" | "ai_audit" | "user_registration"
    title: str
    description: str
    actor: str | None = None
    status: str  # "success" | "warning" | "info"
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdminActivityResponse(BaseModel):
    items: list[AdminActivityItem]


# --- Endpoints ---

@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Thống kê tổng hợp người dùng cho Quản trị viên (Admin)",
    description="Trả về 5 chỉ số tổng hợp người dùng. Mốc thời gian 'hôm nay', '7 ngày', '30 ngày' tính theo 0h00 UTC+7.",
)
async def get_admin_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminStatsResponse:
    """Truy vấn các chỉ số thống kê tổng hợp người dùng cho Admin."""
    now_utc = datetime.now(timezone.utc)
    now_vn = now_utc.astimezone(VN_TZ)

    today_vn_midnight = now_vn.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = today_vn_midnight.astimezone(timezone.utc)

    seven_days_utc = (today_vn_midnight - timedelta(days=7)).astimezone(timezone.utc)
    thirty_days_utc = (today_vn_midnight - timedelta(days=30)).astimezone(timezone.utc)

    online_cutoff_utc = now_utc - timedelta(minutes=5)

    total_res = await db.execute(select(func.count(User.id)))
    total_users = total_res.scalar() or 0

    today_res = await db.execute(
        select(func.count(User.id)).where(User.created_at >= midnight_utc)
    )
    new_users_today = today_res.scalar() or 0

    seven_days_res = await db.execute(
        select(func.count(User.id)).where(User.created_at >= seven_days_utc)
    )
    new_users_7d = seven_days_res.scalar() or 0

    thirty_days_res = await db.execute(
        select(func.count(User.id)).where(User.created_at >= thirty_days_utc)
    )
    new_users_30d = thirty_days_res.scalar() or 0

    online_res = await db.execute(
        select(func.count(User.id)).where(User.last_seen_at >= online_cutoff_utc)
    )
    online_users = online_res.scalar() or 0

    return AdminStatsResponse(
        total_users=total_users,
        new_users_today=new_users_today,
        new_users_7d=new_users_7d,
        new_users_30d=new_users_30d,
        online_users=online_users,
    )


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    status_code=status.HTTP_200_OK,
    summary="Danh sách người dùng cho Quản trị viên kèm tìm kiếm và phân trang",
)
async def list_admin_users(
    search: str | None = Query(None, description="Tìm kiếm theo email hoặc họ tên"),
    role: UserRole | None = Query(None, description="Lọc theo vai trò"),
    is_active: bool | None = Query(None, description="Lọc theo trạng thái hoạt động"),
    page: int = Query(1, ge=1, description="Số trang (bắt đầu từ 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserListResponse:
    """Liệt kê danh sách người dùng với tổng số lượt backtest của mỗi người."""
    query = select(User)

    if search:
        search_filter = f"%{search.strip()}%"
        query = query.where(
            or_(
                User.email.ilike(search_filter),
                User.full_name.ilike(search_filter),
            )
        )

    if role is not None:
        query = query.where(User.role == role)

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Đếm tổng số lượng bản ghi thỏa mãn điều kiện
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    # Phân trang & Sắp xếp theo ngày tạo mới nhất
    offset = (page - 1) * page_size
    query = query.order_by(desc(User.created_at)).offset(offset).limit(page_size)
    users_res = await db.execute(query)
    users = users_res.scalars().all()

    # Truy vấn số lượng backtest cho từng user
    user_ids = [u.id for u in users]
    backtest_counts: dict[uuid.UUID, int] = {}
    if user_ids:
        bt_res = await db.execute(
            select(BacktestHistory.user_id, func.count(BacktestHistory.id))
            .where(BacktestHistory.user_id.in_(user_ids))
            .group_by(BacktestHistory.user_id)
        )
        for uid, count in bt_res.all():
            backtest_counts[uid] = count

    items = [
        AdminUserItem(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            risk_profile=u.risk_profile,
            is_active=u.is_active,
            created_at=u.created_at,
            last_seen_at=u.last_seen_at,
            total_backtests=backtest_counts.get(u.id, 0),
        )
        for u in users
    ]

    return AdminUserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserItem,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật trạng thái hoặc vai trò người dùng",
)
async def update_admin_user(
    user_id: uuid.UUID,
    payload: AdminUpdateUserRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminUserItem:
    """Cập nhật quyền hạn (role) hoặc trạng thái khóa/mở khóa (is_active) của người dùng."""
    user_res = await db.execute(select(User).where(User.id == user_id))
    target_user = user_res.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy người dùng với ID '{user_id}'.",
        )

    # Chặn Admin tự khóa tài khoản của chính mình
    if target_user.id == current_admin.id:
        if payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn không thể tự khóa tài khoản quản trị của chính mình.",
            )
        if payload.role is not None and payload.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn không thể tự hạ quyền quản trị viên của chính mình.",
            )

    if payload.is_active is not None:
        target_user.is_active = payload.is_active

    if payload.role is not None:
        target_user.role = payload.role

    await db.commit()
    await db.refresh(target_user)

    bt_count_res = await db.execute(
        select(func.count(BacktestHistory.id)).where(BacktestHistory.user_id == target_user.id)
    )
    total_bt = bt_count_res.scalar() or 0

    return AdminUserItem(
        id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=target_user.role,
        risk_profile=target_user.risk_profile,
        is_active=target_user.is_active,
        created_at=target_user.created_at,
        last_seen_at=target_user.last_seen_at,
        total_backtests=total_bt,
    )


@router.get(
    "/activity-logs",
    response_model=AdminActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Nhật ký hoạt động và kiểm toán hệ thống",
)
async def get_admin_activity_logs(
    limit: int = Query(25, ge=5, le=100, description="Số lượng bản ghi log cần lấy"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminActivityResponse:
    """Tổng hợp nhật ký từ các lần chạy backtest của người dùng và kiểm toán dự báo AI."""
    activities: list[AdminActivityItem] = []

    # 1. Lấy các lượt backtest gần nhất từ người dùng kèm thông tin email
    bt_res = await db.execute(
        select(BacktestHistory, User.email)
        .join(User, BacktestHistory.user_id == User.id)
        .order_by(desc(BacktestHistory.executed_at))
        .limit(limit)
    )
    for bt, user_email in bt_res.all():
        activities.append(
            AdminActivityItem(
                id=f"bt_{bt.id}",
                timestamp=bt.executed_at,
                event_type="backtest",
                title=f"Khởi chạy Backtest {bt.symbol}",
                description=f"Chiến lược '{bt.strategy_name}' ({bt.strategy_type}) từ {bt.start_date} đến {bt.end_date}",
                actor=user_email,
                status="success" if (bt.total_return is not None and bt.total_return >= 0) else "warning",
                metadata={
                    "symbol": bt.symbol,
                    "total_return": bt.total_return,
                    "sharpe_ratio": bt.sharpe_ratio,
                    "win_rate": bt.win_rate,
                },
            )
        )

    # 2. Lấy các lượt kiểm toán dự báo AI gần nhất
    ai_res = await db.execute(
        select(PredictionAudit)
        .order_by(desc(PredictionAudit.created_at))
        .limit(limit)
    )
    signals_map = {0: "GIẢM", 1: "ĐI NGANG", 2: "TĂNG"}
    for audit in ai_res.scalars().all():
        signal_text = signals_map.get(audit.predicted_signal, "KHÔNG XÁC ĐỊNH")
        status_tag = "info"
        if audit.is_correct is True:
            status_tag = "success"
        elif audit.is_correct is False:
            status_tag = "warning"

        activities.append(
            AdminActivityItem(
                id=f"ai_{audit.id}",
                timestamp=audit.created_at,
                event_type="ai_audit",
                title=f"Kiểm toán Dự báo AI {audit.symbol}",
                description=f"Dự báo nhãn {signal_text} cho ngày mục tiêu {audit.target_date}",
                actor="AI Model Engine",
                status=status_tag,
                metadata={
                    "symbol": audit.symbol,
                    "prediction_date": str(audit.prediction_date),
                    "target_date": str(audit.target_date),
                    "predicted_signal": audit.predicted_signal,
                    "is_correct": audit.is_correct,
                },
            )
        )

    # 3. Lấy các tài khoản người dùng đăng ký mới gần đây
    users_res = await db.execute(
        select(User).order_by(desc(User.created_at)).limit(limit)
    )
    for u in users_res.scalars().all():
        activities.append(
            AdminActivityItem(
                id=f"usr_{u.id}",
                timestamp=u.created_at,
                event_type="user_registration",
                title="Người dùng mới tham gia",
                description=f"Tài khoản {u.email} đã đăng ký vào hệ thống",
                actor=u.email,
                status="info" if u.is_active else "warning",
                metadata={"role": u.role, "risk_profile": u.risk_profile},
            )
        )

    # Sắp xếp hợp nhất tất cả sự kiện theo thời gian giảm dần
    activities.sort(key=lambda x: x.timestamp, reverse=True)

    return AdminActivityResponse(items=activities[:limit])
