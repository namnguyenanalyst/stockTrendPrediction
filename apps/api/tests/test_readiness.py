from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app


@pytest.mark.asyncio
async def test_ready_checks_the_current_session_schema(async_client):
    response = await async_client.get("/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "reachable"


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [
    OperationalError("PRIVATE SQL", {}, RuntimeError("private host")),
    OSError("private hostname"), TimeoutError("private timeout"),
])
async def test_ready_reports_database_failure_without_private_details(async_client, failure):
    previous = app.dependency_overrides[get_db]
    db = AsyncMock()
    db.execute.side_effect = failure

    async def unavailable():
        yield db

    app.dependency_overrides[get_db] = unavailable
    try:
        response = await async_client.get("/ready")
        assert response.status_code == 503
        assert "PRIVATE" not in response.text
    finally:
        app.dependency_overrides[get_db] = previous
