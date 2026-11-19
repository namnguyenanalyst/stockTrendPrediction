"""Tests cho module Admin (/api/v1/admin): User management, Self-protection, và Activity logs."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.models.user import User, UserRole


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Tạo user có quyền ADMIN."""
    user = User(
        id=uuid.uuid4(),
        email=settings.SOLE_ADMIN_EMAIL,
        hashed_password=get_password_hash("AdminSecret123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Tạo JWT access token cho admin."""
    return create_access_token(subject=admin_user.id)


@pytest.fixture
async def sample_trader(db_session: AsyncSession) -> User:
    """Tạo user có quyền TRADER."""
    user = User(
        id=uuid.uuid4(),
        email="trader_john@example.com",
        full_name="John Trader",
        hashed_password=get_password_hash("TraderSecret123"),
        role=UserRole.TRADER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def trader_token(sample_trader: User) -> str:
    """Tạo JWT access token cho trader."""
    return create_access_token(subject=sample_trader.id)


@pytest.mark.asyncio
async def test_admin_list_users_success(
    async_client: AsyncClient,
    admin_token: str,
    admin_user: User,
    sample_trader: User,
):
    """Admin có thể lấy danh sách người dùng kèm phân trang."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2
    emails = [u["email"] for u in data["items"]]
    assert admin_user.email in emails
    assert sample_trader.email in emails


@pytest.mark.asyncio
async def test_trader_cannot_list_users(
    async_client: AsyncClient,
    trader_token: str,
):
    """User vai trò TRADER bị 403 Forbidden khi truy cập danh sách user."""
    headers = {"Authorization": f"Bearer {trader_token}"}
    response = await async_client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_update_user_status_and_role(
    async_client: AsyncClient,
    admin_token: str,
    sample_trader: User,
):
    """Admin có thể khóa tài khoản và nâng quyền user khác."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Khóa tài khoản
    res_lock = await async_client.patch(
        f"/api/v1/admin/users/{sample_trader.id}",
        json={"is_active": False},
        headers=headers,
    )
    assert res_lock.status_code == 200
    assert res_lock.json()["is_active"] is False

    # 2. Nâng quyền lên ADMIN
    res_role = await async_client.patch(
        f"/api/v1/admin/users/{sample_trader.id}",
        json={"role": "admin"},
        headers=headers,
    )
    assert res_role.status_code == 403


@pytest.mark.asyncio
async def test_admin_self_protection_cannot_lock_or_demote_self(
    async_client: AsyncClient,
    admin_token: str,
    admin_user: User,
):
    """Admin không thể tự khóa tài khoản hoặc tự hạ quyền của chính mình."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Cố gắng tự khóa
    res_lock = await async_client.patch(
        f"/api/v1/admin/users/{admin_user.id}",
        json={"is_active": False},
        headers=headers,
    )
    assert res_lock.status_code == 400
    assert "không thể tự khóa tài khoản" in res_lock.json()["detail"]

    # Cố gắng tự hạ quyền
    res_demote = await async_client.patch(
        f"/api/v1/admin/users/{admin_user.id}",
        json={"role": "trader"},
        headers=headers,
    )
    assert res_demote.status_code == 400
    assert "không thể tự hạ quyền" in res_demote.json()["detail"]


@pytest.mark.asyncio
async def test_admin_activity_logs(
    async_client: AsyncClient,
    admin_token: str,
):
    """Admin có thể lấy nhật ký hoạt động của hệ thống."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/api/v1/admin/activity-logs", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)

@pytest.mark.asyncio
async def test_wrong_admin_email_denied(async_client, db_session, sample_trader):
    sample_trader.role = UserRole.ADMIN
    await db_session.commit()
    token = create_access_token(subject=sample_trader.id)
    res = await async_client.get('/api/v1/admin/users', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_changes_revoke_sessions_and_record_audit(async_client, db_session, admin_token, sample_trader):
    from sqlalchemy import select
    from app.db.models import RefreshSession, UserManagementAudit
    from datetime import datetime, timezone, timedelta
    from app.core.security import create_refresh_token
    from app.core.sessions import add_refresh_session
    refresh = create_refresh_token(subject=str(sample_trader.id), extra_claims={"auth_version": 0})
    access = create_access_token(subject=sample_trader.id)
    add_refresh_session(db_session, refresh, sample_trader.id)
    await db_session.commit()
    headers = {"Authorization": f"Bearer {admin_token}"}
    url = f"/api/v1/admin/users/{sample_trader.id}"
    assert (await async_client.patch(url, json={"is_active": False}, headers=headers)).status_code == 200
    assert sample_trader.auth_version == 1
    assert not (await db_session.execute(select(RefreshSession))).scalars().all()
    entries = (await db_session.execute(select(UserManagementAudit))).scalars().all()
    assert len(entries) == 1 and entries[0].old_active and not entries[0].new_active
    assert (await async_client.patch(url, json={"is_active": False}, headers=headers)).status_code == 200
    assert sample_trader.auth_version == 1
    assert (await async_client.get('/api/v1/admin/users', headers={"Authorization": f"Bearer {access}"})).status_code == 401
    assert (await async_client.post('/api/v1/auth/refresh', json={"refresh_token": refresh})).status_code == 401
    logs = (await async_client.get('/api/v1/admin/activity-logs', headers=headers)).json()
    assert any(x['event_type'] == 'user_management' for x in logs['items'])

@pytest.mark.asyncio
async def test_audit_failure_rolls_back(async_client, db_session, admin_token, sample_trader):
    from sqlalchemy import event, select
    from app.db.models import UserManagementAudit
    uid = sample_trader.id
    def fail(*args):
        raise RuntimeError('audit unavailable')
    event.listen(UserManagementAudit, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='audit unavailable'):
            await async_client.patch(f'/api/v1/admin/users/{uid}', json={'is_active': False},
                                     headers={'Authorization': f'Bearer {admin_token}'})
    finally:
        event.remove(UserManagementAudit, 'before_insert', fail)
    await db_session.rollback()  # Test dependency shares the session; production get_db rolls back.
    user = (await db_session.execute(select(User).where(User.id == uid))).scalar_one()
    assert user.is_active and user.auth_version == 0
