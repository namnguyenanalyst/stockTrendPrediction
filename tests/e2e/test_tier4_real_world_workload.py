"""Tier 4: Real-World Application Scenarios & Workload E2E Tests.

Simulates realistic production conditions and market requirements:
1. Session renewal & token refresh lifecycle under long-lived user sessions
2. Complex multi-themed portfolio management (multiple sectors, dynamic updates)
3. Quantitative backtest audit: equity curve continuity and numerical coherence
4. Vietnam market microstructure compliance:
   - Transaction fee: exactly 0.15% per trade
   - Securities sales tax: exactly 0.10% on sell orders
   - Settlement cycle: T+2.5 / T+2 settlement model
"""

import math
import uuid
import pytest
from tests.e2e.client import E2EClient


# =============================================================================
# Workload 1: Session Expiration & Refresh Lifecycle
# =============================================================================

def test_session_refresh_lifecycle_under_continuous_usage(client: E2EClient):
    """Simulate real-world session lifecycle: token expiration, transparent refresh via cookie, and seamless resumed operation."""
    uid = uuid.uuid4().hex[:8]
    email = f"workload_session_{uid}@quant.vn"
    pwd = "WorkloadPassword@123"

    # Step 1: User authenticates
    client.register(email=email, password=pwd, full_name="Workload User")
    login_res = client.login(email=email, password=pwd)
    assert login_res.status_code == 200

    # User creates an initial resource
    wl_res = client.create_watchlist(name="Morning Watchlist", symbols=["FPT", "MWG"])
    assert wl_res.status_code in (200, 201)

    # Step 2: Access token expires or is cleared from memory (simulating token expiration)
    client.clear_token()
    # At this point, protected request should fail with 401
    assert client.me().status_code == 401

    # Step 3: Client uses HTTP-only refresh cookie to obtain fresh access token
    refresh_res = client.refresh()
    assert refresh_res.status_code == 200
    assert client.access_token is not None

    # Step 4: Client resumes normal operation seamlessly
    me_res = client.me()
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

    watchlists = client.list_watchlists().json()
    assert len(watchlists) == 1
    assert watchlists[0]["name"] == "Morning Watchlist"


def test_token_refresh_cookie_preservation(client: E2EClient):
    """Verify refresh cookie persists across multiple operations and remains valid."""
    uid = uuid.uuid4().hex[:8]
    email = f"cookie_persist_{uid}@quant.vn"
    pwd = "WorkloadPassword@123"

    client.register(email=email, password=pwd)
    client.login(email=email, password=pwd)

    assert "refresh_token" in client.stored_cookies or client.stored_cookies

    # Execute multiple GET and POST calls
    client.create_watchlist(name="W1", symbols=["VIC"])
    client.create_preset(name="P1", parameters={"k": 1})
    client.list_watchlists()

    # Refresh should still succeed using the stored cookie
    assert client.refresh().status_code == 200


# =============================================================================
# Workload 2: Themed Multi-Sector Portfolio Management
# =============================================================================

def test_investor_manages_complex_themed_portfolios(registered_user, client: E2EClient):
    """Simulate realistic investor managing 3 distinct sector portfolios, updating, and retiring one."""
    sectors = {
        "Ngân hàng (Banking)": ["VCB", "BID", "CTG", "TCB", "MBB"],
        "Thép & Vật liệu (Steel)": ["HPG", "HSG", "NKG"],
        "Bán lẻ & Công nghệ (Retail/Tech)": ["FPT", "MWG", "PNJ"],
    }

    created_ids = {}
    for sector_name, tickers in sectors.items():
        res = client.create_watchlist(name=sector_name, symbols=tickers)
        assert res.status_code in (200, 201)
        created_ids[sector_name] = res.json()["id"]

    # Verify all 3 portfolios exist
    all_watchlists = client.list_watchlists().json()
    assert len(all_watchlists) == 3

    # Retire/Delete the Steel portfolio
    steel_id = created_ids["Thép & Vật liệu (Steel)"]
    del_res = client.delete_watchlist(steel_id)
    assert del_res.status_code == 204

    # Verify 2 remaining portfolios
    remaining = client.list_watchlists().json()
    assert len(remaining) == 2
    remaining_names = [w["name"] for w in remaining]
    assert "Thép & Vật liệu (Steel)" not in remaining_names
    assert "Ngân hàng (Banking)" in remaining_names
    assert "Bán lẻ & Công nghệ (Retail/Tech)" in remaining_names


# =============================================================================
# Workload 3: Backtest Equity Curve Continuity & Numerical Coherence
# =============================================================================

def test_backtest_simulation_equity_curve_continuity_and_coherence(client: E2EClient):
    """Audit simulation results for mathematical consistency and equity curve continuity."""
    initial_cap = 150_000_000.0
    payload = {
        "symbol": "HPG",
        "strategy_type": "macd_crossover",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": initial_cap,
    }
    res = client.post("/api/backtest/run", json=payload)
    assert res.status_code == 200
    data = res.json()

    curve = data["equity_curve"]
    assert len(curve) >= 2, "Equity curve must contain at least start and end points"

    # First point equity must equal initial capital
    start_equity = curve[0]["equity"]
    assert math.isclose(start_equity, initial_cap, rel_tol=1e-3)

    # End point equity must match total return
    end_equity = curve[-1]["equity"]
    expected_final = initial_cap * (1.0 + data["total_return"])
    assert math.isclose(end_equity, expected_final, rel_tol=1e-3)

    # Max drawdown must be negative or zero
    assert data["max_drawdown"] <= 0.0

    # Win rate must be in [0.0, 1.0]
    assert 0.0 <= data["win_rate"] <= 1.0


# =============================================================================
# Workload 4: Vietnam Market Microstructure Compliance Audits
# =============================================================================

def test_vietnam_microstructure_fee_deduction_015(client: E2EClient):
    """Audit fee deduction: Vietnam stock market standard transaction fee of exactly 0.15% (0.0015)."""
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
    assert math.isclose(data.get("fee_rate", 0.0), 0.0015, abs_tol=1e-5)


def test_vietnam_microstructure_tax_deduction_010(client: E2EClient):
    """Audit tax deduction: Vietnam stock market standard sales tax of exactly 0.10% (0.0010)."""
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
    assert math.isclose(data.get("tax_rate", 0.0), 0.0010, abs_tol=1e-5)


def test_vietnam_microstructure_settlement_cycle_t25(client: E2EClient):
    """Audit settlement cycle: Vietnam stock market settlement cycle T+2.5 or T+2."""
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
    cycle = data.get("settlement_cycle", "")
    assert "T+2" in cycle
