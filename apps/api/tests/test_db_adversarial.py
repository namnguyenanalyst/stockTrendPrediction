"""Adversarial Stress Test Suite for Milestone 1 Database Models & Engine.

Empirical verification covering:
1. Unique email conflict & null constraints
2. Foreign key violation attempts on all child tables
3. Deep cascade delete stress test & cross-tenant isolation
4. Deterministic UUID primary key collision
5. Large JSONB payload handling (10,000 equity curve points, complex nested dicts, 1,000 symbols)
6. High async session concurrency & error isolation during rollbacks
"""

import asyncio
import uuid
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.db.models import (
    BacktestHistory,
    PredictionAudit,
    StrategyPreset,
    User,
    UserWatchlist,
)


@pytest.mark.asyncio
async def test_adversarial_duplicate_email_conflict(db_session: AsyncSession):
    """Stress Test: Inserting duplicate email must immediately fail with IntegrityError."""
    target_email = "conflict_target@vnstock.vn"
    u1 = User(email=target_email, hashed_password="pw1", full_name="User 1")
    db_session.add(u1)
    await db_session.commit()

    u2 = User(email=target_email, hashed_password="pw2", full_name="User 2")
    db_session.add(u2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_adversarial_null_constraints_on_required_fields(db_session: AsyncSession):
    """Stress Test: Null values on non-nullable fields must trigger IntegrityError."""
    # 1. User without email
    u_no_email = User(email=None, hashed_password="pw")  # type: ignore[arg-type]
    db_session.add(u_no_email)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # 2. User without hashed_password
    u_no_pw = User(email="no_pw@vnstock.vn", hashed_password=None)  # type: ignore[arg-type]
    db_session.add(u_no_pw)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # Valid user for FK testing
    user = User(email="valid_parent@vnstock.vn", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()
    parent_id = user.id

    # 3. Watchlist without name
    wl_no_name = UserWatchlist(user_id=parent_id, name=None, symbols=["HPG"])  # type: ignore[arg-type]
    db_session.add(wl_no_name)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # 4. StrategyPreset with SQL null() parameters (non-nullable JSON column)
    from sqlalchemy import null
    preset_no_params = StrategyPreset(user_id=parent_id, name="Test", parameters=null())
    db_session.add(preset_no_params)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # 4b. StrategyPreset without user_id (non-nullable foreign key)
    preset_no_user = StrategyPreset(user_id=None, name="No User", parameters={"a": 1})  # type: ignore[arg-type]
    db_session.add(preset_no_user)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # 5. PredictionAudit without prediction_date
    audit_no_date = PredictionAudit(
        symbol="SSI",
        prediction_date=None,  # type: ignore[arg-type]
        target_date=date(2024, 1, 4),
        predicted_signal=1,
        predicted_probabilities={"neutral": 1.0},
    )
    db_session.add(audit_no_date)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_adversarial_foreign_key_violations_all_tables(db_session: AsyncSession):
    """Stress Test: Foreign key constraints on UserWatchlist, StrategyPreset, and BacktestHistory."""
    fake_user_id = uuid.uuid4()

    # 1. Watchlist with fake user_id
    orphan_wl = UserWatchlist(user_id=fake_user_id, name="Fake User WL", symbols=["VIC"])
    db_session.add(orphan_wl)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # 2. Preset with fake user_id
    orphan_preset = StrategyPreset(
        user_id=fake_user_id,
        name="Fake User Preset",
        parameters={"stop_loss": 0.05},
    )
    db_session.add(orphan_preset)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # 3. BacktestHistory with fake user_id
    orphan_bt = BacktestHistory(
        user_id=fake_user_id,
        symbol="VNM",
        strategy_name="TrendFollowing",
        strategy_type="RuleBased",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 1),
        initial_capital=100_000_000.0,
        total_return=0.10,
        sharpe_ratio=1.2,
        max_drawdown=0.05,
        win_rate=0.6,
        equity_curve=[{"date": "2024-01-01", "equity": 100_000_000.0}],
    )
    db_session.add(orphan_bt)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_adversarial_cascade_delete_and_tenant_isolation(db_session: AsyncSession):
    """Stress Test: Deleting User A cascades to all its children, while User B remains untouched."""
    # Create User A and User B
    user_a = User(email="tenant_a@vnstock.vn", hashed_password="pw_a", full_name="Tenant A")
    user_b = User(email="tenant_b@vnstock.vn", hashed_password="pw_b", full_name="Tenant B")
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    # Populate User A: 5 watchlists, 5 presets, 5 backtest histories
    watchlists_a = [
        UserWatchlist(user_id=user_a.id, name=f"A_WL_{i}", symbols=[f"SYM{i}"]) for i in range(5)
    ]
    presets_a = [
        StrategyPreset(user_id=user_a.id, name=f"A_Preset_{i}", parameters={"param": i})
        for i in range(5)
    ]
    backtests_a = [
        BacktestHistory(
            user_id=user_a.id,
            symbol="HPG",
            strategy_name=f"Strat_A_{i}",
            strategy_type="AI",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 1),
            initial_capital=100_000_000.0,
            total_return=0.05 * i,
            sharpe_ratio=1.0,
            max_drawdown=0.04,
            win_rate=0.55,
            equity_curve=[{"date": "2024-01-01", "equity": 100_000_000.0}],
        )
        for i in range(5)
    ]
    db_session.add_all(watchlists_a + presets_a + backtests_a)

    # Populate User B: 3 watchlists, 3 presets, 3 backtest histories
    watchlists_b = [
        UserWatchlist(user_id=user_b.id, name=f"B_WL_{i}", symbols=[f"SYM{i}"]) for i in range(3)
    ]
    presets_b = [
        StrategyPreset(user_id=user_b.id, name=f"B_Preset_{i}", parameters={"param": i})
        for i in range(3)
    ]
    backtests_b = [
        BacktestHistory(
            user_id=user_b.id,
            symbol="FPT",
            strategy_name=f"Strat_B_{i}",
            strategy_type="AI",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 1),
            initial_capital=50_000_000.0,
            total_return=0.12 * i,
            sharpe_ratio=1.8,
            max_drawdown=0.03,
            win_rate=0.70,
            equity_curve=[{"date": "2024-01-01", "equity": 50_000_000.0}],
        )
        for i in range(3)
    ]
    db_session.add_all(watchlists_b + presets_b + backtests_b)

    # Create unassociated system audit record
    audit_record = PredictionAudit(
        symbol="VNINDEX",
        prediction_date=date(2024, 5, 1),
        target_date=date(2024, 5, 4),
        predicted_signal=2,
        predicted_probabilities={"down": 0.1, "neutral": 0.2, "up": 0.7},
    )
    db_session.add(audit_record)
    await db_session.commit()

    # Pre-condition check: verify counts
    res_a_wl = (
        await db_session.execute(
            select(UserWatchlist).where(UserWatchlist.user_id == user_a.id)
        )
    ).scalars().all()
    assert len(res_a_wl) == 5

    res_b_wl = (
        await db_session.execute(
            select(UserWatchlist).where(UserWatchlist.user_id == user_b.id)
        )
    ).scalars().all()
    assert len(res_b_wl) == 3

    # Action: Delete User A
    await db_session.delete(user_a)
    await db_session.commit()

    # Post-condition 1: User A's records must be completely purged
    post_a_wl = (
        await db_session.execute(
            select(UserWatchlist).where(UserWatchlist.user_id == user_a.id)
        )
    ).scalars().all()
    post_a_presets = (
        await db_session.execute(
            select(StrategyPreset).where(StrategyPreset.user_id == user_a.id)
        )
    ).scalars().all()
    post_a_bt = (
        await db_session.execute(
            select(BacktestHistory).where(BacktestHistory.user_id == user_a.id)
        )
    ).scalars().all()
    assert len(post_a_wl) == 0
    assert len(post_a_presets) == 0
    assert len(post_a_bt) == 0

    # Post-condition 2: User B's records must be 100% intact
    post_b_user = await db_session.get(User, user_b.id)
    assert post_b_user is not None
    post_b_wl = (
        await db_session.execute(
            select(UserWatchlist).where(UserWatchlist.user_id == user_b.id)
        )
    ).scalars().all()
    post_b_presets = (
        await db_session.execute(
            select(StrategyPreset).where(StrategyPreset.user_id == user_b.id)
        )
    ).scalars().all()
    post_b_bt = (
        await db_session.execute(
            select(BacktestHistory).where(BacktestHistory.user_id == user_b.id)
        )
    ).scalars().all()
    assert len(post_b_wl) == 3
    assert len(post_b_presets) == 3
    assert len(post_b_bt) == 3

    # Post-condition 3: PredictionAudit must remain intact
    post_audit = await db_session.get(PredictionAudit, audit_record.id)
    assert post_audit is not None
    assert post_audit.symbol == "VNINDEX"


@pytest.mark.asyncio
async def test_adversarial_deterministic_uuid_pk_collision(db_session: AsyncSession):
    """Stress Test: Inserting two records with identical UUID primary key must fail."""
    fixed_id = uuid.uuid4()

    u1 = User(id=fixed_id, email="uuid_conflict_1@vnstock.vn", hashed_password="pw")
    db_session.add(u1)
    await db_session.commit()

    u2 = User(id=fixed_id, email="uuid_conflict_2@vnstock.vn", hashed_password="pw")
    db_session.add(u2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_adversarial_large_jsonb_equity_curve_10k_points(db_session: AsyncSession):
    """Stress Test: Storing and reloading 10,000 equity curve points in JSON/JSONB."""
    user = User(email="quant_whale@vnstock.vn", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()

    # Generate 10,000 sequential equity curve points
    ten_thousand_points = [
        {
            "step": i,
            "date": f"2020-01-{(i % 28) + 1:02d}",
            "equity": 100_000_000.0 + (i * 1234.56),
            "drawdown": float((i % 50) / 100.0),
            "benchmark": 1000.0 + (i * 0.5),
        }
        for i in range(10_000)
    ]

    bt = BacktestHistory(
        user_id=user.id,
        symbol="HPG",
        strategy_name="StressTest_10k_Points",
        strategy_type="Ensemble",
        start_date=date(2020, 1, 1),
        end_date=date(2024, 1, 1),
        initial_capital=100_000_000.0,
        total_return=1.234,
        sharpe_ratio=2.1,
        max_drawdown=0.15,
        win_rate=0.62,
        equity_curve=ten_thousand_points,
    )
    db_session.add(bt)
    await db_session.commit()
    await db_session.refresh(bt)

    # Detach and reload in fresh query
    db_session.expunge(bt)
    loaded_bt = await db_session.get(BacktestHistory, bt.id)

    assert loaded_bt is not None
    assert len(loaded_bt.equity_curve) == 10_000
    assert loaded_bt.equity_curve[0]["step"] == 0
    assert loaded_bt.equity_curve[5000]["step"] == 5000
    assert loaded_bt.equity_curve[9999]["step"] == 9999
    assert loaded_bt.equity_curve[9999]["equity"] == 100_000_000.0 + (9999 * 1234.56)


@pytest.mark.asyncio
async def test_adversarial_deeply_nested_parameters_jsonb(db_session: AsyncSession):
    """Stress Test: Complex nested dictionary structures, unicode, and varied types in JSONB."""
    user = User(email="nested_json@vnstock.vn", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()

    complex_parameters = {
        "strategy_config": {
            "name": "Chiến lược Siêu Cổ Phiếu 2026 🚀",
            "weights": [0.35, 0.25, 0.40],
            "risk_controls": {
                "stop_loss": {"enabled": True, "value": 0.07, "trailing": False},
                "take_profit": {"levels": [{"ratio": 0.5, "target": 0.15}, {"ratio": 0.5, "target": 0.25}]},
                "market_filter": {"vnindex_ma200_above": True, "breadth_threshold": 0.65},
            },
            "sub_models": {
                "lstm": {"hidden_dim": 128, "layers": 2, "dropout": 0.2},
                "lightgbm": {"n_estimators": 500, "learning_rate": 0.03, "colsample_bytree": 0.8},
            },
        },
        "vietnamese_chars": "Đầu tư thông minh, quản trị rủi ro chặt chẽ, tối đa hoá lợi nhuận.",
        "boolean_flag": False,
        "null_field": None,
        "extreme_float": 1.2345678901234567e-15,
    }

    preset = StrategyPreset(
        user_id=user.id,
        name="Deeply Nested Complex Preset",
        description="Preset with deep JSON nesting and Vietnamese unicode",
        parameters=complex_parameters,
    )
    db_session.add(preset)
    await db_session.commit()
    await db_session.refresh(preset)

    db_session.expunge(preset)
    reloaded = await db_session.get(StrategyPreset, preset.id)

    assert reloaded is not None
    assert reloaded.parameters["strategy_config"]["name"] == "Chiến lược Siêu Cổ Phiếu 2026 🚀"
    assert reloaded.parameters["strategy_config"]["sub_models"]["lstm"]["hidden_dim"] == 128
    assert reloaded.parameters["vietnamese_chars"] == "Đầu tư thông minh, quản trị rủi ro chặt chẽ, tối đa hoá lợi nhuận."
    assert reloaded.parameters["null_field"] is None
    assert reloaded.parameters["boolean_flag"] is False


@pytest.mark.asyncio
async def test_adversarial_massive_watchlist_symbols(db_session: AsyncSession):
    """Stress Test: Watchlist storing 1,000 distinct stock tickers."""
    user = User(email="broad_market_watcher@vnstock.vn", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()

    symbols = [f"TICKER_{i:04d}" for i in range(1000)]
    wl = UserWatchlist(user_id=user.id, name="VN All-Share 1000", symbols=symbols)
    db_session.add(wl)
    await db_session.commit()

    db_session.expunge(wl)
    reloaded_wl = await db_session.get(UserWatchlist, wl.id)

    assert reloaded_wl is not None
    assert len(reloaded_wl.symbols) == 1000
    assert reloaded_wl.symbols[0] == "TICKER_0000"
    assert reloaded_wl.symbols[999] == "TICKER_0999"


@pytest.mark.asyncio
async def test_adversarial_prediction_audit_probabilities_precision(db_session: AsyncSession):
    """Stress Test: PredictionAudit storing precision probabilities and extreme distributions."""
    audit = PredictionAudit(
        symbol="MWG",
        prediction_date=date(2024, 6, 1),
        target_date=date(2024, 6, 4),
        predicted_signal=0,
        predicted_probabilities={
            "down": 0.99999999999,
            "neutral": 0.000000000005,
            "up": 0.000000000005,
        },
    )
    db_session.add(audit)
    await db_session.commit()

    db_session.expunge(audit)
    reloaded_audit = await db_session.get(PredictionAudit, audit.id)

    assert reloaded_audit is not None
    assert reloaded_audit.predicted_probabilities["down"] > 0.9999
    assert reloaded_audit.predicted_probabilities["up"] < 1e-10


@pytest.mark.asyncio
async def test_adversarial_high_concurrency_sessions(db_engine: AsyncEngine):
    """Concurrency Stress Test: 30 concurrent async tasks creating distinct users and sessions."""
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def worker_task(index: int) -> uuid.UUID:
        async with session_factory() as session:
            user = User(
                email=f"concurrent_worker_{index}_{uuid.uuid4().hex[:6]}@vnstock.vn",
                hashed_password=f"hash_{index}",
                full_name=f"Worker {index}",
            )
            session.add(user)
            await session.commit()
            return user.id

    # Execute 30 concurrent insertion tasks
    task_results = await asyncio.gather(*[worker_task(i) for i in range(30)])

    assert len(task_results) == 30
    assert len(set(task_results)) == 30  # All UUIDs unique

    # Verify all 30 users exist in database
    async with session_factory() as verify_session:
        res = await verify_session.execute(
            select(User).where(User.email.like("concurrent_worker_%"))
        )
        saved_users = res.scalars().all()
        assert len(saved_users) == 30


@pytest.mark.asyncio
async def test_adversarial_session_rollback_isolation_and_get_db(db_engine: AsyncEngine):
    """Stress Test: Transaction rollback cleans up failed operations and does not poison subsequent sessions."""
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    conflict_email = "rollback_target@vnstock.vn"

    # Step 1: Commit initial user
    async with session_factory() as session1:
        u1 = User(email=conflict_email, hashed_password="pw1", full_name="User 1")
        session1.add(u1)
        await session1.commit()

    # Step 2: Attempt duplicate in session2, trigger IntegrityError and rollback
    async with session_factory() as session2:
        u2 = User(email=conflict_email, hashed_password="pw2", full_name="User 2 Conflict")
        session2.add(u2)
        with pytest.raises(IntegrityError):
            await session2.commit()
        await session2.rollback()

    # Step 3: Verify session3 opens cleanly, is unpoisoned, and successfully commits new user
    clean_email = "clean_after_rollback@vnstock.vn"
    async with session_factory() as session3:
        u3 = User(email=clean_email, hashed_password="pw3", full_name="User 3 Clean")
        session3.add(u3)
        await session3.commit()

    # Step 4: Verification session confirms exact expected state
    async with session_factory() as session4:
        res = await session4.execute(
            select(User).where(User.email.in_([conflict_email, clean_email]))
        )
        saved = {u.email: u.full_name for u in res.scalars().all()}
        assert len(saved) == 2
        assert saved[conflict_email] == "User 1"
        assert saved[clean_email] == "User 3 Clean"


@pytest.mark.asyncio
async def test_adversarial_get_db_generator_lifecycle(db_engine: AsyncEngine):
    """Stress Test: get_db() lifecycle commits on normal exit and rolls back on exception."""
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    # Replicate get_db() logic with test session_factory
    async def custom_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    # 1. Normal execution commits
    test_email = "get_db_success@vnstock.vn"
    async for sess in custom_get_db():
        sess.add(User(email=test_email, hashed_password="pw"))

    # Verify committed
    async with session_factory() as check_sess:
        u = (await check_sess.execute(select(User).where(User.email == test_email))).scalar_one_or_none()
        assert u is not None

    # 2. Exception inside generator triggers rollback
    fail_email = "get_db_fail@vnstock.vn"
    with pytest.raises(RuntimeError):
        async for sess in custom_get_db():
            sess.add(User(email=fail_email, hashed_password="pw"))
            raise RuntimeError("Simulated unhandled route failure")

    # Verify rolled back (fail_email must NOT exist)
    async with session_factory() as check_sess:
        u_fail = (await check_sess.execute(select(User).where(User.email == fail_email))).scalar_one_or_none()
        assert u_fail is None
