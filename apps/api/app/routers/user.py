"""Router Cá nhân hóa và Quản lý Danh mục Người dùng (/api/v1/user).

Bao gồm:
- /watchlists: CRUD danh mục cổ phiếu ghim theo dõi
- /presets: CRUD mẫu tham số chiến lược đầu tư
- /backtests: Lưu và truy vấn nhật ký kiểm thử chiến lược định lượng
Đảm bảo 100% phân tách đa người dùng (Multi-Tenant Isolation) theo current_user.id.
Mọi truy cập tài nguyên của người dùng khác hoặc ID không tồn tại đều trả về HTTP 404.
"""

import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.db.models.backtest import BacktestHistory
from app.db.models.preset import StrategyPreset
from app.db.models.user import User
from app.db.models.watchlist import UserWatchlist
from app.schemas.backtest import (
    BacktestHistoryCreateRequest,
    BacktestHistoryResponse,
)
from app.schemas.preset import (
    PresetCreateRequest,
    PresetResponse,
)
from app.schemas.watchlist import (
    WatchlistCreateRequest,
    WatchlistResponse,
)

router = APIRouter()


# =============================================================================
# 1. Danh mục theo dõi (Watchlists)
# =============================================================================


@router.get(
    "/watchlists",
    response_model=list[WatchlistResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách các danh mục theo dõi của người dùng hiện tại",
)
async def list_watchlists(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[WatchlistResponse]:
    """Truy vấn các watchlist gắn chặt với current_user.id."""
    result = await db.execute(
        select(UserWatchlist)
        .where(UserWatchlist.user_id == current_user.id)
        .order_by(UserWatchlist.created_at.desc())
    )
    items = result.scalars().all()
    return [WatchlistResponse.model_validate(w) for w in items]


@router.post(
    "/watchlists",
    response_model=WatchlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo danh mục theo dõi mới",
)
async def create_watchlist(
    req: WatchlistCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> WatchlistResponse:
    """Tạo mới watchlist cho người dùng hiện tại."""
    item = UserWatchlist(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=req.name,
        symbols=req.symbols,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return WatchlistResponse.model_validate(item)


@router.delete(
    "/watchlists/{watchlist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa danh mục theo dõi",
)
async def delete_watchlist(
    watchlist_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Xóa watchlist theo ID. Ngăn chặn IDOR: trả về 404 nếu không tìm thấy hoặc thuộc tài khoản khác."""
    try:
        wid = uuid.UUID(watchlist_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )

    result = await db.execute(select(UserWatchlist).where(UserWatchlist.id == wid))
    item = result.scalar_one_or_none()

    if not item or item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )

    await db.delete(item)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# 2. Mẫu tham số chiến lược (Strategy Presets)
# =============================================================================


@router.get(
    "/presets",
    response_model=list[PresetResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách các mẫu tham số chiến lược của người dùng",
)
async def list_presets(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PresetResponse]:
    """Truy vấn các preset gắn chặt với current_user.id."""
    result = await db.execute(
        select(StrategyPreset)
        .where(StrategyPreset.user_id == current_user.id)
        .order_by(StrategyPreset.created_at.desc())
    )
    items = result.scalars().all()
    return [PresetResponse.model_validate(p) for p in items]


@router.post(
    "/presets",
    response_model=PresetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lưu mẫu tham số chiến lược mới",
)
async def create_preset(
    req: PresetCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PresetResponse:
    """Lưu mẫu chiến lược tùy chỉnh cho người dùng hiện tại."""
    item = StrategyPreset(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=req.name,
        description=req.description,
        parameters=req.parameters,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return PresetResponse.model_validate(item)


@router.delete(
    "/presets/{preset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa mẫu tham số chiến lược",
)
async def delete_preset(
    preset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Xóa preset theo ID. Ngăn chặn IDOR: trả về 404 nếu không tìm thấy hoặc thuộc tài khoản khác."""
    try:
        pid = uuid.UUID(preset_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy preset not found",
        )

    result = await db.execute(select(StrategyPreset).where(StrategyPreset.id == pid))
    item = result.scalar_one_or_none()

    if not item or item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy preset not found",
        )

    await db.delete(item)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# 3. Nhật ký kiểm thử chiến lược (Backtest Histories)
# =============================================================================


@router.get(
    "/backtests",
    response_model=list[BacktestHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách nhật ký kiểm thử chiến lược của người dùng",
)
async def list_backtests(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[BacktestHistoryResponse]:
    """Truy vấn các kết quả backtest của current_user.id, sắp xếp mới nhất lên đầu."""
    result = await db.execute(
        select(BacktestHistory)
        .where(BacktestHistory.user_id == current_user.id)
        .order_by(BacktestHistory.executed_at.desc())
    )
    items = result.scalars().all()
    return [BacktestHistoryResponse.model_validate(b) for b in items]


@router.post(
    "/backtests",
    response_model=BacktestHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lưu kết quả kiểm thử chiến lược vào tài khoản",
)
async def save_backtest(
    req: BacktestHistoryCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BacktestHistoryResponse:
    """Lưu trữ kết quả backtest bao gồm các chỉ số tài chính và đường cong Equity Curve."""
    # Chuyển đổi start_date và end_date sang kiểu datetime.date nếu nhận dạng chuỗi
    if isinstance(req.start_date, date):
        start_d = req.start_date
    else:
        try:
            start_d = datetime.strptime(str(req.start_date).strip(), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_date must be a valid date in YYYY-MM-DD format",
            )

    if isinstance(req.end_date, date):
        end_d = req.end_date
    else:
        try:
            end_d = datetime.strptime(str(req.end_date).strip(), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="end_date must be a valid date in YYYY-MM-DD format",
            )

    item = BacktestHistory(
        id=uuid.uuid4(),
        user_id=current_user.id,
        symbol=req.symbol,
        strategy_name=req.strategy_name,
        strategy_type=req.strategy_type,
        start_date=start_d,
        end_date=end_d,
        initial_capital=req.initial_capital,
        total_return=req.total_return,
        sharpe_ratio=req.sharpe_ratio,
        max_drawdown=req.max_drawdown,
        win_rate=req.win_rate,
        equity_curve=req.equity_curve,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return BacktestHistoryResponse.model_validate(item)
