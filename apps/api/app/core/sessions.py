"""Database-backed refresh lifecycle shared by login, refresh and logout."""

import hashlib
from datetime import datetime, timezone
from urllib.parse import urlsplit

from fastapi import HTTPException, Request, Response
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.models.refresh_session import RefreshSession

COOKIE_PATH = "/api/v1/auth"


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def add_refresh_session(db: AsyncSession, token: str, user_id) -> None:
    payload = decode_token(token)
    db.add(RefreshSession(token_hash=token_digest(token), user_id=user_id,
                         expires_at=datetime.fromtimestamp(payload["exp"], timezone.utc)))


def set_refresh_cookie(response: Response, token: str) -> None:
    remaining = max(0, int(decode_token(token)["exp"] - datetime.now(timezone.utc).timestamp()))
    response.set_cookie("refresh_token", token, httponly=True, path=COOKIE_PATH,
                        secure=settings.ENVIRONMENT.lower() == "production", samesite="lax", max_age=remaining)


def check_cookie_origin(request: Request) -> None:
    allowed_origins = {origin.rstrip("/").lower() for origin in settings.CORS_ORIGINS}
    origin = request.headers.get("origin")
    if origin:
        if origin.rstrip("/").lower() not in allowed_origins:
            raise HTTPException(403, "Untrusted origin for cookie authentication")
        return
    referer = request.headers.get("referer")
    if referer:
        parsed = urlsplit(referer)
        if not parsed.scheme or not parsed.netloc:
            raise HTTPException(403, "Untrusted referer for cookie authentication")
        referer_origin = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
        if referer_origin not in allowed_origins:
            raise HTTPException(403, "Untrusted referer for cookie authentication")


async def consume_refresh_session(db: AsyncSession, token: str, user_id) -> None:
    result = await db.execute(delete(RefreshSession).where(
        RefreshSession.token_hash == token_digest(token), RefreshSession.user_id == user_id,
        RefreshSession.expires_at > datetime.now(timezone.utc)))
    if result.rowcount != 1:
        raise HTTPException(401, "Refresh session expired or revoked", headers={"WWW-Authenticate": "Bearer"})
