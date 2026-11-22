"""Shared historical indicator calculations for charts and backtests."""
import numpy as np
import pandas as pd


def compute_chart_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Tính toán các chỉ báo kỹ thuật cơ bản cho một mã phục vụ bộ lọc điều kiện chiến thuật."""
    df_clean = df.copy().sort_values("Date").reset_index(drop=True)
    if not pd.api.types.is_datetime64_any_dtype(df_clean["Date"]):
        df_clean["Date"] = pd.to_datetime(df_clean["Date"])

    close = df_clean["Close"].astype(float)
    high = df_clean["High"].astype(float) if "High" in df_clean.columns else close
    low = df_clean["Low"].astype(float) if "Low" in df_clean.columns else close
    volume = (
        df_clean["Volume"].astype(float)
        if "Volume" in df_clean.columns
        else pd.Series(0.0, index=df_clean.index)
    )

    # MA Series đa chu kỳ (SMA 5, 10, 20, 50, 100, 200)
    for span in [5, 10, 20, 50, 100, 200]:
        df_clean[f"SMA{span}"] = close.rolling(span, min_periods=1).mean()

    # EMA Series đa chu kỳ (EMA 5, 10, 12, 20, 26, 50, 100, 200)
    for span in [5, 10, 12, 20, 26, 50, 100, 200]:
        df_clean[f"EMA{span}"] = close.ewm(span=span, adjust=False).mean()

    # MACD (12, 26, 9)
    df_clean["MACD"] = df_clean["EMA12"] - df_clean["EMA26"]
    df_clean["MACD_Signal"] = df_clean["MACD"].ewm(span=9, adjust=False).mean()

    # RSI (14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14, min_periods=1).mean()
    rs = gain / (loss + 1e-9)
    df_clean["RSI"] = 100.0 - (100.0 / (1.0 + rs))

    # Bollinger Bands (20, 2)
    std20 = close.rolling(20, min_periods=1).std().fillna(0.0)
    df_clean["BB_Upper"] = df_clean["SMA20"] + 2.0 * std20
    df_clean["BB_Lower"] = df_clean["SMA20"] - 2.0 * std20

    # Volume SMAs (5, 10, 20)
    for span in [5, 10, 20]:
        df_clean[f"Vol_SMA{span}"] = volume.rolling(span, min_periods=1).mean()

    # GTGD trung bình (Tỷ VNĐ) theo chu kỳ 5, 10, 20 phiên
    val_series = (close * volume) / 1e6
    for span in [5, 10, 20]:
        df_clean[f"Avg_Trading_Val_{span}"] = val_series.rolling(span, min_periods=1).mean()

    # ADX (14)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr14 = tr.rolling(14, min_periods=1).mean()
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_di = 100.0 * (pd.Series(plus_dm).rolling(14, min_periods=1).mean() / (atr14 + 1e-9))
    minus_di = 100.0 * (pd.Series(minus_dm).rolling(14, min_periods=1).mean() / (atr14 + 1e-9))
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    df_clean["ADX"] = dx.rolling(14, min_periods=1).mean().fillna(20.0)

    # Relative Strength RS (0 - 99.93)
    rs_60 = close.pct_change(60).fillna(0.0)
    df_clean["RS"] = ((rs_60.expanding().rank(pct=True)) * 99.93).clip(0.0, 99.93)

    return df_clean
