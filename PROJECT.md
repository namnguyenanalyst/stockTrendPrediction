# Project: Stock Trend Prediction & Quantitative Platform Production Upgrade

## Architecture
The platform is upgraded from a single-user demo to a production-grade, multi-user quantitative investment platform.
- **Tiers & Boundaries**:
  - `apps/api`: Asynchronous FastAPI backend (Python 3.11+, Pydantic V2, SQLAlchemy 2.0 Async Session, Alembic migrations, Bcrypt password hashing, JWT Access & Refresh Token authentication, User personalization CRUD, and 100% preserved quantitative ML pipelines).
  - `apps/web`: Next.js 16 (App Router), React 19, Tailwind CSS frontend with dedicated route groups `(auth)` and `(dashboard)`, Next.js `middleware.ts` route protection, `AuthContext` / `useAuth` hook, and personalization UI (database-backed watchlists, strategy presets, and backtest history logs).
  - `apps/ml`: Core machine learning and quantitative finance engine (`vn-stock`), maintaining Vietnam market microstructure (0.15% fee, 0.10% tax, T+2 settlement cycle, lot size 100, Stop Loss / Take Profit / Trailing Stop risk management).
  - `infra`: Multi-container Docker Compose infrastructure with 3 healthy services (`vn_stock_db` [PostgreSQL 16 Alpine], `vn_stock_api` [FastAPI with automatic migrations], `vn_stock_web` [Next.js standalone build]).
  - `tests/e2e`: Opaque-box requirement-driven E2E test harness exercising all API and Web contracts across 4 systematic tiers.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Core Database Models | 5 core SQLAlchemy models (`users`, `user_watchlists`, `strategy_presets`, `backtest_histories`, `prediction_audits`) with UUID PKs, JSONB, FKs and cascade delete | M1 | ORIGINAL_REQUEST R2 |
| 2 | Async Database Session & Engine | SQLAlchemy 2.0 async engine (`postgresql+asyncpg://`), connection pool, session dependency, SQLite async compatibility for fast testing | M1 | ORIGINAL_REQUEST R1, R2 |
| 3 | Alembic Migrations System | Initial async Alembic setup and migration version generating all 5 tables automatically upon startup without seed data | M1 | ORIGINAL_REQUEST R2 |
| 4 | Password Hashing & JWT Security | Bcrypt password hashing, short-lived JWT Access Token (Bearer header), HTTP-only Refresh Token cookie, configuration loading via `.env` | M2 | ORIGINAL_REQUEST R1 |
| 5 | Auth Router (`/api/v1/auth`) | Endpoints: `POST /register`, `POST /login`, `POST /refresh`, `GET /me` | M2 | ORIGINAL_REQUEST R1 |
| 6 | Personalization CRUD Endpoints | Endpoints: `/api/v1/user/watchlists`, `/api/v1/user/presets`, `/api/v1/user/backtests` with strict tenant isolation by `current_user.id` | M2 | ORIGINAL_REQUEST R1 |
| 7 | Preservation of Quant & ML Logic | 100% preservation of T+2 cycle, 0.15% fee, 0.10% tax, lot size 100, and ML inference pipelines; backward-compatible routing | M2 | ORIGINAL_REQUEST R1 |
| 8 | Frontend Auth UI & State Management | Route group `(auth)` with `/login` and `/register`, `AuthContext`, `useAuth` hook, UserMenu in top header | M3 | ORIGINAL_REQUEST R3 |
| 9 | Protected Routes Middleware | Next.js `middleware.ts` guarding `/dashboard` and `/backtest`, redirecting unauthenticated users to `/login`, and authenticated users away from `/login` | M3 | ORIGINAL_REQUEST R3 |
| 10 | Frontend Personalization Integration | Stock watchlist pinning synced to DB, "Save this strategy" modal in Backtest saved to DB presets, backtest history log with equity curve viewing | M3 | ORIGINAL_REQUEST R3 |
| 11 | Docker Compose Infrastructure | `infra/docker-compose.yml` with `vn_stock_db`, `vn_stock_api`, `vn_stock_web`, healthchecks, volumes, proper build contexts | M4 | ORIGINAL_REQUEST R4 |
| 12 | Optimized Container Dockerfiles | `apps/api/Dockerfile` on Python 3.11 with automatic `alembic upgrade head`, `apps/web/Dockerfile` with Next.js Standalone build (`output: "standalone"`) | M4 | ORIGINAL_REQUEST R4 |
| 13 | Environment Configuration | Comprehensive `.env.example` covering DB credentials, JWT secrets, CORS origins, API URLs | M4 | ORIGINAL_REQUEST R4 |
| 14 | Backend Unit & Integration Tests | Pytest test suite in `apps/api/tests/` verifying db models, migrations, auth flow, user personalization, and cross-tenant isolation | E2E & M2 | ORIGINAL_REQUEST Verification |
| 15 | Frontend Unit & Integration Tests | Vitest test suite in `apps/web/` verifying auth client, personalization client, storage migration, and middleware logic | E2E & M3 | ORIGINAL_REQUEST Verification |
| 16 | Opaque-Box E2E Testing Suite | Requirements-driven 4-tier test suite (Tier 1 Feature, Tier 2 Boundary, Tier 3 Cross-feature, Tier 4 Real-world) producing `TEST_READY.md` | E2E Track | ORIGINAL_REQUEST Acceptance |
| 17 | Final E2E Verification & Hardening | 100% pass of E2E test suite followed by Tier 5 adversarial coverage hardening | Final Milestone | ORIGINAL_REQUEST Acceptance |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track | Design and construct opaque-box test suite (Tiers 1-4) covering all features independently; publish `TEST_READY.md` | none | DONE |
| M1 | Database Schema & Migrations | SQLAlchemy 2.0 Async models, session factory, Alembic async migration for all 5 tables | none | DONE |
| M2 | Backend Auth & Personalization API | Bcrypt security, JWT Access/Refresh tokens, `/api/v1/auth`, `/api/v1/user/*` CRUD with tenant isolation, quant logic preservation | M1 | DONE |
| M3 | Frontend Auth UI & Personalization | Next.js 16 `(auth)` routes, `middleware.ts`, `AuthContext`, watchlist/preset/backtest history UI integration | M2 | DONE |
| M4 | DevOps, Docker & 1-Click Deployment | Update `infra/docker-compose.yml`, optimize `apps/api/Dockerfile` & `apps/web/Dockerfile` (standalone), provide `.env.example` | M1, M2, M3 | DONE |
| M5 | Final Verification & Hardening | Phase 1 (Tiers 1-4) and Phase 2 (Tier 5 adversarial hardening) complete; 530/530 tests passed, 0 lint errors, clean forensic audit, gate approved | M4, E2E | DONE |

## Interface Contracts

### Backend ↔ Database
- Dialects supported: `postgresql+asyncpg://` for production, `sqlite+aiosqlite://` for lightning test isolation.
- Session dependency: `get_db() -> AsyncGenerator[AsyncSession, None]`.
- Tables:
  - `users`: `id` (UUID PK), `email` (str, unique, index), `hashed_password` (str), `full_name` (str, nullable), `role` (`trader` | `admin`), `risk_profile` (`conservative` | `balanced` | `aggressive`), `is_active` (bool), `created_at`, `updated_at`.
  - `user_watchlists`: `id` (UUID PK), `user_id` (UUID FK -> users.id, cascade), `name` (str), `symbols` (JSONB list of strings), `created_at`, `updated_at`.
  - `strategy_presets`: `id` (UUID PK), `user_id` (UUID FK -> users.id, cascade), `name` (str), `description` (str, nullable), `parameters` (JSONB dict), `created_at`, `updated_at`.
  - `backtest_histories`: `id` (UUID PK), `user_id` (UUID FK -> users.id, cascade), `symbol` (str, index), `strategy_name` (str), `strategy_type` (str), `start_date` (date), `end_date` (date), `initial_capital` (float), `total_return` (float), `sharpe_ratio` (float), `max_drawdown` (float), `win_rate` (float), `equity_curve` (JSONB list), `executed_at` (datetime).
  - `prediction_audits`: `id` (UUID PK), `symbol` (str, index), `prediction_date` (date), `target_date` (date, T+3), `predicted_signal` (int: 0, 1, 2), `predicted_probabilities` (JSONB dict), `actual_return` (float, nullable), `is_correct` (bool, nullable).

### Frontend ↔ Backend REST API
- Authentication Header: `Authorization: Bearer <access_token>`
- Refresh Token Cookie: `refresh_token=<token>; HttpOnly; Path=/api/v1/auth; SameSite=Lax`
- Endpoints:
  - `POST /api/v1/auth/register`: Request `{ email, password, full_name?, risk_profile? }` -> Response `{ id, email, full_name, role, risk_profile, is_active, created_at }`
  - `POST /api/v1/auth/login`: Request `{ email, password }` -> Response `{ access_token, token_type: "bearer", user: {...} }` + Set-Cookie `refresh_token`
  - `POST /api/v1/auth/refresh`: Request (reads cookie `refresh_token` or body) -> Response `{ access_token, token_type: "bearer" }`
  - `GET /api/v1/auth/me`: Requires Bearer token -> Response `{ id, email, full_name, role, risk_profile, is_active }`
  - `GET /api/v1/user/watchlists`: -> Response `list[WatchlistOut]`
  - `POST /api/v1/user/watchlists`: Request `{ name, symbols }` -> Response `WatchlistOut`
  - `DELETE /api/v1/user/watchlists/{watchlist_id}`: -> Response `204 No Content`
  - `GET /api/v1/user/presets`: -> Response `list[PresetOut]`
  - `POST /api/v1/user/presets`: Request `{ name, description?, parameters }` -> Response `PresetOut`
  - `DELETE /api/v1/user/presets/{preset_id}`: -> Response `204 No Content`
  - `GET /api/v1/user/backtests`: -> Response `list[BacktestHistoryOut]`
  - `POST /api/v1/user/backtests`: Request `BacktestHistoryCreate` -> Response `BacktestHistoryOut`
  - Backward-compatible endpoints preserved: `/api/stocks/*`, `/api/predict/*`, `/api/backtest/*`.

## Code Layout
- `apps/api/`:
  - `app/core/`: `config.py` (settings, secrets, DB URLs), `security.py` (Bcrypt, JWT encode/decode), `deps.py` (`get_db`, `get_current_user`, `get_current_active_user`)
  - `app/db/`: `base.py` (DeclarativeBase), `session.py` (async engine, sessionmaker), `models/` (`__init__.py`, `user.py`, `watchlist.py`, `preset.py`, `backtest.py`, `audit.py`)
  - `app/schemas/`: `auth.py`, `user.py`, `watchlist.py`, `preset.py`, `backtest.py`
  - `app/routers/`: `auth.py`, `user.py`, `stocks.py`, `prediction.py`, `backtest.py`
  - `alembic/`: `env.py`, `script.py.mako`, `versions/`
  - `tests/`: `conftest.py`, `test_db_models.py`, `test_auth.py`, `test_user_personalization.py`, `test_api.py`, `test_services.py`
  - `Dockerfile`, `pyproject.toml`
- `apps/web/`:
  - `src/app/(auth)/`: `login/page.tsx`, `register/page.tsx`, `layout.tsx`
  - `src/app/(dashboard)/`: `dashboard/page.tsx`, `backtest/page.tsx`, `layout.tsx`
  - `src/app/page.tsx`: Root redirect to `/dashboard`
  - `src/middleware.ts`: Next.js edge route protection
  - `src/context/AuthContext.tsx`: React 19 Auth provider & `useAuth` hook
  - `src/lib/api.ts`: API client with auth interceptor and personalization functions
  - `src/components/`: `TopHeader.tsx` (UserMenu), `MarketOverviewTab.tsx` (Watchlist pinning), `BacktestSimulatorTab.tsx` (Save strategy & backtest history log)
  - `next.config.ts` (`output: "standalone"`), `Dockerfile`
- `infra/`:
  - `docker-compose.yml`: 3 services (`vn_stock_db`, `vn_stock_api`, `vn_stock_web`)
  - `.env.example`: Full production environment template
- `tests/e2e/`:
  - Test runner and test suites for Tiers 1-4
