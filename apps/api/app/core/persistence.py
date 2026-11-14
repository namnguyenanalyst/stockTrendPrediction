"""Explicit rollback for write conflicts, keeping the session usable after rejection."""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


async def commit_or_conflict(db: AsyncSession, detail="Conflicting saved data") -> None:
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, detail) from None
