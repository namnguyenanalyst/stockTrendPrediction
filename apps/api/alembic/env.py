"""Alembic environment configuration cho SQLAlchemy 2.0 Async."""

import asyncio
import concurrent.futures
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.models import Base

# Alembic Config object
config = context.config

# Cấu hình logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata của toàn bộ 5 models
target_metadata = Base.metadata


def get_url() -> str:
    """Lấy async database URL từ settings."""
    return settings.async_db_url


def run_migrations_offline() -> None:
    """Chạy migration ở chế độ offline."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Thực thi migration trên database connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Tạo AsyncEngine và thực thi migrations."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Chạy migration ở chế độ online với hỗ trợ async."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Tránh xung đột nếu đang chạy bên trong một asyncio event loop hiện hành
        with concurrent.futures.ThreadPoolExecutor() as pool_executor:
            future = pool_executor.submit(asyncio.run, run_async_migrations())
            future.result()
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
