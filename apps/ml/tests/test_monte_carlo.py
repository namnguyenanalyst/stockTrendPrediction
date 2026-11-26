import numpy as np
import pandas as pd
import pytest

from vn_stock.backtest import run_monte_carlo_random_test


def frame():
    return pd.DataFrame({"Date": pd.bdate_range("2026-01-05", periods=8),
                         "Open": 100., "High": 100., "Low": 100., "Close": 100.})


def test_monte_carlo_does_not_reset_callers_random_generator():
    np.random.seed(123)
    expected = np.random.random(3)
    np.random.seed(123)
    run_monte_carlo_random_test(frame(), n_simulations=2)
    np.testing.assert_array_equal(np.random.random(3), expected)


def test_zero_exceedances_never_report_zero_p_value(monkeypatch):
    from types import SimpleNamespace
    ai = SimpleNamespace(metrics=SimpleNamespace(total_return_pct=1e6, sharpe_ratio=1e6))
    monkeypatch.setattr("vn_stock.backtest.run_backtest", lambda **kwargs: SimpleNamespace(
        metrics=SimpleNamespace(total_return_pct=0, sharpe_ratio=0, max_drawdown_pct=0)))
    result = run_monte_carlo_random_test(frame(), n_simulations=9, ai_result=ai)
    assert result["ai_comparison"]["p_value_sharpe"] == 0.1
    assert len(result["simulations"]) == 9
    assert result["null_model"] == "iid_class_signals"


@pytest.mark.parametrize("count,probs", [(0, (.25, .5, .25)), (2, (.1, .1, .1)), (2, (-1., 1., 1.))])
def test_invalid_simulation_configuration_is_rejected(count, probs):
    with pytest.raises(ValueError):
        run_monte_carlo_random_test(frame(), n_simulations=count, class_probs=probs)
