"""Quản lý kết nối CSDL và phiên làm việc bất đồng bộ (AsyncSession) trong SQLAlchemy 2.0."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, StaticPool

from app.core.config import settings


def create_engine_for_url(url: str, echo: bool = False) -> AsyncEngine:
    """Tạo AsyncEngine phù hợp với dialect (PostgreSQL connection pooling hoặc SQLite)."""
    connect_args: dict[str, Any] = {}
    engine_kwargs: dict[str, Any] = {
        "echo": echo,
    }

    if "sqlite" in url:
        connect_args["check_same_thread"] = False
        engine_kwargs["connect_args"] = connect_args
        if ":memory:" in url:
            engine_kwargs["poolclass"] = StaticPool
        else:
            engine_kwargs["poolclass"] = NullPool
    else:
        # PostgreSQL / asyncpg production settings
        engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
        engine_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT
        engine_kwargs["pool_recycle"] = settings.DB_POOL_RECYCLE
        engine_kwargs["pool_pre_ping"] = True

    return create_async_engine(url, **engine_kwargs)


# Module-level engine và sessionmaker sử dụng cấu hình từ settings
engine: AsyncEngine = create_engine_for_url(settings.async_db_url, echo=settings.DB_ECHO)
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency cung cấp AsyncSession với cơ chế transaction an toàn."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
