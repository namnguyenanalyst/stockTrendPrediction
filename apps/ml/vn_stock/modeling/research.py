"""Reproducible offline research runs; audited data and protocol precede all results."""

import argparse
from dataclasses import asdict
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
from time import perf_counter

import numpy as np
import pandas as pd

from vn_stock.backtest import (
    TradeRecord,
    calculate_financial_metrics,
    monte_carlo_tail_probability,
    run_backtest,
    trading_prices_vnd,
)
from vn_stock.config import MODELS_DIR
from vn_stock.data_quality import CORE_COLUMNS, audit_panel
from vn_stock.modeling.evaluation import EvaluationConfig, run_temporal_evaluation

WINDOWS = (("2025-12-31", "2026-03-31"), ("2026-03-31", "2026-06-30"),
           ("2026-06-30", "2026-09-30"), ("2026-09-30", "2026-11-13"))
TRADING = {"initial_capital": 300_000_000.0, "fee_rate": 0.0015,
           "tax_rate": 0.001, "slippage_rate": 0.0005, "lot_size": 100,
           "settlement_delay": 2, "execution_price": "open", "close_at_end": True}


def _write_json(path, value):
    def normalize(item):
        if isinstance(item, dict):
            return {key: normalize(value) for key, value in item.items()}
        if isinstance(item, (list, tuple)):
            return [normalize(value) for value in item]
        if isinstance(item, float) and not np.isfinite(item):
            return None
        return item
    path.write_text(json.dumps(normalize(value), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def _aggregate_backtests(results, initial_capital):
    curves = [result.equity_df.set_index("Date")[["Total_Equity", "Benchmark_Equity"]]
              for result in results]
    if any(not frame.index.equals(curves[0].index) for frame in curves):
        raise ValueError("Research requires aligned observed sessions; no backfilling.")
    equity = sum(frame.Total_Equity for frame in curves)
    benchmark = sum(frame.Benchmark_Equity for frame in curves)
    trades = [TradeRecord(**trade) for result in results
              for trade in result.trades_df.to_dict(orient="records")]
    metrics = calculate_financial_metrics(equity, initial_capital, trades,
        buy_and_hold_return_pct=float((benchmark.iloc[-1] / initial_capital - 1) * 100))
    curve = [{"date": str(date), "equity": float(eq), "buy_hold": float(bh)}
             for date, eq, bh in zip(equity.index, equity, benchmark)]
    return metrics, curve


def _market_inputs(panel, predictions, model):
    records = pd.DataFrame([row for row in predictions if row["model"] == model])
    inputs = {}
    for symbol, group in records.groupby("symbol", sort=True):
        group = group.sort_values("date")
        dates = pd.to_datetime(group.date)
        source = panel[panel.Symbol == symbol].set_index("Date").loc[dates].reset_index()
        inputs[symbol] = (trading_prices_vnd(source, "kVND"), np.array(group.probabilities.tolist()))
    return inputs


def _simulate_portfolio(inputs, rng=None):
    settings = {**TRADING, "initial_capital": TRADING["initial_capital"] / len(inputs)}
    results = []
    for symbol, (market, probabilities) in inputs.items():
        if rng is None:
            result = run_backtest(market, probabilities=probabilities, symbol=symbol, **settings)
        else:
            signals = rng.choice(3, size=len(market), p=[.25, .5, .25])
            result = run_backtest(market, signals=signals, symbol=symbol, **settings)
        results.append(result)
    return _aggregate_backtests(results, TRADING["initial_capital"]), results


def evaluate_financial_holdout(panel, predictions, n_simulations=100, seed=42):
    """Compare both models on all fixed-universe stocks, never select a winning stock."""
    if n_simulations < 1:
        raise ValueError("At least one simulation is required.")
    report, market_inputs = {}, {}
    for kind in ("lightgbm", "lstm"):
        inputs = _market_inputs(panel, predictions, kind)
        if not inputs:
            raise ValueError("No held-out predictions to simulate.")
        market_inputs[kind] = inputs
        (metrics, curve), results = _simulate_portfolio(inputs)
        report[kind] = {"metrics": metrics.__dict__, "equity_curve": curve,
                        "per_symbol": {r.symbol: {"metrics": r.metrics.__dict__,
                            "trades": r.trades_df.to_dict(orient="records")} for r in results}}
    first = market_inputs["lightgbm"]
    second = market_inputs["lstm"]
    if set(first) != set(second) or any(not first[s][0].Date.equals(second[s][0].Date) for s in first):
        raise ValueError("Models must use identical symbol/date panels for the shared null.")
    rng = np.random.default_rng(seed)
    null = []
    for iteration in range(n_simulations):
        (metrics, _), _ = _simulate_portfolio(first, rng)
        null.append({"iteration": iteration, "roi": metrics.total_return_pct,
                     "sharpe": metrics.sharpe_ratio, "mdd": metrics.max_drawdown_pct})
    report["monte_carlo"] = {"seed": seed, "simulations": null,
        "null_model": "iid_class_signals_independent_by_symbol", "class_probabilities": [.25, .5, .25],
        "comparisons": {kind: {"p_roi": monte_carlo_tail_probability(
            [r["roi"] for r in null], report[kind]["metrics"]["total_return_pct"]),
            "p_sharpe": monte_carlo_tail_probability(
            [r["sharpe"] for r in null], report[kind]["metrics"]["sharpe_ratio"])}
            for kind in ("lightgbm", "lstm")}}
    return report


def run_research(output_dir: Path, allow_unverified_prices=False):
    import torch

    from vn_stock.data_ingestion import load_local_data, load_panel_dataset
    output_dir = Path(output_dir).resolve()
    if output_dir == MODELS_DIR.resolve() or output_dir.is_relative_to(MODELS_DIR.resolve()):
        raise ValueError("Research must not write to production models.")
    panel = load_panel_dataset()
    index = load_local_data("VNINDEX")
    audit = audit_panel(panel, index.Date if index is not None else None)
    if not audit["training_allowed"]:
        raise ValueError(f"Data audit failed: {audit['fatal_errors']}")
    if not allow_unverified_prices:
        raise ValueError("Unverified price adjustments: use explicit diagnostic mode, not final performance claims.")
    output_dir.mkdir(parents=True, exist_ok=False)
    _write_json(output_dir / "data_audit.json", audit)
    panel = panel[CORE_COLUMNS].copy()
    panel.to_parquet(output_dir / "panel_snapshot.parquet", index=False)
    torch.set_num_threads(1)
    protocol = {"windows": [asdict(EvaluationConfig(a, b)) for a, b in WINDOWS],
        "seed": 42, "monte_carlo_simulations": 100, "trading": TRADING,
        "data_sha256": audit["data_sha256"], "result_status": "diagnostic_unverified_price_adjustments",
        "python": sys.version, "platform": platform.platform(), "torch_threads": 1,
        "sources": {str(p.relative_to(Path(__file__).parents[1])): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in Path(__file__).parents[1].rglob("*.py")}}
    _write_json(output_dir / "protocol.json", protocol)
    source_root = Path(__file__).parents[1]
    for relative, digest in protocol["sources"].items():
        content = (source_root / relative).read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise RuntimeError("Source changed while freezing the research protocol.")
        target = output_dir / "source_snapshot" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    _write_json(output_dir / "environment.json", {
        package: version(package) for package in
        ("numpy", "pandas", "scikit-learn", "lightgbm", "torch", "shap", "pyarrow")})
    summaries = []
    for number, (cutoff, end) in enumerate(WINDOWS, 1):
        started = perf_counter()
        fold = output_dir / f"fold_{number}"
        print(f"Fold {number}: cutoff={cutoff}, end={end}, epochs=40", flush=True)
        evaluation = run_temporal_evaluation(panel, fold, EvaluationConfig(cutoff, end))
        predictions = json.loads((fold / "predictions.json").read_text())
        print(f"Fold {number}: evaluating portfolio and 100 shared null portfolios", flush=True)
        financial = evaluate_financial_holdout(panel, predictions)
        _write_json(fold / "financial.json", financial)
        summary = {"fold": number, "cutoff": cutoff, "end": end,
                   "classification": evaluation["metrics"], "test_samples": evaluation["test_samples"],
                   "finance": {k: financial[k]["metrics"] for k in ("lightgbm", "lstm")},
                   "monte_carlo_comparisons": financial["monte_carlo"]["comparisons"],
                   "elapsed_seconds": perf_counter() - started}
        summaries.append(summary)
        _write_json(output_dir / "summary.json", {"protocol": protocol, "folds": summaries})
        print(f"Fold {number} completed in {summary['elapsed_seconds']:.1f}s", flush=True)
    return summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-unverified-prices", action="store_true")
    args = parser.parse_args()
    run_research(args.output, args.allow_unverified_prices)
