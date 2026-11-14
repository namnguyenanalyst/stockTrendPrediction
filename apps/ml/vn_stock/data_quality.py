"""Read-only checks of observed OHLCV integrity and unresolved adjustment risks."""

import hashlib

import numpy as np
import pandas as pd

CORE_COLUMNS = ["Date", "Symbol", "Open", "High", "Low", "Close", "Volume", "VNINDEX_Return_1d"]
PRICE_COLUMNS = ["Open", "High", "Low", "Close"]


def panel_fingerprint(panel: pd.DataFrame) -> str:
    canonical = panel[CORE_COLUMNS].sort_values(["Date", "Symbol"]).reset_index(drop=True)
    return hashlib.sha256(pd.util.hash_pandas_object(canonical, index=False).values.tobytes()).hexdigest()


def audit_panel(panel: pd.DataFrame, market_dates=None, jump_threshold=0.15) -> dict:
    """Flag large jumps for verification, never infer adjustment factors from prices."""
    missing_columns = sorted(set(CORE_COLUMNS) - set(panel.columns))
    if missing_columns or panel.empty:
        return {"fatal_errors": {"missing_columns": missing_columns, "empty": panel.empty},
                "training_allowed": False, "publication_ready": False}
    frame = panel[CORE_COLUMNS].copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    numeric = frame[PRICE_COLUMNS + ["Volume"]].apply(pd.to_numeric, errors="coerce")
    prices = numeric[PRICE_COLUMNS]
    fatal = {
        "invalid_dates": int(frame.Date.isna().sum()),
        "missing_symbols": int(frame.Symbol.isna().sum()),
        "duplicate_keys": int(frame.duplicated(["Date", "Symbol"]).sum()),
        "nonfinite_ohlcv_rows": int((~np.isfinite(numeric)).any(axis=1).sum()),
        "nonpositive_prices": int((prices <= 0).any(axis=1).sum()),
        "negative_volume": int((numeric.Volume < 0).sum()),
        "invalid_candle_bounds": int(((prices.High < prices.max(axis=1)) |
                                       (prices.Low > prices.min(axis=1))).sum()),
    }
    reference = pd.DatetimeIndex(market_dates if market_dates is not None else frame.Date.unique()).dropna()
    symbols, jumps = {}, []
    for symbol, original in frame.groupby("Symbol"):
        group = original.sort_values("Date")
        returns = pd.to_numeric(group.Close, errors="coerce").pct_change(fill_method=None)
        for date, value in zip(group.loc[returns.abs() > jump_threshold, "Date"],
                               returns[returns.abs() > jump_threshold]):
            jumps.append({"symbol": symbol, "date": str(date.date()), "return": float(value)})
        expected = reference[(reference >= group.Date.min()) & (reference <= group.Date.max())]
        missing = expected.difference(pd.DatetimeIndex(group.Date))
        symbols[symbol] = {"rows": len(group), "first_date": str(group.Date.min().date()),
                           "last_date": str(group.Date.max().date()),
                           "sorted": bool(original.Date.is_monotonic_increasing),
                           "missing_market_dates": [str(d.date()) for d in missing]}
    return {"rows": len(frame), "symbols": symbols, "data_sha256": panel_fingerprint(frame),
            "fatal_errors": fatal, "training_allowed": not any(fatal.values()),
            "publication_ready": False,
            "price_unit": "kVND_assumed_from_ingestion_contract_not_independently_verified",
            "price_adjustment_status": "unverified",
            "jump_threshold": jump_threshold, "large_jump_candidates": jumps,
            "weekend_rows": int((frame.Date.dt.dayofweek >= 5).sum()),
            "missing_index_returns": int(frame.VNINDEX_Return_1d.isna().sum()),
            "ignored_legacy_columns": sorted(set(panel.columns) - set(CORE_COLUMNS)),
            "limitations": ["Large jumps are candidates, not verified corporate actions.",
                            "Observed index dates do not prove an official exchange calendar.",
                            "A fixed current constituent universe may have survivorship bias."]}
