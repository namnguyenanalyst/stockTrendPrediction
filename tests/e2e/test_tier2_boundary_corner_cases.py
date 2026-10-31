"""Tier 2: Boundary & Corner Cases E2E Tests (>= 5 tests per feature group).

Exhaustively exercises edge conditions, malicious inputs, boundary values, and error flows:
1. Registration boundaries & error handling (duplicate, malformed, too short, SQLi)
2. Authentication & Token boundaries (401 on bad password, missing header, tampered token, expired token)
3. Resource deletion & non-existent ID boundaries (404 on unknown ID, format errors, double deletion)
4. Input validation & schema guards for Personalization (422 on empty name, empty symbols, bad JSONB)
5. Quantitative & Market Parameter boundaries (capital <= 0, inverted dates, negative limits)
"""

import uuid
import pytest
from tests.e2e.client import E2EClient
from tests.e2e.mock_server import create_jwt_token


# =============================================================================
# Group 1: Registration Boundaries & Validation
# =============================================================================

def test_register_duplicate_email_returns_400(client: E2EClient):
    """Attempting to register with an already registered email returns HTTP 400."""
    uid = uuid.uuid4().hex[:8]
    email = f"dup_{uid}@quant.vn"
    pwd = "ValidPassword@123"

    res1 = client.register(email=email, password=pwd)
    assert res1.status_code in (200, 201)

    res2 = client.register(email=email, password=pwd)
    assert res2.status_code == 400
    assert "already registered" in res2.text.lower()


def test_register_malformed_email_missing_at_returns_422(client: E2EClient):
    """Registering with an email missing '@' returns HTTP 422 Unprocessable Entity."""
    res = client.register(email="invalid_email_format.vn", password="ValidPassword@123")
    assert res.status_code == 422


def test_register_malformed_email_missing_domain_returns_422(client: E2EClient):
    """Registering with an email missing top-level domain returns HTTP 422."""
    res = client.register(email="user@nodomain", password="ValidPassword@123")
    assert res.status_code == 422


def test_register_password_under_minimum_length_returns_422(client: E2EClient):
    """Registering with password < 8 characters returns HTTP 422."""
    res = client.register(email="short_pwd@quant.vn", password="short")
    assert res.status_code == 422


def test_register_invalid_risk_profile_returns_422(client: E2EClient):
    """Registering with an unsupported risk profile returns HTTP 422."""
    uid = uuid.uuid4().hex[:8]
    res = client.register(
        email=f"bad_risk_{uid}@quant.vn",
        password="ValidPassword@123",
        risk_profile="reckless_gambler",
    )
    assert res.status_code == 422


def test_register_sql_injection_payload_sanitized(client: E2EClient):
    """Registering with SQL injection characters is safely escaped and does not crash."""
    uid = uuid.uuid4().hex[:8]
    email = f"sqli_{uid}@quant.vn"
    name_payload = "Trader' OR '1'='1'; DROP TABLE users;--"
    res = client.register(email=email, password="ValidPassword@123", full_name=name_payload)
    assert res.status_code in (200, 201)
    assert res.json()["full_name"] == name_payload


# =============================================================================
# Group 2: Authentication & Token Boundaries
# =============================================================================

def test_login_nonexistent_email_returns_401(client: E2EClient):
    """Logging in with a non-existent email returns HTTP 401 Unauthorized."""
    res = client.login(email="ghost_user_99999@quant.vn", password="SomePassword@123")
    assert res.status_code == 401
    assert "incorrect" in res.text.lower() or "unauthorized" in res.text.lower()


def test_login_incorrect_password_returns_401(client: E2EClient):
    """Logging in with the wrong password returns HTTP 401."""
    uid = uuid.uuid4().hex[:8]
    email = f"wrong_pwd_{uid}@quant.vn"
    client.register(email=email, password="CorrectPassword@123")

    res = client.login(email=email, password="WrongPassword@999")
    assert res.status_code == 401


def test_me_without_auth_header_returns_401(client: E2EClient):
    """Accessing protected endpoint /api/v1/auth/me without token returns HTTP 401."""
    client.clear_token()
    res = client.me()
    assert res.status_code == 401


def test_me_with_malformed_bearer_header_returns_401(client: E2EClient):
    """Accessing /api/v1/auth/me with random garbage token returns HTTP 401."""
    client.set_token("gibberish-not-a-valid-token")
    res = client.me()
    assert res.status_code == 401


def test_me_with_tampered_signature_returns_401(client: E2EClient):
    """Accessing /api/v1/auth/me with a modified payload/signature returns HTTP 401."""
    valid_token = create_jwt_token({"sub": "random-uuid", "email": "tampered@quant.vn"})
    tampered_token = valid_token[:-5] + "XXXXX"
    client.set_token(tampered_token)
    res = client.me()
    assert res.status_code == 401


def test_me_with_expired_jwt_token_returns_401(client: E2EClient):
    """Accessing /api/v1/auth/me with an expired JWT returns HTTP 401."""
    expired_token = create_jwt_token({"sub": "user-uuid"}, expires_in_seconds=-10)
    client.set_token(expired_token)
    res = client.me()
    assert res.status_code == 401


def test_refresh_missing_cookie_and_body_returns_401(client: E2EClient):
    """Calling /api/v1/auth/refresh without cookie or body returns HTTP 401."""
    client.clear_cookies()
    res = client.post("/api/v1/auth/refresh", json={})
    assert res.status_code == 401


def test_refresh_invalid_token_returns_401(client: E2EClient):
    """Calling /api/v1/auth/refresh with invalid token returns HTTP 401."""
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": "corrupt-refresh-token"})
    assert res.status_code == 401


# =============================================================================
# Group 3: Resource Deletion & Non-Existent ID Boundaries
# =============================================================================

def test_delete_watchlist_nonexistent_uuid_returns_404(registered_user, client: E2EClient):
    """Deleting a non-existent watchlist UUID returns HTTP 404 Not Found."""
    fake_id = str(uuid.uuid4())
    res = client.delete_watchlist(fake_id)
    assert res.status_code == 404


def test_delete_preset_nonexistent_uuid_returns_404(registered_user, client: E2EClient):
    """Deleting a non-existent preset UUID returns HTTP 404 Not Found."""
    fake_id = str(uuid.uuid4())
    res = client.delete_preset(fake_id)
    assert res.status_code == 404


def test_delete_watchlist_invalid_uuid_format_returns_404_or_422(registered_user, client: E2EClient):
    """Deleting a watchlist with invalid non-UUID format returns HTTP 404 or 422."""
    res = client.delete_watchlist("not-a-valid-uuid-identifier")
    assert res.status_code in (404, 422)


def test_delete_preset_invalid_uuid_format_returns_404_or_422(registered_user, client: E2EClient):
    """Deleting a preset with invalid non-UUID format returns HTTP 404 or 422."""
    res = client.delete_preset("not-a-valid-uuid-identifier")
    assert res.status_code in (404, 422)


def test_double_delete_same_watchlist_returns_404(registered_user, client: E2EClient):
    """Deleting the same watchlist twice returns 204 on first and 404 on second."""
    create_res = client.create_watchlist(name="DoubleDelete", symbols=["HPG"])
    wid = create_res.json()["id"]

    del1 = client.delete_watchlist(wid)
    assert del1.status_code == 204

    del2 = client.delete_watchlist(wid)
    assert del2.status_code == 404


# =============================================================================
# Group 4: Input Validation & Malformed Payloads for Personalization
# =============================================================================

def test_create_watchlist_empty_name_returns_422(registered_user, client: E2EClient):
    """Creating a watchlist with an empty name returns HTTP 422."""
    res = client.create_watchlist(name="", symbols=["VIC"])
    assert res.status_code == 422


def test_create_watchlist_empty_symbols_list_returns_422(registered_user, client: E2EClient):
    """Creating a watchlist with an empty symbols list returns HTTP 422."""
    res = client.create_watchlist(name="Empty Watchlist", symbols=[])
    assert res.status_code == 422


def test_create_watchlist_non_list_symbols_returns_422(registered_user, client: E2EClient):
    """Creating a watchlist with symbols as string instead of list returns HTTP 422."""
    res = client.post("/api/v1/user/watchlists", json={"name": "BadSymbols", "symbols": "HPG"})
    assert res.status_code == 422


def test_create_preset_missing_parameters_returns_422(registered_user, client: E2EClient):
    """Creating a strategy preset without the required parameters dict returns HTTP 422."""
    res = client.post("/api/v1/user/presets", json={"name": "NoParams"})
    assert res.status_code == 422


def test_create_preset_non_dict_parameters_returns_422(registered_user, client: E2EClient):
    """Creating a strategy preset with parameters as integer returns HTTP 422."""
    res = client.post("/api/v1/user/presets", json={"name": "IntParams", "parameters": 12345})
    assert res.status_code == 422


def test_save_backtest_missing_required_metrics_returns_422(registered_user, client: E2EClient):
    """Saving backtest history without required fields returns HTTP 422."""
    res = client.post("/api/v1/user/backtests", json={"symbol": "HPG"})
    assert res.status_code == 422


# =============================================================================
# Group 5: Quantitative & Market Parameter Boundaries
# =============================================================================

def test_backtest_run_negative_initial_capital_returns_422(client: E2EClient):
    """Running backtest simulation with negative initial capital returns HTTP 422."""
    payload = {
        "symbol": "HPG",
        "strategy_type": "macd_crossover",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": -100_000.0,
    }
    res = client.post("/api/backtest/run", json=payload)
    assert res.status_code == 422


def test_backtest_run_zero_initial_capital_returns_422(client: E2EClient):
    """Running backtest simulation with zero initial capital returns HTTP 422."""
    payload = {
        "symbol": "HPG",
        "strategy_type": "macd_crossover",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 0.0,
    }
    res = client.post("/api/backtest/run", json=payload)
    assert res.status_code == 422


def test_backtest_run_inverted_dates_returns_400(client: E2EClient):
    """Running backtest with start_date after end_date returns HTTP 400."""
    payload = {
        "symbol": "HPG",
        "strategy_type": "macd_crossover",
        "start_date": "2023-12-31",
        "end_date": "2023-01-01",
        "initial_capital": 100_000_000.0,
    }
    res = client.post("/api/backtest/run", json=payload)
    assert res.status_code in (400, 422)


def test_stocks_history_negative_limit_returns_422(client: E2EClient):
    """Querying stock history with negative limit returns HTTP 422."""
    res = client.get("/api/stocks/history?symbol=VIC&limit=-5")
    assert res.status_code == 422


def test_predict_direction_unsupported_symbol_returns_404_or_400(client: E2EClient):
    """Predicting direction for an unknown ticker returns HTTP 404 or 400."""
    res = client.post("/api/predict/direction", json={"symbol": "NONEXISTENT_TICKER_XYZ"})
    assert res.status_code in (400, 404)
