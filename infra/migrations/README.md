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

## Account verification and recovery (005)

Migration `005_account_flows` follows `004_remove_user_risk_profile`. It adds
`email_verified_at` (NULL for existing users), `auth_version` (0), account action
tokens and persistent rate limits. Passwords, roles and investment data are preserved.
No risk profile or Google identity fields are introduced.

Back up the intended database, check `uv run alembic current` from `apps/api`,
then run `uv run alembic upgrade head` before deploying the updated API and Web.
Downgrade to 004 drops verification state and recovery tokens; do not run the old
API after password resets, because it cannot enforce the new auth_version revocations.

### Gmail SMTP

1. Enable Google two-step verification and generate an App Password for the sender
   (if unavailable, check the account's Google security policy).
2. Set SMTP_HOST=smtp.gmail.com, SMTP_PORT=587, SMTP_USERNAME to the sender address,
   SMTP_PASSWORD to the App Password, SMTP_FROM_EMAIL to that same sender.
3. Set FRONTEND_PUBLIC_URL to the actual Web origin (http://localhost:3000 for
   development; HTTPS required with ENVIRONMENT=production). URL paths may not
   contain credentials, query parameters or fragments.
4. Keep credentials in untracked .env/environment variables. Never use NEXT_PUBLIC_
   for SMTP secrets. Compose forwards these variables to the API only.
5. Restart API, register a disposable account, inspect the inbox/spam folder,
   confirm verification, then request a password reset and log in with the new password.

Delivery uses STARTTLS with certificate verification and a 10-second timeout.
Background tasks run after commit, without a durable queue: process termination
may lose a pending message; request another link. Delivery failure never deletes
an account. Logs report success/failure and purpose without addresses or tokens.
Monitor `Account mail delivery failed` and HTTP 429 responses. SMTP credentials
are not necessary for mocked automated tests, but real-mail acceptance remains
pending until the sender is configured. No Google OAuth setup is needed.

Recovery links contain a URL fragment. Reloading after the client removes that
fragment requires reopening the original email link. Links expire after 30 minutes
(reset) or 24 hours (verification); reissuing invalidates the old link.

### Isolated PostgreSQL tests

Run `uv run pytest tests/test_account_flows.py` from apps/api. Optionally set
ACCOUNT_TEST_DATABASE_URL to a **disposable** PostgreSQL database to include
independent-transaction concurrency tests. The fixture creates and drops tables;
never point it at development or production data.
