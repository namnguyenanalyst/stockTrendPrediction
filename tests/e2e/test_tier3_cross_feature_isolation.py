"""Tier 3: Cross-Feature Combinations & Multi-Tenant Isolation E2E Tests.

Verifies:
1. Multi-Tenant Isolation (User A vs User B):
   - User B cannot view User A's watchlists
   - User B cannot delete User A's watchlist (returns 404 IDOR prevention)
   - User B cannot view User A's presets
   - User B cannot delete User A's preset (returns 404 IDOR prevention)
   - User B cannot view User A's backtests
   - Unauthenticated requests to all user endpoints return 401
2. Full Investor End-to-End Lifecycle:
   - Register -> Login -> Stock Survey -> Save Watchlist -> Save Preset -> Run Backtest -> Save History -> Verify -> Teardown
3. Concurrent Multi-User Portfolio Simulation:
   - User A (Conservative) and User B (Aggressive) independently configure portfolios with zero crosstalk
"""

import uuid
import pytest
from tests.e2e.client import E2EClient


# =============================================================================
# Section 1: Multi-Tenant Isolation & IDOR Prevention
# =============================================================================

def test_user_b_cannot_view_user_a_watchlists(user_a_client: E2EClient, user_b_client: E2EClient):
    """User B cannot see watchlists created by User A."""
    # User A creates a watchlist
    res_a = user_a_client.create_watchlist(name="Confidential Alpha", symbols=["VIC", "VHM"])
    assert res_a.status_code in (200, 201)
    wid_a = res_a.json()["id"]

    # User B lists watchlists
    res_b = user_b_client.list_watchlists()
    assert res_b.status_code == 200
    b_items = res_b.json()
    assert not any(w["id"] == wid_a for w in b_items)
    assert not any(w["name"] == "Confidential Alpha" for w in b_items)


def test_user_b_cannot_delete_user_a_watchlist_returns_404(
    user_a_client: E2EClient,
    user_b_client: E2EClient,
):
    """Attempt by User B to delete User A's watchlist returns 404 (IDOR Prevention)."""
    res_a = user_a_client.create_watchlist(name="Protected Watchlist", symbols=["HPG"])
    wid_a = res_a.json()["id"]

    # User B attempts to delete User A's resource
    del_res = user_b_client.delete_watchlist(wid_a)
    assert del_res.status_code == 404

    # Confirm User A's resource is still intact
    list_a = user_a_client.list_watchlists().json()
    assert any(w["id"] == wid_a for w in list_a)


def test_user_b_cannot_view_user_a_presets(user_a_client: E2EClient, user_b_client: E2EClient):
    """User B cannot view strategy presets created by User A."""
    res_a = user_a_client.create_preset(name="Alpha Proprietary Alg", parameters={"fast": 8, "slow": 21})
    pid_a = res_a.json()["id"]

    res_b = user_b_client.list_presets()
    assert res_b.status_code == 200
    assert not any(p["id"] == pid_a for p in res_b.json())


def test_user_b_cannot_delete_user_a_preset_returns_404(
    user_a_client: E2EClient,
    user_b_client: E2EClient,
):
    """Attempt by User B to delete User A's preset returns 404 (IDOR Prevention)."""
    res_a = user_a_client.create_preset(name="Untouchable Preset", parameters={"risk": 0.01})
    pid_a = res_a.json()["id"]

    del_res = user_b_client.delete_preset(pid_a)
    assert del_res.status_code == 404

    # Verify preset still belongs to User A
    list_a = user_a_client.list_presets().json()
    assert any(p["id"] == pid_a for p in list_a)


def test_user_b_cannot_view_user_a_backtest_histories(
    user_a_client: E2EClient,
    user_b_client: E2EClient,
):
    """User B cannot view backtest histories saved by User A."""
    res_a = user_a_client.save_backtest({
        "symbol": "TCB",
        "strategy_name": "Private Strat",
        "strategy_type": "quant_ai",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 500_000_000.0,
        "total_return": 0.45,
        "sharpe_ratio": 2.1,
        "max_drawdown": -0.03,
        "win_rate": 0.75,
        "equity_curve": [{"date": "2023-01-01", "equity": 500_000_000.0}],
    })
    bid_a = res_a.json()["id"]

    res_b = user_b_client.list_backtests()
    assert res_b.status_code == 200
    assert not any(b["id"] == bid_a for b in res_b.json())


def test_unauthenticated_user_denied_all_personalization_endpoints(client: E2EClient):
    """Unauthenticated client is rejected with 401 across all personalization endpoints."""
    client.clear_token()
    client.clear_cookies()

    assert client.get("/api/v1/user/watchlists").status_code == 401
    assert client.post("/api/v1/user/watchlists", json={"name": "x", "symbols": ["VIC"]}).status_code == 401
    assert client.delete(f"/api/v1/user/watchlists/{uuid.uuid4()}").status_code == 401

    assert client.get("/api/v1/user/presets").status_code == 401
    assert client.post("/api/v1/user/presets", json={"name": "x", "parameters": {}}).status_code == 401
    assert client.delete(f"/api/v1/user/presets/{uuid.uuid4()}").status_code == 401

    assert client.get("/api/v1/user/backtests").status_code == 401
    assert client.post("/api/v1/user/backtests", json={"symbol": "VIC"}).status_code == 401


# =============================================================================
# Section 2: Full Investor End-to-End Lifecycle
# =============================================================================

def test_full_investor_journey_e2e(client: E2EClient):
    """Full lifecycle: Register -> Login -> Stock Universe -> Watchlist -> Preset -> Backtest -> Save -> Verify -> Teardown."""
    uid = uuid.uuid4().hex[:8]
    email = f"journey_{uid}@quantplatform.vn"
    pwd = "JourneyPassword@2026"
    full_name = "Trần Đình Khang"

    # Step 1: Register
    reg_res = client.register(email=email, password=pwd, full_name=full_name, risk_profile="balanced")
    assert reg_res.status_code in (200, 201)

    # Step 2: Login
    login_res = client.login(email=email, password=pwd)
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Step 3: Browse stock coverage universe
    stocks_res = client.get("/api/stocks/symbols")
    assert stocks_res.status_code == 200
    available_tickers = [s["symbol"] for s in stocks_res.json()]
    assert "HPG" in available_tickers

    # Step 4: Create pinned Watchlist
    wl_res = client.create_watchlist(name="Steel Core", symbols=["HPG"])
    assert wl_res.status_code in (200, 201)
    wid = wl_res.json()["id"]

    # Step 5: Save custom Strategy Preset
    preset_params = {"fast_period": 10, "slow_period": 24, "signal_period": 8}
    preset_res = client.create_preset(
        name="HPG Custom MACD",
        parameters=preset_params,
        description="Optimized for HPG 2023 volatility",
    )
    assert preset_res.status_code in (200, 201)
    pid = preset_res.json()["id"]

    # Step 6: Execute Backtest Simulation via quantitative engine
    bt_run = client.post("/api/backtest/run", json={
        "symbol": "HPG",
        "strategy_type": "macd_crossover",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 200_000_000.0,
        "parameters": preset_params,
    })
    assert bt_run.status_code == 200
    run_data = bt_run.json()
    assert run_data["total_return"] is not None

    # Step 7: Persist simulation results into user backtest history
    save_payload = {
        "symbol": "HPG",
        "strategy_name": "HPG Custom MACD",
        "strategy_type": "macd_crossover",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": run_data["initial_capital"],
        "total_return": run_data["total_return"],
        "sharpe_ratio": run_data["sharpe_ratio"],
        "max_drawdown": run_data["max_drawdown"],
        "win_rate": run_data["win_rate"],
        "equity_curve": run_data["equity_curve"],
    }
    save_res = client.save_backtest(save_payload)
    assert save_res.status_code in (200, 201)
    bid = save_res.json()["id"]

    # Step 8: Verify user's history contains the exact persisted run
    history_res = client.list_backtests()
    assert history_res.status_code == 200
    history_items = history_res.json()
    saved_record = next(b for b in history_items if b["id"] == bid)
    assert saved_record["symbol"] == "HPG"
    assert saved_record["total_return"] == run_data["total_return"]
    assert len(saved_record["equity_curve"]) == len(run_data["equity_curve"])

    # Step 9: Clean teardown (delete watchlist and preset)
    assert client.delete_watchlist(wid).status_code == 204
    assert client.delete_preset(pid).status_code == 204
    assert len(client.list_watchlists().json()) == 0
    assert len(client.list_presets().json()) == 0


def test_dual_user_concurrent_portfolio_workflow(
    user_a_client: E2EClient,
    user_b_client: E2EClient,
):
    """Concurrent multi-user workflow: User A and User B manage distinct portfolios simultaneously."""
    # User A creates Conservative Portfolio
    wl_a = user_a_client.create_watchlist(name="Safe Dividend", symbols=["VNM", "FPT"]).json()
    preset_a = user_a_client.create_preset(name="Conservative Stop", parameters={"stop_loss": 0.03}).json()

    # User B creates Aggressive Portfolio
    wl_b = user_b_client.create_watchlist(name="High Beta Steel", symbols=["HPG", "HSG", "NKG"]).json()
    preset_b = user_b_client.create_preset(name="Aggressive Trailing", parameters={"trailing_stop": 0.08}).json()

    # User A saves Backtest A
    user_a_client.save_backtest({
        "symbol": "VNM",
        "strategy_name": "Div Strategy",
        "strategy_type": "dividend",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 100_000_000.0,
        "total_return": 0.08,
        "sharpe_ratio": 1.2,
        "max_drawdown": -0.02,
        "win_rate": 0.70,
        "equity_curve": [],
    })

    # User B saves Backtest B
    user_b_client.save_backtest({
        "symbol": "HPG",
        "strategy_name": "Momentum Steel",
        "strategy_type": "momentum",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 300_000_000.0,
        "total_return": 0.35,
        "sharpe_ratio": 1.9,
        "max_drawdown": -0.09,
        "win_rate": 0.62,
        "equity_curve": [],
    })

    # Verify User A only sees their own resources
    watchlists_a = user_a_client.list_watchlists().json()
    presets_a = user_a_client.list_presets().json()
    backtests_a = user_a_client.list_backtests().json()
    assert len(watchlists_a) == 1 and watchlists_a[0]["id"] == wl_a["id"]
    assert len(presets_a) == 1 and presets_a[0]["id"] == preset_a["id"]
    assert len(backtests_a) == 1 and backtests_a[0]["symbol"] == "VNM"

    # Verify User B only sees their own resources
    watchlists_b = user_b_client.list_watchlists().json()
    presets_b = user_b_client.list_presets().json()
    backtests_b = user_b_client.list_backtests().json()
    assert len(watchlists_b) == 1 and watchlists_b[0]["id"] == wl_b["id"]
    assert len(presets_b) == 1 and presets_b[0]["id"] == preset_b["id"]
    assert len(backtests_b) == 1 and backtests_b[0]["symbol"] == "HPG"
