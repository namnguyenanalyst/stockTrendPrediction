"""Regression tests for authentication boundaries, durable sessions and API failures."""

import asyncio
import threading
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from unittest.mock import AsyncMock

import bcrypt
import jwt
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.core.persistence import commit_or_conflict
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from app.core.sessions import add_refresh_session, consume_refresh_session
from app.db.models.user import User
from app.schemas.backtest import BacktestHistoryCreateRequest
from app.schemas.preset import PresetCreateRequest
from app.services import prediction_service


def test_password_tail_is_part_of_the_secret():
    password = "A" * 72 + "one"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("A" * 72 + "two", hashed)


def test_legacy_hash_accepts_short_password_but_rejects_ambiguous_long_password():
    hashed = bcrypt.hashpw(b"A" * 72, bcrypt.gensalt(rounds=4)).decode()
    assert verify_password("A" * 72, hashed)
    assert not verify_password("A" * 72 + "tail", hashed)


@pytest.mark.asyncio
@pytest.mark.parametrize("missing", ["exp", "iat", "type", "sub"])
async def test_tokens_require_all_security_claims(async_client, db_session, missing):
    user = User(id=uuid.uuid4(), email=f"claims_{uuid.uuid4().hex}@test.vn", hashed_password="unused")
    db_session.add(user)
    await db_session.commit()
    now = int(datetime.now(timezone.utc).timestamp())
    payload = {"sub": str(user.id), "type": "access", "iat": now, "exp": now + 300}
    payload.pop(missing)
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    response = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def history_payload():
    return {"symbol": "VIC", "strategy_name": "Test", "strategy_type": "ai",
            "start_date": "2026-01-01", "end_date": "2026-02-01", "initial_capital": 1e8,
            "total_return": 1., "sharpe_ratio": .1, "max_drawdown": 2., "win_rate": 50.}


@pytest.mark.parametrize("updates", [
    {"end_date": "2025-01-01"}, {"initial_capital": float("inf")},
    {"total_return": float("nan")}, {"win_rate": 101.}, {"strategy_name": " "},
])
def test_saved_financial_records_reject_invalid_values(updates):
    with pytest.raises(ValidationError):
        BacktestHistoryCreateRequest(**{**history_payload(), **updates})


def test_prediction_does_not_expose_internal_exception_details():
    with patch("vn_stock.modeling.predict_trend", side_effect=RuntimeError("PRIVATE_FILE=/secret/model")):
        with pytest.raises(HTTPException) as exc:
            prediction_service.predict_stock_signal()
    assert "PRIVATE_FILE" not in exc.value.detail


@pytest.mark.asyncio
async def test_blocking_prediction_is_dispatched_off_event_loop(async_client):
    loop_thread = threading.get_ident()
    called_threads = []

    def fail_in_worker(**kwargs):
        called_threads.append(threading.get_ident())
        raise HTTPException(503, "Model unavailable")

    with patch.object(prediction_service, "predict_stock_signal", side_effect=fail_in_worker):
        response = await async_client.get("/api/predict/signal")
    assert response.status_code == 503
    assert called_threads and called_threads[0] != loop_thread


async def login_session(client):
    email = f"session_{uuid.uuid4().hex}@test.vn"
    response = await client.post("/api/v1/auth/register", json={"email": email, "password": "SafePassword@123"})
    assert response.status_code == 201
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": "SafePassword@123"})
    assert response.status_code == 200
    return response


@pytest.mark.asyncio
async def test_refresh_rotation_rejects_replay_and_logout_revokes_cookie(async_client, db_session):
    from sqlalchemy import select
    from app.db.models.refresh_session import RefreshSession
    from app.core.sessions import token_digest

    logged_in = await login_session(async_client)
    old = logged_in.cookies["refresh_token"]
    refreshed = await async_client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    rotated = refreshed.cookies["refresh_token"]
    assert rotated != old
    assert decode_token(rotated)["exp"] == decode_token(old)["exp"]
    saved = (await db_session.execute(select(RefreshSession))).scalars().all()
    assert len(saved) == 1 and saved[0].token_hash == token_digest(rotated)
    replay = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": old})
    assert replay.status_code == 401
    assert (await async_client.post("/api/v1/auth/logout")).status_code == 204
    assert not async_client.cookies.get("refresh_token")
    assert (await async_client.post("/api/v1/auth/refresh", json={"refresh_token": rotated})).status_code == 401


@pytest.mark.parametrize("symbol", ["../secret", "/tmp/private", "", "A" * 21])
def test_invalid_symbols_never_reach_disk_or_remote_fetch(symbol):
    from app.services import stock_service

    with patch("pandas.read_parquet") as reader:
        with pytest.raises(HTTPException) as exc:
            stock_service.load_stock_dataframe(symbol)
    assert exc.value.status_code == 400
    reader.assert_not_called()


def test_invalid_batch_model_cannot_be_reported_as_successful_empty_batch():
    with pytest.raises(HTTPException) as exc:
        prediction_service.predict_batch_signals(model_type="unsupported")
    assert exc.value.status_code == 400


def test_status_refuses_a_corrupt_manifest_instead_of_falling_back(tmp_path, monkeypatch):
    from app.routers.prediction import get_predict_status

    monkeypatch.setattr(settings, "MODELS_DIR", tmp_path)
    (tmp_path / "production_bundle_t3.json").write_text("{}")
    (tmp_path / "production_training_info_t3.json").write_text('{"timestamp":"loose-stale-info"}')
    with pytest.raises(HTTPException) as exc:
        get_predict_status()
    assert exc.value.status_code == 503


@pytest.mark.asyncio
@pytest.mark.parametrize("expected,supplied", [("   ", "   "), ("valid-secret", "é")])
async def test_worker_secret_blank_or_nonmatching_unicode_is_forbidden(expected, supplied, monkeypatch):
    from app.core.deps import verify_internal_worker_secret

    monkeypatch.setattr(settings, "INTERNAL_WORKER_SECRET", expected)
    with pytest.raises(HTTPException) as exc:
        await verify_internal_worker_secret(supplied)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_cookie_session_changes_reject_untrusted_origin(async_client):
    await login_session(async_client)
    response = await async_client.post("/api/v1/auth/refresh", headers={"Origin": "https://untrusted.invalid"})
    assert response.status_code == 403


def test_failed_live_sync_is_not_marked_successful():
    with patch("vn_stock.data_ingestion.fetch_stock_data", side_effect=RuntimeError("offline")), \
         patch("vn_stock.modeling.predict_trend") as predict:
        with pytest.raises(HTTPException) as exc:
            prediction_service.sync_live_and_predict()
    assert exc.value.status_code == 503
    predict.assert_not_called()


@pytest.mark.parametrize("stale_stage", ["download", "prediction"])
def test_stale_cache_cannot_be_marked_live_synced(stale_stage):
    import pandas as pd

    date = "2020-01-01" if stale_stage == "download" else "2026-11-13"
    with patch("vn_stock.market_session.get_target_market_date", return_value="2026-11-13"), \
         patch("vn_stock.data_ingestion.fetch_stock_data", return_value=pd.DataFrame({"Date": [date]})), \
         patch("vn_stock.modeling.predict_trend", return_value={"date": "2020-01-01"}):
        with pytest.raises(HTTPException) as exc:
            prediction_service.sync_live_and_predict()
    assert exc.value.status_code == 503


@pytest.mark.parametrize("key", ["", "short", Settings.model_fields["JWT_SECRET_KEY"].default])
def test_production_rejects_default_or_short_jwt_secret(key):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ENVIRONMENT="production", JWT_SECRET_KEY=key)


def test_extra_claims_cannot_override_token_security_fields():
    token = create_access_token("owner", {"sub": "attacker", "type": "refresh", "exp": 0})
    payload = decode_token(token)
    assert payload["sub"] == "owner" and payload["type"] == "access"


def test_nested_nonfinite_json_is_rejected_before_database_serialization():
    with pytest.raises(ValidationError):
        PresetCreateRequest(name="Risk", parameters={"nested": [float("nan")]})
    with pytest.raises(ValidationError):
        BacktestHistoryCreateRequest(**{**history_payload(), "equity_curve": [{"equity": float("inf")}]})


@pytest.mark.asyncio
async def test_conflicting_write_rolls_back_and_returns_safe_conflict():
    from sqlalchemy.exc import IntegrityError

    db = AsyncMock()
    db.commit.side_effect = IntegrityError("private SQL", {}, RuntimeError("private constraint"))
    with pytest.raises(HTTPException) as exc:
        await commit_or_conflict(db)
    assert exc.value.status_code == 409
    assert "private" not in exc.value.detail
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_validation_response_does_not_echo_password(async_client):
    response = await async_client.post("/api/v1/auth/register", json={"email": "invalid", "password": "SECRET"})
    assert response.status_code == 422
    assert "SECRET" not in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("resource,payload,changed", [
    ("watchlists", {"name": "Old", "symbols": ["VIC"]}, {"name": "New", "symbols": ["HPG"]}),
    ("presets", {"name": "Old", "parameters": {"state": "Draft"}},
     {"name": "New", "parameters": {"state": "Active"}}),
])
async def test_update_saved_data_is_durable_and_owner_scoped(async_client, db_session, resource, payload, changed):
    from app.db.models.user import UserRole

    owner = User(id=uuid.uuid4(), email=f"owner{uuid.uuid4().hex}@test.vn", hashed_password="unused")
    outsider = User(id=uuid.uuid4(), email=f"admin{uuid.uuid4().hex}@test.vn", hashed_password="unused", role=UserRole.ADMIN)
    db_session.add_all([owner, outsider])
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(owner.id)}"}
    other_headers = {"Authorization": f"Bearer {create_access_token(outsider.id)}"}
    base = f"/api/v1/user/{resource}"
    created = await async_client.post(base, json=payload, headers=headers)
    assert created.status_code == 201
    path = base + "/" + created.json()["id"]
    denied = await async_client.put(path, json=changed, headers=other_headers)
    assert denied.status_code == 404
    saved = await async_client.put(path, json={**changed, "user_id": str(outsider.id)}, headers=headers)
    assert saved.status_code == 200 and saved.json()["user_id"] == str(owner.id)
    db_session.expire_all()
    listed = await async_client.get(base, headers=headers)
    assert listed.json()[0]["name"] == "New"
    assert (await async_client.get(base, headers=other_headers)).json() == []
    assert (await async_client.get(base + "?limit=1&offset=1", headers=headers)).json() == []


@pytest.mark.asyncio
async def test_refresh_consumption_is_atomic_across_database_sessions(tmp_path):
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.db.models import Base

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'sessions.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        async with factory() as db:
            db.add(User(id=user_id, email="atomic@test.vn", hashed_password="unused"))
            await db.flush()
            add_refresh_session(db, token, user_id)
            await db.commit()

        async def consume():
            async with factory() as db:
                try:
                    await consume_refresh_session(db, token, user_id)
                    await db.commit()
                    return 200
                except HTTPException as exc:
                    await db.rollback()
                    return exc.status_code

        assert sorted(await asyncio.gather(consume(), consume())) == [200, 401]
    finally:
        await engine.dispose()


def test_refresh_session_migration_round_trip(tmp_path, monkeypatch):
    import sqlite3
    import logging
    from alembic import command
    from alembic.config import Config

    path = tmp_path / "migration.db"
    monkeypatch.setattr(settings, "ASYNC_DATABASE_URL", f"sqlite+aiosqlite:///{path}")
    config = Config("alembic.ini")
    prediction_logger = logging.getLogger("app.services.prediction_service")
    command.upgrade(config, "003_refresh_sessions")
    assert not prediction_logger.disabled
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "003_refresh_sessions"
        assert db.execute("PRAGMA table_info(refresh_sessions)").fetchall()
    command.downgrade(config, "-1")
    with sqlite3.connect(path) as db:
        assert not db.execute("PRAGMA table_info(refresh_sessions)").fetchall()
        assert db.execute("PRAGMA table_info(users)").fetchall()
