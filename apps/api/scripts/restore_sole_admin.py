"""Preview, then apply a reviewed restoration plan with an exclusive users lock.

Run from apps/api with PYTHONPATH=.: python scripts/restore_sole_admin.py --snapshot /private/path.json
Then repeat with the same snapshot and --apply. Snapshot contains credentials; never commit it.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
from sqlalchemy import select, text, delete
from app.db.session import async_session_factory, engine
from app.db.models import User, UserRole, RefreshSession, UserManagementAudit

TARGETS = {"admin@vnstock": (UserRole.ADMIN, True),
           "hainamnguyen0104@gmail.com": (UserRole.TRADER, True),
           "admin@vnstock.io": (UserRole.TRADER, False)}

async def capture(db):
    users = (await db.execute(select(User).order_by(User.email))).scalars().all()
    if set(TARGETS) - {u.email for u in users}:
        raise RuntimeError("Missing expected account; refusing restoration")
    if any(u.role == UserRole.ADMIN and u.email not in TARGETS for u in users):
        raise RuntimeError("Unexpected administrator; refusing restoration")
    selected = [u for u in users if u.email in TARGETS]
    sessions = (await db.execute(select(RefreshSession).where(RefreshSession.user_id.in_([u.id for u in selected])).order_by(RefreshSession.token_hash))).scalars().all()
    def row(obj):
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    state = json.loads(json.dumps({"users": [row(u) for u in selected], "sessions": [row(s) for s in sessions]}, default=str))
    return selected, state

async def run(snapshot: Path, apply: bool):
    async with async_session_factory() as db:
        async with db.begin():
            if apply:
                if db.bind.dialect.name != "postgresql":
                    raise RuntimeError("Apply requires PostgreSQL")
                await db.execute(text("LOCK TABLE users, refresh_sessions IN EXCLUSIVE MODE"))
            users, state = await capture(db)
            changed = [u for u in users if (u.role, u.is_active) != TARGETS[u.email]]
            if not apply:
                fd = os.open(snapshot, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w") as out:
                    json.dump(state, out, indent=2)
                print("Private snapshot saved; changes:", [u.email for u in changed])
                return
            if snapshot.stat().st_mode & 0o077:
                raise RuntimeError("Snapshot must be readable only by its owner")
            expected = json.loads(snapshot.read_text())
            if not changed:
                print("Already restored; no session versions changed")
                return
            if state != expected:
                raise RuntimeError("State changed since preview; create a fresh snapshot")
            for u in changed:
                role, active = TARGETS[u.email]
                db.add(UserManagementAudit(actor=None, target_id=u.id, target_email=u.email,
                    old_role=u.role.value, new_role=role.value, old_active=u.is_active,
                    new_active=active, source="maintenance"))
                u.role, u.is_active = role, active
                u.auth_version += 1
                await db.execute(delete(RefreshSession).where(RefreshSession.user_id == u.id))
            await db.flush()
            print("Restored:", [u.email for u in changed])
    await engine.dispose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.snapshot, args.apply))
