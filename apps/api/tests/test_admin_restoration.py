"""Restoration preconditions on an isolated in-memory database."""
import importlib.util
from pathlib import Path
import pytest
from app.db.models import User, UserRole

spec = importlib.util.spec_from_file_location('restore', Path(__file__).parents[1] / 'scripts/restore_sole_admin.py')
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)

@pytest.mark.asyncio
async def test_missing_accounts_refused(db_session):
    with pytest.raises(RuntimeError, match='Missing'):
        await restore.capture(db_session)

@pytest.mark.asyncio
async def test_unexpected_admin_refused(db_session):
    for email in [*restore.TARGETS, 'unexpected@example.com']:
        db_session.add(User(email=email, hashed_password='unused', role=UserRole.ADMIN))
    await db_session.commit()
    with pytest.raises(RuntimeError, match='Unexpected'):
        await restore.capture(db_session)

@pytest.mark.asyncio
async def test_preview_private_snapshot_and_no_mutation(db_session, monkeypatch, tmp_path):
    from contextlib import asynccontextmanager
    import json
    for email in restore.TARGETS:
        db_session.add(User(email=email, hashed_password='unused', role=UserRole.ADMIN))
    await db_session.commit()
    @asynccontextmanager
    async def factory():
        yield db_session
    monkeypatch.setattr(restore, 'async_session_factory', factory)
    snapshot = tmp_path / 'private.json'
    await restore.run(snapshot, False)
    assert snapshot.stat().st_mode & 0o777 == 0o600
    assert len(json.loads(snapshot.read_text())['users']) == 3
    users, _ = await restore.capture(db_session)
    assert all(u.role == UserRole.ADMIN and u.auth_version == 0 for u in users)
    await db_session.commit()
    with pytest.raises(FileExistsError):
        await restore.run(snapshot, False)
