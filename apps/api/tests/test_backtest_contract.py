"""Backtest request validation without market data or production artifacts."""
import pytest
from pydantic import ValidationError

from app.models.schemas import AdvancedBacktestRequest, BacktestRequest


@pytest.mark.parametrize("payload", [
    {"lot_size": 0}, {"settlement_delay": -1}, {"execution_price": "high"},
    {"buy_prob_threshold": -0.1}, {"sell_prob_threshold": 2},
    {"stop_loss_pct": -0.1}, {"trailing_stop_pct": float("nan")},
])
def test_simple_request_rejects_invalid_execution_parameters(payload):
    with pytest.raises(ValidationError):
        BacktestRequest(**payload)


@pytest.mark.parametrize("payload", [
    {"lot_size": 0}, {"settlement_delay": -1}, {"model_type": "typo"},
    {"start_date": "not-a-date"}, {"end_date": "2026-02-30"},
])
def test_advanced_request_rejects_invalid_parameters(payload):
    data = {"start_date": "2026-01-05", "end_date": "2026-02-02", **payload}
    with pytest.raises(ValidationError):
        AdvancedBacktestRequest(**data)


@pytest.mark.parametrize("path,payload", [
    ("/api/backtest/run", {"lot_size": 0}),
    ("/api/backtest/run-advanced", {"start_date": "not-a-date", "end_date": "2026-02-02"}),
])
@pytest.mark.asyncio
async def test_invalid_requests_return_422_without_running_engine(path, payload, monkeypatch):
    import httpx
    from app.main import app
    from app.services import backtest_service
    def forbid_engine(*args, **kwargs):
        pytest.fail("Invalid request reached backtest service")
    monkeypatch.setattr(backtest_service, "run_backtest_simulation", forbid_engine)
    monkeypatch.setattr(backtest_service, "run_advanced_backtest", forbid_engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        result = await client.post(path, json=payload)
    assert result.status_code == 422


def test_single_backtest_missing_data_does_not_fetch(monkeypatch):
    from fastapi import HTTPException
    from app.services.backtest_service import run_backtest_simulation
    monkeypatch.setattr("vn_stock.data_ingestion.load_local_data", lambda _: None)
    def forbid_fetch(*args, **kwargs):
        pytest.fail("Backtest implicitly refreshed data")
    monkeypatch.setattr("vn_stock.data_ingestion.fetch_stock_data", forbid_fetch)
    with pytest.raises(HTTPException) as error:
        run_backtest_simulation(BacktestRequest())
    assert error.value.status_code == 404


@pytest.mark.parametrize("advanced", [False, True])
def test_engine_validation_errors_are_not_server_errors(advanced, monkeypatch):
    import pandas as pd
    from fastapi import HTTPException
    from app.services import backtest_service
    monkeypatch.setattr("vn_stock.data_ingestion.load_local_data", lambda _: pd.DataFrame({"Close": [1]}))
    monkeypatch.setattr(backtest_service.stock_service, "get_available_symbols", lambda: [])
    def reject(*args, **kwargs):
        raise ValueError("Missing historical point-in-time data")
    monkeypatch.setattr("vn_stock.backtest.backtest_symbol_oos", reject)
    monkeypatch.setattr("vn_stock.backtest.run_portfolio_backtest", reject)
    with pytest.raises(HTTPException) as error:
        if advanced:
            backtest_service.run_advanced_backtest(AdvancedBacktestRequest(
                start_date="2026-01-05", end_date="2026-02-02"))
        else:
            backtest_service.run_backtest_simulation(BacktestRequest())
    assert error.value.status_code == 422
    assert "historical" in error.value.detail


@pytest.mark.parametrize("conditions", [
    {"rsi_min": 80, "rsi_max": 20}, {"min_pe": 20, "max_pe": 10},
    {"condition_logic": "XOR"}, {"stop_loss_pct": -0.1},
    {"rsi_threshold": float("nan")}, {"vol_spike_period": 7},
    {"use_ma": True, "ma_operator": "invalid"},
    {"use_ema": True, "ema_operator": "invalid"},
    {"use_macd": True, "macd_operator": "invalid"},
    {"use_price_cross": True, "price_cross_operator": "invalid"},
    {"use_price_increase": True, "price_t0_operator": "invalid"},
    {"market_condition": "uptrend"},
])
def test_nested_conditions_reject_invalid_rules(conditions):
    from app.models.schemas import BacktestConditionFilter
    with pytest.raises(ValidationError):
        BacktestConditionFilter(**conditions)


def test_advanced_backtest_rejects_unknown_sector_or_empty_portfolio(monkeypatch):
    from fastapi import HTTPException
    from app.services import backtest_service
    monkeypatch.setattr(backtest_service.stock_service, "get_available_sectors", lambda: [])
    monkeypatch.setattr(backtest_service.stock_service, "get_available_symbols", lambda: [])
    with pytest.raises(HTTPException) as sec_err:
        backtest_service.run_advanced_backtest(AdvancedBacktestRequest(
            scope_type="sector", sector_name="NonExistentSector",
            start_date="2026-01-05", end_date="2026-02-02",
        ))
    assert sec_err.value.status_code == 422

    with pytest.raises(HTTPException) as port_err:
        backtest_service.run_advanced_backtest(AdvancedBacktestRequest(
            scope_type="portfolio", portfolio_symbols=[],
            start_date="2026-01-05", end_date="2026-02-02",
        ))
    assert port_err.value.status_code == 422


def test_single_backtest_computes_nullable_reward_risk_ratio(monkeypatch):
    import pandas as pd
    from vn_stock.backtest import BacktestMetrics, BacktestResult
    from app.services import backtest_service

    monkeypatch.setattr("vn_stock.data_ingestion.load_local_data", lambda _: pd.DataFrame({"Close": [1]}))

    def make_result(trades_rows):
        metrics = BacktestMetrics(
            initial_capital=100_000_000, final_equity=105_000_000,
            total_return_pct=5.0, cagr_pct=10.0, buy_and_hold_return_pct=2.0,
            excess_return_pct=3.0, annualized_volatility_pct=12.0,
            sharpe_ratio=1.2, sortino_ratio=1.5, max_drawdown_pct=3.0,
            calmar_ratio=3.3, var_95_pct=1.0, cvar_95_pct=1.5,
            win_rate_pct=50.0, profit_factor=2.0, total_trades=len(trades_rows),
            winning_trades=1, losing_trades=1, avg_trade_return_pct=2.5,
            best_trade_return_pct=10.0, worst_trade_return_pct=-5.0,
            avg_holding_days=3.0, total_fees_paid=1000, total_taxes_paid=500,
            total_costs=1500, cost_impact_pct=0.01,
        )
        eq_df = pd.DataFrame({"Date": ["2026-01-05"], "Total_Equity": [105_000_000.0]})
        return BacktestResult("VIC", "AI_LIGHTGBM_VALIDATION", metrics, eq_df, pd.DataFrame(trades_rows), {})

    # 1. Both win and loss -> 10.0 / 5.0 = 2.0
    monkeypatch.setattr("vn_stock.backtest.backtest_symbol_oos", lambda **_: make_result([
        {"trade_id": 1, "order_type": "SELL", "exec_date": "2026-01-06", "exec_price": 27400, "shares": 100,
         "fee": 400, "tax": 200, "net_cash_flow": 2739400, "realized_pnl": 100000, "realized_return_pct": 10.0, "holding_days": 3},
        {"trade_id": 2, "order_type": "SELL", "exec_date": "2026-01-10", "exec_price": 25000, "shares": 100,
         "fee": 400, "tax": 200, "net_cash_flow": 2499400, "realized_pnl": -50000, "realized_return_pct": -5.0, "holding_days": 3},
    ]))
    res_both = backtest_service.run_backtest_simulation(BacktestRequest())
    assert res_both.metrics.reward_risk_ratio == 2.0

    # 2. Win only -> None
    monkeypatch.setattr("vn_stock.backtest.backtest_symbol_oos", lambda **_: make_result([
        {"trade_id": 1, "order_type": "SELL", "exec_date": "2026-01-06", "exec_price": 27400, "shares": 100,
         "fee": 400, "tax": 200, "net_cash_flow": 2739400, "realized_pnl": 100000, "realized_return_pct": 10.0, "holding_days": 3},
    ]))
    res_win_only = backtest_service.run_backtest_simulation(BacktestRequest())
    assert res_win_only.metrics.reward_risk_ratio is None
