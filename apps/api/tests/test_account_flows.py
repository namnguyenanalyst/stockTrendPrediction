"""Account lifecycle regression tests; SMTP is always replaced in these tests."""

import asyncio
import os
from datetime import timedelta

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, update

from app.core.account_actions import now_utc
from app.db.models.account_action import AccountAction, AccountRateLimit
from app.db.models.user import User


@pytest.fixture(autouse=True)
def mail(monkeypatch):
    deliveries = []
    monkeypatch.setattr(
        "app.routers.auth.send_account_mail", lambda *args: deliveries.append(args)
    )
    return deliveries


@pytest_asyncio.fixture
async def db_engine():
    # A dedicated disposable database only. Never point this at development data.
    from app.db.models import Base
    from app.db.session import create_engine_for_url

    engine = create_engine_for_url(
        os.getenv("ACCOUNT_TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def register(client, email="flow@example.com"):
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "original-password"}
    )
    assert response.status_code == 201, response.text
    return response.json()


async def login(client, email="flow@example.com", password="original-password"):
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


async def clear_limits(db):
    await db.execute(delete(AccountRateLimit))
    await db.commit()


@pytest.mark.asyncio
async def test_registration_and_verification(async_client, mail, db_session):
    user = await register(async_client)
    assert user["email_verified_at"] is None
    assert "risk_profile" not in user
    recipient, token, purpose = mail[-1]
    assert (recipient, purpose) == ("flow@example.com", "verify")
    stored = (await db_session.execute(select(AccountAction))).scalar_one()
    assert stored.token_hash != token and len(stored.token_hash) == 64
    auth = {"Authorization": f"Bearer {await login(async_client)}"}
    assert (await async_client.get("/api/v1/auth/me", headers=auth)).status_code == 200
    # GET cannot mutate verification state.
    assert (
        await async_client.get("/api/v1/auth/verify-email", params={"token": token})
    ).status_code == 405
    assert (
        await async_client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "changed-password"},
        )
    ).status_code == 400
    assert (
        await async_client.post("/api/v1/auth/verify-email", json={"token": token})
    ).status_code == 200
    assert (
        await async_client.post("/api/v1/auth/verify-email", json={"token": token})
    ).status_code == 400
    assert (await async_client.get("/api/v1/auth/me", headers=auth)).json()["email_verified_at"]
    before = len(mail)
    assert (
        await async_client.post("/api/v1/auth/resend-verification", headers=auth)
    ).status_code == 202
    assert len(mail) == before


@pytest.mark.asyncio
async def test_resend_invalidates_previous_token(async_client, mail, db_session):
    await register(async_client)
    old = mail[-1][1]
    await clear_limits(db_session)
    auth = {"Authorization": f"Bearer {await login(async_client)}"}
    assert (
        await async_client.post("/api/v1/auth/resend-verification", headers=auth)
    ).status_code == 202
    new = mail[-1][1]
    assert old != new
    assert (
        await async_client.post("/api/v1/auth/verify-email", json={"token": old})
    ).status_code == 400
    assert (
        await async_client.post("/api/v1/auth/verify-email", json={"token": new})
    ).status_code == 200


@pytest.mark.asyncio
async def test_reset_revokes_every_session(async_client, db_session, mail):
    await register(async_client)
    token1 = await login(async_client)
    refresh1 = async_client.cookies.get("refresh_token")
    token2 = await login(async_client)
    refresh2 = async_client.cookies.get("refresh_token")
    await clear_limits(db_session)
    assert (
        await async_client.post("/api/v1/auth/forgot-password", json={"email": "FLOW@example.com"})
    ).status_code == 202
    reset = mail[-1][1]
    assert mail[-1][2] == "reset"
    response = await async_client.post(
        "/api/v1/auth/reset-password", json={"token": reset, "new_password": "new-password"}
    )
    assert response.status_code == 200, response.text
    for access in (token1, token2):
        assert (
            await async_client.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"}
            )
        ).status_code == 401
    for refresh in (refresh1, refresh2):
        assert (
            await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        ).status_code == 401
    assert (
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "flow@example.com", "password": "original-password"},
        )
    ).status_code == 401
    assert (
        await async_client.post(
            "/api/v1/auth/reset-password", json={"token": reset, "new_password": "other-password"}
        )
    ).status_code == 400
    access = await login(async_client, password="new-password")
    profile = (
        await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    ).json()
    assert profile["email_verified_at"] is None


@pytest.mark.asyncio
async def test_expired_and_invalid_tokens(async_client, db_session, mail):
    await register(async_client)
    token = mail[-1][1]
    await db_session.execute(
        update(AccountAction).values(expires_at=now_utc() - timedelta(seconds=1))
    )
    await db_session.commit()
    for value in (token, "invalid"):
        r = await async_client.post("/api/v1/auth/verify-email", json={"token": value})
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "INVALID_OR_EXPIRED_TOKEN"


@pytest.mark.asyncio
async def test_unknown_inactive_and_send_limits(async_client, mail, db_session):
    await register(async_client)
    await clear_limits(db_session)
    start = len(mail)
    unknown = await async_client.post(
        "/api/v1/auth/forgot-password", json={"email": "missing@example.com"}
    )
    await db_session.execute(update(User).values(is_active=False))
    await db_session.commit()
    inactive = await async_client.post(
        "/api/v1/auth/forgot-password", json={"email": "flow@example.com"}
    )
    assert unknown.status_code == inactive.status_code == 202
    assert unknown.json() == inactive.json()
    assert len(mail) == start
    limited = await async_client.post(
        "/api/v1/auth/forgot-password", json={"email": "missing@example.com"}
    )
    assert limited.status_code == 429 and int(limited.headers["Retry-After"]) >= 60


@pytest.mark.asyncio
async def test_hourly_email_and_ip_limits(async_client, db_session):
    for i in range(5):
        assert (
            await async_client.post(
                "/api/v1/auth/forgot-password", json={"email": "same@example.com"}
            )
        ).status_code == 202
        # Simulate a minute passing without resetting the hour buckets.
        from app.core.sessions import token_digest

        await db_session.execute(
            delete(AccountRateLimit).where(
                AccountRateLimit.key == token_digest("send:minute:same@example.com")
            )
        )
        await db_session.commit()
    assert (
        await async_client.post("/api/v1/auth/forgot-password", json={"email": "same@example.com"})
    ).status_code == 429
    await clear_limits(db_session)
    for i in range(20):
        assert (
            await async_client.post(
                "/api/v1/auth/forgot-password", json={"email": f"user{i}@example.com"}
            )
        ).status_code == 202
    assert (
        await async_client.post("/api/v1/auth/forgot-password", json={"email": "last@example.com"})
    ).status_code == 429


@pytest.mark.asyncio
async def test_bad_token_attempts_are_counted(async_client):
    for _ in range(30):
        assert (
            await async_client.post("/api/v1/auth/verify-email", json={"token": "bad"})
        ).status_code == 400
    assert (
        await async_client.post("/api/v1/auth/verify-email", json={"token": "bad"})
    ).status_code == 429


@pytest.mark.asyncio
async def test_smtp_failure_preserves_registration(async_client, monkeypatch):
    from app.core.account_mail import send_account_mail

    monkeypatch.setattr("app.routers.auth.send_account_mail", send_account_mail)

    def fail(*args, **kwargs):
        raise OSError("fake secret must not reach HTTP response")

    monkeypatch.setattr("app.core.account_mail.smtplib.SMTP", fail)
    monkeypatch.setattr("app.core.account_mail.settings.SMTP_USERNAME", "sender@example.com")
    monkeypatch.setattr("app.core.account_mail.settings.SMTP_PASSWORD", "secret")
    assert (await register(async_client))["id"]
    assert await login(async_client)


@pytest.mark.asyncio
async def test_new_reset_replaces_old(async_client, db_session, mail):
    await register(async_client)
    await clear_limits(db_session)
    await async_client.post("/api/v1/auth/forgot-password", json={"email": "flow@example.com"})
    old = mail[-1][1]
    await clear_limits(db_session)
    await async_client.post("/api/v1/auth/forgot-password", json={"email": "flow@example.com"})
    new = mail[-1][1]
    for token, status in ((old, 400), (new, 200)):
        r = await async_client.post(
            "/api/v1/auth/reset-password", json={"token": token, "new_password": "new-password"}
        )
        assert r.status_code == status


@pytest.mark.asyncio
async def test_concurrent_reset_one_winner(db_engine, async_client, mail, db_session):
    if db_engine.dialect.name != "postgresql":
        pytest.skip("Requires independent PostgreSQL transactions")
    import httpx
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.db.session import get_db
    from app.main import app

    await register(async_client)
    await clear_limits(db_session)
    await async_client.post("/api/v1/auth/forgot-password", json={"email": "flow@example.com"})
    token = mail[-1][1]
    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def independent_db():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = independent_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        results = await asyncio.gather(
            *(
                client.post(
                    "/api/v1/auth/reset-password",
                    json={"token": token, "new_password": f"new-password-{i}"},
                )
                for i in range(2)
            )
        )
    assert sorted(r.status_code for r in results) == [200, 400]
