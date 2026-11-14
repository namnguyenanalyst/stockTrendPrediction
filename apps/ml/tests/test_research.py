import json

import pandas as pd
import pytest

from vn_stock.modeling.research import evaluate_financial_holdout, _write_json


def fixture_data():
    dates = pd.bdate_range("2026-01-05", periods=8)
    panel, predictions = [], []
    for symbol in ("VIC", "HPG"):
        for date in dates:
            panel.append({"Date": date, "Symbol": symbol, "Open": 50.,
                          "High": 50., "Low": 50., "Close": 50.})
            for kind in ("lightgbm", "lstm"):
                predictions.append({"date": str(date.date()), "symbol": symbol,
                                    "model": kind, "probabilities": [.1, .1, .8]})
    return pd.DataFrame(panel), predictions


def test_research_compares_identical_panels_and_persists_valid_json(tmp_path):
    panel, predictions = fixture_data()
    result = evaluate_financial_holdout(panel, predictions, n_simulations=2)
    assert result["lightgbm"]["metrics"] == result["lstm"]["metrics"]
    assert result["lightgbm"]["metrics"]["excess_return_pct"] == 0
    assert len(result["monte_carlo"]["simulations"]) == 2
    assert result["monte_carlo"]["comparisons"]["lightgbm"]["p_sharpe"] > 0
    path = tmp_path / "financial.json"
    _write_json(path, result)
    assert "NaN" not in path.read_text()
    assert json.loads(path.read_text())["lightgbm"]["per_symbol"]["VIC"]["trades"][0]["realized_pnl"] is None


def test_research_rejects_mismatched_model_test_dates():
    panel, predictions = fixture_data()
    with pytest.raises(ValueError, match="aligned|identical"):
        evaluate_financial_holdout(panel, predictions[1:], n_simulations=2)
