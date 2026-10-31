"""Automated Unit Tests cho 5 Core SQLAlchemy Models.

Kiểm tra:
1. Khởi tạo CRUD và giá trị mặc định (UUID, role, risk_profile, timestamps).
2. Ràng buộc toàn vẹn Unique (email người dùng).
3. Ràng buộc Foreign Key và Cascade Delete (Watchlists, Presets, Backtests bị xóa khi User bị xóa).
4. Khả năng serialize/deserialize JSONB/JSON (symbols, parameters, equity_curve, predicted_probabilities).
5. Bảng kiểm toán dự báo PredictionAudit và cập nhật độ lệch mô hình.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    BacktestHistory,
    Base,
    PredictionAudit,
    RiskProfile,
    StrategyPreset,
    User,
    UserRole,
    UserWatchlist,
)


def test_all_five_tables_registered_in_base_metadata():
    """Kiểm tra toàn bộ 5 bảng dữ liệu cốt lõi đã được đăng ký đầy đủ vào Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
        "users",
        "user_watchlists",
        "strategy_presets",
        "backtest_histories",
        "prediction_audits",
    }
    assert expected_tables.issubset(table_names), f"Thiếu bảng: {expected_tables - table_names}"


@pytest.mark.asyncio
async def test_create_user_and_default_values(db_session: AsyncSession):
    """Kiểm tra tạo người dùng và các giá trị mặc định chuẩn xác."""
    user = User(
        email="trader_default@vnstock.vn",
        hashed_password="hashed_pw_placeholder",
        full_name="Nguyễn Văn A",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.email == "trader_default@vnstock.vn"
    assert user.role == UserRole.TRADER
    assert user.risk_profile == RiskProfile.BALANCED
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None
    assert "User(id=" in repr(user)


@pytest.mark.asyncio
async def test_user_unique_email_constraint(db_session: AsyncSession):
    """Kiểm tra ràng buộc duy nhất (Unique) trên trường email."""
    user1 = User(
        email="duplicate@vnstock.vn",
        hashed_password="pw1",
    )
    db_session.add(user1)
    await db_session.commit()

    user2 = User(
        email="duplicate@vnstock.vn",
        hashed_password="pw2",
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_user_custom_role_and_risk_profile(db_session: AsyncSession):
    """Kiểm tra gán role admin và khẩu vị rủi ro tùy biến."""
    user = User(
        email="admin@vnstock.vn",
        hashed_password="admin_hashed_pw",
        role=UserRole.ADMIN,
        risk_profile=RiskProfile.AGGRESSIVE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.role == UserRole.ADMIN
    assert user.risk_profile == RiskProfile.AGGRESSIVE


@pytest.mark.asyncio
async def test_watchlist_crud_and_json_symbols(db_session: AsyncSession):
    """Kiểm tra CRUD Watchlist và lưu trữ danh sách mã JSON/JSONB."""
    user = User(email="user_wl@vnstock.vn", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()

    # Create
    symbols_list = ["HPG", "NKG", "HSG"]
    watchlist = UserWatchlist(
        user_id=user.id,
        name="Thép Tiềm Năng",
        symbols=symbols_list,
    )
    db_session.add(watchlist)
    await db_session.commit()
    await db_session.refresh(watchlist)

    assert isinstance(watchlist.id, uuid.UUID)
    assert watchlist.user_id == user.id
    assert watchlist.name == "Thép Tiềm Năng"
    assert watchlist.symbols == symbols_list

    # Update
    watchlist.symbols = ["HPG", "VNM"]
    await db_session.commit()
    await db_session.refresh(watchlist)
    assert watchlist.symbols == ["HPG", "VNM"]


@pytest.mark.asyncio
async def test_watchlist_foreign_key_and_cascade_delete(db_session: AsyncSession):
    """Kiểm tra xóa User sẽ tự động xóa sạch các Watchlists liên quan (CASCADE)."""
    user = User(email="cascade_user@vnstock.vn", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()

    wl1 = UserWatchlist(user_id=user.id, name="WL 1", symbols=["VIC"])
    wl2 = UserWatchlist(user_id=user.id, name="WL 2", symbols=["FPT"])
    db_session.add_all([wl1, wl2])
    await db_session.commit()

    # Xác nhận đã tạo
    result = await db_session.execute(
        select(UserWatchlist).where(UserWatchlist.user_id == user.id)
    )
    assert len(result.scalars().all()) == 2

    # Xóa User
    await db_session.delete(user)
    await db_session.commit()

    # Xác nhận watchlists đã bị cascade delete
    result_after = await db_session.execute(
        select(UserWatchlist).where(UserWatchlist.user_id == user.id)
    )
    assert len(result_after.scalars().all()) == 0


@pytest.mark.asyncio
async def test_strategy_preset_crud_and_parameters(db_session: AsyncSession):
    """Kiểm tra lưu trữ dict tham số chiến lược định lượng trong StrategyPreset."""
    user = User(email="preset_user@vnstock.vn", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()

    params = {
        "stop_loss_pct": 0.05,
        "take_profit_pct": 0.12,
        "trailing_stop_pct": 0.03,
        "rsi_period": 14,
        "lot_size": 100,
    }
    preset = StrategyPreset(
        user_id=user.id,
        name="Chiến lược RSI Breakout T+2",
        description="Chiến lược lướt sóng ngắn hạn theo đà tăng RSI",
        parameters=params,
    )
    db_session.add(preset)
    await db_session.commit()
    await db_session.refresh(preset)

    assert isinstance(preset.id, uuid.UUID)
    assert preset.parameters["stop_loss_pct"] == 0.05
    assert preset.parameters["lot_size"] == 100

    # Cascade delete khi xóa user
    await db_session.delete(user)
    await db_session.commit()

    res = await db_session.execute(select(StrategyPreset).where(StrategyPreset.user_id == user.id))
    assert len(res.scalars().all()) == 0


@pytest.mark.asyncio
async def test_backtest_history_crud_and_metrics(db_session: AsyncSession):
    """Kiểm tra lưu trữ và truy vấn kết quả Backtest cùng đường cong Equity Curve."""
    user = User(email="bt_user@vnstock.vn", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()

    curve_data = [
        {"date": "2024-01-02", "equity": 100_000_000.0, "drawdown": 0.0},
        {"date": "2024-01-03", "equity": 102_500_000.0, "drawdown": 0.0},
        {"date": "2024-01-04", "equity": 101_800_000.0, "drawdown": 0.0068},
    ]

    history = BacktestHistory(
        user_id=user.id,
        symbol="HPG",
        strategy_name="TrendFollowing_LSTM_T2",
        strategy_type="AI_Ensemble",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
        initial_capital=100_000_000.0,
        total_return=0.185,
        sharpe_ratio=1.65,
        max_drawdown=0.082,
        win_rate=0.64,
        equity_curve=curve_data,
    )
    db_session.add(history)
    await db_session.commit()
    await db_session.refresh(history)

    assert isinstance(history.id, uuid.UUID)
    assert history.symbol == "HPG"
    assert history.total_return == 0.185
    assert len(history.equity_curve) == 3
    assert history.equity_curve[1]["equity"] == 102_500_000.0

    # Cascade delete check
    await db_session.delete(user)
    await db_session.commit()

    res = await db_session.execute(
        select(BacktestHistory).where(BacktestHistory.user_id == user.id)
    )
    assert len(res.scalars().all()) == 0


@pytest.mark.asyncio
async def test_prediction_audit_crud_and_signals(db_session: AsyncSession):
    """Kiểm tra lưu trữ nhật ký dự báo AI (PredictionAudit) và cập nhật kết quả thực tế."""
    audit = PredictionAudit(
        symbol="VIC",
        prediction_date=date(2024, 10, 1),
        target_date=date(2024, 10, 4),  # T+3
        predicted_signal=2,  # 2: Tăng
        predicted_probabilities={"down": 0.08, "neutral": 0.17, "up": 0.75},
    )
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    assert isinstance(audit.id, uuid.UUID)
    assert audit.symbol == "VIC"
    assert audit.predicted_signal == 2
    assert audit.predicted_probabilities["up"] == 0.75
    assert audit.actual_return is None
    assert audit.is_correct is None

    # Giả lập đối soát khi đến ngày T+3
    audit.actual_return = 0.042
    audit.is_correct = True
    await db_session.commit()
    await db_session.refresh(audit)

    assert audit.actual_return == 0.042
    assert audit.is_correct is True


@pytest.mark.asyncio
async def test_invalid_foreign_key_raises_error(db_session: AsyncSession):
    """Kiểm tra gán user_id không tồn tại sẽ kích hoạt lỗi ràng buộc Foreign Key."""
    orphan_wl = UserWatchlist(
        user_id=uuid.uuid4(),  # Random ID không có trong bảng users
        name="Orphan Watchlist",
        symbols=["SSI"],
    )
    db_session.add(orphan_wl)
    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()
