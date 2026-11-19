# Database Migrations (`infra/migrations`)

Thư mục này được sử dụng để lưu trữ các script chuyển đổi và quản lý schema cơ sở dữ liệu (Database Schema Migrations), do Backend API (`apps/api`) chịu trách nhiệm quản trị (sử dụng công cụ như Alembic với SQLAlchemy / SQLModel).

## 🗄️ Luồng vận hành đề xuất
1. Khi định nghĩa mô hình bảng mới tại `apps/api/app/models/`:
   ```bash
   cd apps/api
   alembic revision --autogenerate -m "create_initial_stock_tables"
   ```
2. Áp dụng migration lên cơ sở dữ liệu PostgreSQL:
   ```bash
   alembic upgrade head
   ```

*Hiện tại thư mục này được để trống làm khung chờ, sẵn sàng khi bắt đầu phát triển tầng ORM/Database.*

## Remove user risk profile (004)

Deploy API and Web together. Back up PostgreSQL before applying this migration.
Stop the old API, run `uv run alembic upgrade head` from `apps/api` using the
intended database settings, then start the updated API and Web. The API Docker
entrypoint also applies migrations before starting Uvicorn.

Migration 004 permanently removes saved risk preferences, preserving users,
roles and related records. For rollback, stop the new API, run
`uv run alembic downgrade 003_refresh_sessions`, then start the old application.
Downgrade restores the column with balanced values; original choices require
the backup to recover.
