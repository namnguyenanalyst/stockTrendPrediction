"""Transactional single-use tokens and cross-worker, database-backed limits."""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.core.sessions import token_digest
from app.db.models.account_action import AccountAction, AccountRateLimit
from app.db.models.user import User


def now_utc():
    return datetime.now(timezone.utc)


async def rate_limit(db, key: str, maximum: int, seconds: int):
    now = now_utc()
    table = AccountRateLimit
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    expired = table.expires_at <= now
    stmt = insert(table).values(
        key=token_digest(key), count=1, expires_at=now + timedelta(seconds=seconds)
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[table.key],
        set_={
            "count": case((expired, 1), else_=table.count + 1),
            "expires_at": case(
                (expired, now + timedelta(seconds=seconds)), else_=table.expires_at
            ),
        },
        where=expired | (table.count < maximum),
    ).returning(table.count)
    if (await db.execute(stmt)).scalar_one_or_none() is None:
        raise HTTPException(
            429, detail={"code": "RATE_LIMITED"}, headers={"Retry-After": str(seconds)}
        )

    await db.commit()


async def send_limits(db, identity: str, ip: str):
    # Stable lock order across processes; counters for unknown emails are identical.
    await rate_limit(db, f"send:ip:{ip}", 20, 3600)
    await rate_limit(db, f"send:hour:{identity}", 5, 3600)
    await rate_limit(db, f"send:minute:{identity}", 1, 60)


async def issue_action(db, user, purpose):
    await db.execute(
        delete(AccountAction).where(
            AccountAction.user_id == user.id, AccountAction.purpose == purpose
        )
    )
    token = secrets.token_urlsafe(32)
    minutes = 1440 if purpose == "verify" else 30
    db.add(
        AccountAction(
            token_hash=token_digest(token),
            user_id=user.id,
            purpose=purpose,
            expires_at=now_utc() + timedelta(minutes=minutes),
        )
    )
    await db.flush()
    return token


async def consume_action(db, token, purpose):
    conditions = (
        AccountAction.token_hash == token_digest(token),
        AccountAction.purpose == purpose,
        AccountAction.expires_at > now_utc(),
    )
    user_id = (
        await db.execute(select(AccountAction.user_id).where(*conditions))
    ).scalar_one_or_none()
    if user_id is not None:
        user = (
            await db.execute(
                select(User)
                .where(User.id == user_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()
        if user and user.is_active:
            result = await db.execute(
                delete(AccountAction)
                .where(*conditions)
                .returning(AccountAction.user_id)
                .execution_options(synchronize_session="fetch")
            )
            if result.scalar_one_or_none() is not None:
                return user
    raise HTTPException(400, detail={"code": "INVALID_OR_EXPIRED_TOKEN"})
