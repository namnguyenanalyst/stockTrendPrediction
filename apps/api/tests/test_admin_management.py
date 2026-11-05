"""Tests cho module Admin (/api/v1/admin): User management, Self-protection, và Activity logs."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.db.models.user import RiskProfile, User, UserRole


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Tạo user có quyền ADMIN."""
    user = User(
        id=uuid.uuid4(),
        email="admin_super@example.com",
        hashed_password=get_password_hash("AdminSecret123"),
        role=UserRole.ADMIN,
        risk_profile=RiskProfile.BALANCED,
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
        risk_profile=RiskProfile.AGGRESSIVE,
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
    assert res_role.status_code == 200
    assert res_role.json()["role"] == "admin"


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
