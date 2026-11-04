"""Router quản trị hệ thống (/api/v1/admin) dành cho vai trò ADMIN.

Nguyên tắc bảo mật:
- Yêu cầu quyền ADMIN (TRADER bị từ chối với HTTP 403 Forbidden).
- Thống kê tổng hợp số lượng tài khoản (PoLP: không trả bất kỳ thông tin cá nhân hay chiến lược nào).
- Tính toán mốc thời gian theo múi giờ Việt Nam (UTC+7, 0h00 ICT).
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user, get_db
from app.db.models.user import User

router = APIRouter(tags=["Admin"])

VN_TZ = timezone(timedelta(hours=7))


class AdminStatsResponse(BaseModel):
    total_users: int
    new_users_today: int
    new_users_7d: int
    new_users_30d: int
    online_users: int


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

    # Mốc 0h00 hôm nay theo giờ Việt Nam (UTC+7)
    today_vn_midnight = now_vn.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight_utc = today_vn_midnight.astimezone(timezone.utc)

    # Mốc 7 ngày và 30 ngày trước theo giờ Việt Nam
    seven_days_utc = (today_vn_midnight - timedelta(days=7)).astimezone(timezone.utc)
    thirty_days_utc = (today_vn_midnight - timedelta(days=30)).astimezone(timezone.utc)

    # Cửa sổ Online: hoạt động trong 5 phút gần nhất
    online_cutoff_utc = now_utc - timedelta(minutes=5)

    # Tổng số người dùng
    total_res = await db.execute(select(func.count(User.id)))
    total_users = total_res.scalar() or 0

    # Người dùng mới hôm nay
    today_res = await db.execute(
        select(func.count(User.id)).where(User.created_at >= midnight_utc)
    )
    new_users_today = today_res.scalar() or 0

    # Người dùng mới trong 7 ngày
    seven_days_res = await db.execute(
        select(func.count(User.id)).where(User.created_at >= seven_days_utc)
    )
    new_users_7d = seven_days_res.scalar() or 0

    # Người dùng mới trong 30 ngày
    thirty_days_res = await db.execute(
        select(func.count(User.id)).where(User.created_at >= thirty_days_utc)
    )
    new_users_30d = thirty_days_res.scalar() or 0

    # Người dùng đang online (last_seen_at trong 5 phút qua)
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
