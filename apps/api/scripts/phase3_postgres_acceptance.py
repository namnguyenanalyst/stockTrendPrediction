"""Explicit local integration probe: creates two temporary users and deletes them afterwards.

Run from apps/api: uv run python scripts/phase3_postgres_acceptance.py --run
Uses real ASGI routes and configured PostgreSQL, with no ML retraining or SSI requests.
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
import secrets
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from sqlalchemy import delete, func, select, text

from app.core.config import settings
from app.db.models.refresh_session import RefreshSession
from app.db.models.user import User
from app.db.session import async_session_factory, engine
from app.main import app


async def run_probe():
    if settings.ENVIRONMENT.lower() == "production" or engine.dialect.name != "postgresql":
        raise RuntimeError("Probe is restricted to non-production PostgreSQL.")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    user_ids, report = [], {}
    try:
        async with engine.connect() as conn:
            report["migration"] = (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalar_one()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://phase3.local") as client:
            access = []
            for _ in range(2):
                email, password = f"phase3_probe_{uuid.uuid4().hex}@example.invalid", secrets.token_urlsafe(32)
                registered = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
                assert registered.status_code == 201, "Registration failed"
                user_ids.append(uuid.UUID(registered.json()["id"]))
                logged_in = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
                assert logged_in.status_code == 200, "Login failed"
                access.append({"Authorization": "Bearer " + logged_in.json()["access_token"]})
            report["register_login_real_postgres"] = True
            base = "/api/v1/user/presets"
            saved = await client.post(base, json={"name": "Phase3 probe", "parameters": {"state": "Draft"}}, headers=access[0])
            assert saved.status_code == 201, "Saving preset failed"
            path = base + "/" + saved.json()["id"]
            changed = {"name": "Updated probe", "parameters": {"state": "Active"}}
            assert (await client.put(path, json=changed, headers=access[1])).status_code == 404
            assert (await client.put(path, json=changed, headers=access[0])).status_code == 200
            listed = await client.get(base, headers=access[0])
            assert listed.json()[0]["parameters"]["state"] == "Active"
            report["owner_isolation_and_durable_update"] = True
            old = client.cookies["refresh_token"]
            results = await asyncio.gather(*[
                client.post("/api/v1/auth/refresh", json={"refresh_token": old}) for _ in range(2)])
            report["concurrent_refresh_statuses"] = sorted(r.status_code for r in results)
            assert report["concurrent_refresh_statuses"] == [200, 401]
            rotated = next(r for r in results if r.status_code == 200).cookies["refresh_token"]
            assert rotated != old
            assert (await client.post("/api/v1/auth/logout", json={"refresh_token": rotated})).status_code == 204
            assert (await client.post("/api/v1/auth/refresh", json={"refresh_token": rotated})).status_code == 401
            report["logout_revocation"] = True
    finally:
        async with async_session_factory() as db:
            await db.execute(delete(User).where(User.id.in_(user_ids)))
            await db.commit()
            report["remaining_probe_users"] = (await db.execute(
                select(func.count()).select_from(User).where(User.id.in_(user_ids)))).scalar_one()
            report["remaining_probe_sessions"] = (await db.execute(
                select(func.count()).select_from(RefreshSession).where(RefreshSession.user_id.in_(user_ids)))).scalar_one()
        await engine.dispose()
    assert report["remaining_probe_users"] == report["remaining_probe_sessions"] == 0
    output = Path(__file__).resolve().parents[1] / "reports" / "phase3_postgres_acceptance.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.parse_args()
    asyncio.run(run_probe())
