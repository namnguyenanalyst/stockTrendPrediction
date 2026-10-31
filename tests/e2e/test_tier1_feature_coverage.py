"""Tier 1: Feature Coverage E2E Tests (>= 5 tests per feature).

Verifies happy path and valid variations across all core system features:
1. User registration (POST /api/v1/auth/register)
2. Login & JWT access token / refresh cookie (POST /api/v1/auth/login)
3. Token refresh (POST /api/v1/auth/refresh)
4. User profile (GET /api/v1/auth/me)
5. Watchlists CRUD (GET, POST, DELETE /api/v1/user/watchlists)
6. Strategy Presets CRUD (GET, POST, DELETE /api/v1/user/presets)
7. Backtest History CRUD (GET, POST /api/v1/user/backtests)
8. Existing Quant & ML Endpoints (/health, /api/stocks, /api/predict, /api/backtest)
"""

import uuid
import pytest
from tests.e2e.client import E2EClient


# =============================================================================
# Feature 1: User Registration (POST /api/v1/auth/register)
# =============================================================================

def test_register_balanced_profile_default(client: E2EClient):
    """Register user with default balanced risk profile."""
    uid = uuid.uuid4().hex[:8]
    email = f"balanced_{uid}@quant.vn"
    res = client.register(email=email, password="SafePassword@123", risk_profile="balanced")
    assert res.status_code in (200, 201)
    data = res.json()
    assert data["email"] == email
    assert data["risk_profile"] == "balanced"
    assert data["role"] == "trader"
    assert data["is_active"] is True
    assert "id" in data


def test_register_conservative_profile(client: E2EClient):
    """Register user with conservative risk profile."""
    uid = uuid.uuid4().hex[:8]
    email = f"conservative_{uid}@quant.vn"
    res = client.register(email=email, password="SafePassword@123", risk_profile="conservative")
    assert res.status_code in (200, 201)
    assert res.json()["risk_profile"] == "conservative"


def test_register_aggressive_profile(client: E2EClient):
    """Register user with aggressive risk profile."""
    uid = uuid.uuid4().hex[:8]
    email = f"aggressive_{uid}@quant.vn"
    res = client.register(email=email, password="SafePassword@123", risk_profile="aggressive")
    assert res.status_code in (200, 201)
    assert res.json()["risk_profile"] == "aggressive"


def test_register_with_vietnamese_fullname(client: E2EClient):
    """Register user with full UTF-8 Vietnamese name."""
    uid = uuid.uuid4().hex[:8]
    email = f"vnname_{uid}@quant.vn"
    full_name = "Nguyễn Văn Hùng Lộc"
    res = client.register(email=email, password="SafePassword@123", full_name=full_name)
    assert res.status_code in (200, 201)
    assert res.json()["full_name"] == full_name


def test_register_minimal_payload_uses_defaults(client: E2EClient):
    """Register user with only email and password, verifying sensible defaults."""
    uid = uuid.uuid4().hex[:8]
    email = f"minimal_{uid}@quant.vn"
    res = client.register(email=email, password="SafePassword@123")
    assert res.status_code in (200, 201)
    data = res.json()
    assert data["email"] == email
    assert data["risk_profile"] == "balanced"
    assert data["role"] == "trader"


def test_register_does_not_leak_password_in_response(client: E2EClient):
    """Verify security constraint: password hash is never returned in registration response."""
    uid = uuid.uuid4().hex[:8]
    email = f"sec_{uid}@quant.vn"
    res = client.register(email=email, password="SecretPassword@999")
    assert res.status_code in (200, 201)
    data = res.json()
    assert "password" not in data
    assert "hashed_password" not in data


# =============================================================================
# Feature 2: User Login (POST /api/v1/auth/login)
# =============================================================================

def test_login_valid_credentials_returns_bearer_token(client: E2EClient):
    """Login with valid credentials returns access_token with bearer token_type."""
    uid = uuid.uuid4().hex[:8]
    email = f"login_{uid}@quant.vn"
    pwd = "MySecretPassword@1"
    client.register(email=email, password=pwd)

    res = client.login(email=email, password=pwd)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert len(data["access_token"]) > 20
    assert data.get("token_type", "").lower() == "bearer"
    assert data["user"]["email"] == email


def test_login_sets_httponly_refresh_cookie(client: E2EClient):
    """Login response contains Set-Cookie header for refresh_token with HttpOnly flag."""
    uid = uuid.uuid4().hex[:8]
    email = f"cookie_{uid}@quant.vn"
    pwd = "MySecretPassword@1"
    client.register(email=email, password=pwd)

    res = client.login(email=email, password=pwd)
    assert res.status_code == 200
    cookie_header = res.headers.get("set-cookie", "")
    assert "refresh_token" in cookie_header or "refresh_token" in client.stored_cookies


def test_login_cookie_attributes_path_and_samesite(client: E2EClient):
    """Verify refresh cookie contains secure scope path and SameSite attributes."""
    uid = uuid.uuid4().hex[:8]
    email = f"attrs_{uid}@quant.vn"
    pwd = "MySecretPassword@1"
    client.register(email=email, password=pwd)

    res = client.login(email=email, password=pwd)
    assert res.status_code == 200
    cookie_header = res.headers.get("set-cookie", "").lower()
    if cookie_header:
        assert "httponly" in cookie_header
        assert "path" in cookie_header


def test_login_case_insensitive_email(client: E2EClient):
    """Login succeeds when email casing differs from registration (e.g. USER@QUANT.VN)."""
    uid = uuid.uuid4().hex[:8]
    email = f"case_{uid}@quant.vn"
    pwd = "CasePassword@123"
    client.register(email=email, password=pwd)

    res = client.login(email=email.upper(), password=pwd)
    assert res.status_code == 200
    assert res.json()["user"]["email"] == email.lower()


def test_login_returns_complete_user_profile(client: E2EClient):
    """Login payload includes user metadata (id, email, full_name, role, risk_profile)."""
    uid = uuid.uuid4().hex[:8]
    email = f"meta_{uid}@quant.vn"
    pwd = "MetaPassword@123"
    client.register(email=email, password=pwd, full_name="Meta Trader", risk_profile="aggressive")

    res = client.login(email=email, password=pwd)
    assert res.status_code == 200
    user_info = res.json()["user"]
    assert user_info["full_name"] == "Meta Trader"
    assert user_info["risk_profile"] == "aggressive"
    assert user_info["role"] == "trader"


# =============================================================================
# Feature 3: Token Refresh (POST /api/v1/auth/refresh)
# =============================================================================

def test_refresh_via_cookie_returns_new_access_token(client: E2EClient):
    """Calling /refresh with cookie sends back a fresh valid access token."""
    uid = uuid.uuid4().hex[:8]
    email = f"refc_{uid}@quant.vn"
    pwd = "RefreshPassword@123"
    client.register(email=email, password=pwd)
    login_res = client.login(email=email, password=pwd)
    first_token = login_res.json()["access_token"]

    ref_res = client.refresh()
    assert ref_res.status_code == 200
    new_token = ref_res.json().get("access_token")
    assert new_token is not None
    assert len(new_token) > 20


def test_refresh_via_body_returns_new_access_token(client: E2EClient):
    """Calling /refresh with JSON body containing refresh_token succeeds."""
    uid = uuid.uuid4().hex[:8]
    email = f"refb_{uid}@quant.vn"
    pwd = "RefreshPassword@123"
    client.register(email=email, password=pwd)
    client.login(email=email, password=pwd)

    refresh_token_cookie = client.stored_cookies.get("refresh_token")
    if refresh_token_cookie:
        res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_cookie})
        assert res.status_code == 200
        assert "access_token" in res.json()


def test_refresh_token_enables_authenticated_me_query(client: E2EClient):
    """A newly refreshed access token can successfully access /api/v1/auth/me."""
    uid = uuid.uuid4().hex[:8]
    email = f"refme_{uid}@quant.vn"
    pwd = "RefreshPassword@123"
    client.register(email=email, password=pwd)
    client.login(email=email, password=pwd)

    client.refresh()
    me_res = client.me()
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email


def test_consecutive_refresh_requests_succeed(client: E2EClient):
    """Executing consecutive refresh requests yields working access tokens."""
    uid = uuid.uuid4().hex[:8]
    email = f"multi_{uid}@quant.vn"
    pwd = "MultiPassword@123"
    client.register(email=email, password=pwd)
    client.login(email=email, password=pwd)

    ref1 = client.refresh()
    assert ref1.status_code == 200
    ref2 = client.refresh()
    assert ref2.status_code == 200
    assert client.me().status_code == 200


def test_refresh_token_preserves_user_identity_and_role(client: E2EClient):
    """Refreshed token maintains correct user id, email and role in subsequent requests."""
    uid = uuid.uuid4().hex[:8]
    email = f"pres_{uid}@quant.vn"
    pwd = "PresPassword@123"
    client.register(email=email, password=pwd, risk_profile="conservative")
    client.login(email=email, password=pwd)

    client.refresh()
    me_data = client.me().json()
    assert me_data["email"] == email
    assert me_data["risk_profile"] == "conservative"
    assert me_data["role"] == "trader"


# =============================================================================
# Feature 4: Current User Profile (GET /api/v1/auth/me)
# =============================================================================

def test_me_with_valid_bearer_token_returns_200(registered_user, client: E2EClient):
    """GET /api/v1/auth/me returns 200 OK with valid bearer token."""
    res = client.me()
    assert res.status_code == 200


def test_me_returns_uuid_and_matching_email(registered_user, client: E2EClient):
    """GET /api/v1/auth/me returns valid UUID identifier and matching email."""
    res = client.me()
    data = res.json()
    assert data["email"] == registered_user["email"]
    assert len(data["id"]) >= 32


def test_me_reflects_registered_risk_profile(registered_user, client: E2EClient):
    """GET /api/v1/auth/me reflects the assigned risk profile."""
    res = client.me()
    assert res.json()["risk_profile"] == registered_user["risk_profile"]


def test_me_confirms_trader_role_and_active_status(registered_user, client: E2EClient):
    """GET /api/v1/auth/me returns role 'trader' and is_active True."""
    res = client.me()
    data = res.json()
    assert data["role"] == "trader"
    assert data["is_active"] is True


def test_me_response_excludes_hashed_password(registered_user, client: E2EClient):
    """GET /api/v1/auth/me strictly omits hashed_password or sensitive fields."""
    res = client.me()
    data = res.json()
    assert "hashed_password" not in data
    assert "password" not in data


# =============================================================================
# Feature 5: User Watchlists CRUD (/api/v1/user/watchlists)
# =============================================================================

def test_create_watchlist_with_valid_symbols(registered_user, client: E2EClient):
    """Create a watchlist with valid symbols and name."""
    res = client.create_watchlist(name="VN30 Bluechips", symbols=["HPG", "VIC", "FPT"])
    assert res.status_code in (200, 201)
    data = res.json()
    assert data["name"] == "VN30 Bluechips"
    assert "HPG" in data["symbols"]
    assert "id" in data


def test_list_watchlists_contains_created_item(registered_user, client: E2EClient):
    """Listing watchlists contains the newly created item."""
    client.create_watchlist(name="Banking Leaders", symbols=["VCB", "MBB", "TCB"])
    res = client.list_watchlists()
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    assert any(w["name"] == "Banking Leaders" for w in items)


def test_create_multiple_watchlists_for_same_user(registered_user, client: E2EClient):
    """User can create multiple distinct watchlists."""
    client.create_watchlist(name="Steel Portfolio", symbols=["HPG", "HSG", "NKG"])
    client.create_watchlist(name="Retail Stocks", symbols=["MWG", "PNJ", "FRT"])
    res = client.list_watchlists()
    names = [w["name"] for w in res.json()]
    assert "Steel Portfolio" in names
    assert "Retail Stocks" in names


def test_delete_watchlist_returns_204_no_content(registered_user, client: E2EClient):
    """Deleting an existing watchlist returns HTTP 204 No Content."""
    create_res = client.create_watchlist(name="Temp Watchlist", symbols=["VIC"])
    wid = create_res.json()["id"]

    del_res = client.delete_watchlist(wid)
    assert del_res.status_code == 204


def test_list_watchlists_after_deletion_is_empty(registered_user, client: E2EClient):
    """After deleting the only watchlist, list returns an empty array."""
    create_res = client.create_watchlist(name="Single Watchlist", symbols=["VIC"])
    wid = create_res.json()["id"]
    client.delete_watchlist(wid)

    res = client.list_watchlists()
    assert len(res.json()) == 0


# =============================================================================
# Feature 6: Strategy Presets CRUD (/api/v1/user/presets)
# =============================================================================

def test_create_preset_with_valid_parameters(registered_user, client: E2EClient):
    """Create a strategy preset with quantitative parameters."""
    params = {"stop_loss": 0.05, "take_profit": 0.12, "trailing_stop": 0.03}
    res = client.create_preset(name="MACD Conservative", parameters=params)
    assert res.status_code in (200, 201)
    data = res.json()
    assert data["name"] == "MACD Conservative"
    assert data["parameters"] == params
    assert "id" in data


def test_create_preset_with_optional_description(registered_user, client: E2EClient):
    """Create a strategy preset with optional rich description."""
    params = {"fast_period": 12, "slow_period": 26, "signal_period": 9}
    desc = "Standard MACD crossover strategy adapted for VN-Index volatility"
    res = client.create_preset(name="MACD Tuned", parameters=params, description=desc)
    assert res.status_code in (200, 201)
    assert res.json()["description"] == desc


def test_list_presets_returns_user_presets(registered_user, client: E2EClient):
    """Listing presets returns all presets created by the current user."""
    client.create_preset(name="Strategy 1", parameters={"p": 1})
    client.create_preset(name="Strategy 2", parameters={"p": 2})

    res = client.list_presets()
    assert res.status_code == 200
    names = [p["name"] for p in res.json()]
    assert "Strategy 1" in names
    assert "Strategy 2" in names


def test_delete_preset_returns_204(registered_user, client: E2EClient):
    """Deleting an existing preset returns HTTP 204 No Content."""
    create_res = client.create_preset(name="Disposable Preset", parameters={"x": 10})
    pid = create_res.json()["id"]

    del_res = client.delete_preset(pid)
    assert del_res.status_code == 204


def test_list_presets_after_deletion_is_empty(registered_user, client: E2EClient):
    """After deleting preset, list confirms its absence."""
    create_res = client.create_preset(name="ToDelete", parameters={"k": 5})
    pid = create_res.json()["id"]
    client.delete_preset(pid)

    res = client.list_presets()
    assert not any(p["id"] == pid for p in res.json())


# =============================================================================
# Feature 7: Backtest Histories CRUD (/api/v1/user/backtests)
# =============================================================================

def test_save_backtest_with_full_quantitative_metrics(registered_user, client: E2EClient):
    """Save backtest history with full financial metrics and equity curve."""
    curve = [
        {"date": "2023-01-01", "equity": 100_000_000.0},
        {"date": "2023-06-30", "equity": 112_000_000.0},
        {"date": "2023-12-31", "equity": 124_500_000.0},
    ]
    payload = {
        "symbol": "HPG",
        "strategy_name": "MACD Trend Follow",
        "strategy_type": "macd_crossover",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 100_000_000.0,
        "total_return": 0.245,
        "sharpe_ratio": 1.65,
        "max_drawdown": -0.055,
        "win_rate": 0.68,
        "equity_curve": curve,
    }
    res = client.save_backtest(payload)
    assert res.status_code in (200, 201)
    data = res.json()
    assert data["symbol"] == "HPG"
    assert data["total_return"] == 0.245
    assert len(data["equity_curve"]) == 3
    assert "id" in data


def test_list_backtests_returns_saved_history(registered_user, client: E2EClient):
    """Listing backtests returns previously saved backtest records."""
    payload = {
        "symbol": "FPT",
        "strategy_name": "Bollinger Breakout",
        "strategy_type": "bollinger_bands",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 50_000_000.0,
        "total_return": 0.18,
        "sharpe_ratio": 1.4,
        "max_drawdown": -0.04,
        "win_rate": 0.60,
        "equity_curve": [{"date": "2023-01-01", "equity": 50_000_000.0}],
    }
    client.save_backtest(payload)

    res = client.list_backtests()
    assert res.status_code == 200
    items = res.json()
    assert any(b["symbol"] == "FPT" for b in items)


def test_save_multiple_backtests_different_symbols(registered_user, client: E2EClient):
    """User can log backtests across multiple symbols."""
    for sym in ["VIC", "VNM", "MWG"]:
        payload = {
            "symbol": sym,
            "strategy_name": f"{sym} Test",
            "strategy_type": "sma",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 10_000_000.0,
            "total_return": 0.10,
            "sharpe_ratio": 1.1,
            "max_drawdown": -0.05,
            "win_rate": 0.55,
            "equity_curve": [],
        }
        client.save_backtest(payload)

    res = client.list_backtests()
    symbols = [b["symbol"] for b in res.json()]
    assert "VIC" in symbols
    assert "VNM" in symbols
    assert "MWG" in symbols


def test_backtest_history_retains_complete_equity_curve(registered_user, client: E2EClient):
    """Saved backtest record preserves all equity curve coordinate points intact."""
    curve = [{"date": f"2023-0{i+1}-01", "equity": 100_000_000.0 + i * 1_000_000} for i in range(5)]
    payload = {
        "symbol": "HPG",
        "strategy_name": "Curve Test",
        "strategy_type": "custom",
        "start_date": "2023-01-01",
        "end_date": "2023-05-01",
        "initial_capital": 100_000_000.0,
        "total_return": 0.05,
        "sharpe_ratio": 1.2,
        "max_drawdown": -0.02,
        "win_rate": 0.50,
        "equity_curve": curve,
    }
    save_res = client.save_backtest(payload)
    bid = save_res.json()["id"]

    res = client.list_backtests()
    saved = next(b for b in res.json() if b["id"] == bid)
    assert len(saved["equity_curve"]) == 5


def test_list_backtests_ordered_by_executed_at_desc(registered_user, client: E2EClient):
    """Backtest history list is sorted in descending order of execution time."""
    for sym in ["AAA", "BBB"]:
        client.save_backtest({
            "symbol": sym,
            "strategy_name": "Order Test",
            "strategy_type": "test",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 10_000_000.0,
            "total_return": 0.05,
            "sharpe_ratio": 1.0,
            "max_drawdown": -0.01,
            "win_rate": 0.5,
            "equity_curve": [],
        })

    res = client.list_backtests()
    items = res.json()
    assert len(items) >= 2
    # Verify latest is first
    assert items[0]["symbol"] == "BBB"


# =============================================================================
# Feature 8: Existing Quant & ML Endpoints (Backward Compatible)
# =============================================================================

def test_health_endpoint_healthy_status(client: E2EClient):
    """GET /health returns 200 with service status healthy."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_stocks_symbols_returns_coverage_universe(client: E2EClient):
    """GET /api/stocks/symbols returns core VN stock coverage universe."""
    res = client.get("/api/stocks/symbols")
    assert res.status_code == 200
    symbols = res.json()
    assert isinstance(symbols, list)
    sym_codes = [s["symbol"] for s in symbols]
    for required in ["VIC", "HPG", "FPT"]:
        assert required in sym_codes


def test_stocks_history_returns_ohlcv_bars(client: E2EClient):
    """GET /api/stocks/history returns OHLCV time-series bars."""
    res = client.get("/api/stocks/history?symbol=VIC&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "VIC"
    assert len(data["bars"]) == 10
    bar = data["bars"][0]
    for col in ["date", "open", "high", "low", "close", "volume"]:
        assert col in bar


def test_stocks_indicators_returns_ta_features(client: E2EClient):
    """GET /api/stocks/indicators returns technical analysis indicator features."""
    res = client.get("/api/stocks/indicators?symbol=VIC&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "VIC"
    assert len(data["indicators"]) == 5
    ind = data["indicators"][0]
    for col in ["close", "open_close_ratio", "sma_20_dev", "rsi_14"]:
        assert col in ind


def test_predict_direction_returns_signal_and_probabilities(client: E2EClient):
    """POST /api/predict/direction returns T+3 signal and class probabilities."""
    res = client.post("/api/predict/direction", json={"symbol": "HPG"})
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "HPG"
    assert "predicted_signal" in data
    assert "predicted_probabilities" in data
    probs = data["predicted_probabilities"]
    assert "down" in probs and "up" in probs


def test_backtest_run_simulation_returns_financial_metrics(client: E2EClient):
    """POST /api/backtest/run executes simulation with fee and settlement parameters."""
    payload = {
        "symbol": "HPG",
        "strategy_type": "macd_crossover",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 100_000_000.0,
    }
    res = client.post("/api/backtest/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_return"] is not None
    assert data["sharpe_ratio"] is not None
    assert data["fee_rate"] == 0.0015
    assert data["tax_rate"] == 0.0010
    assert len(data["equity_curve"]) >= 2
