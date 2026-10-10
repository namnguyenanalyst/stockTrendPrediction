"""Service quản lý truy vấn dữ liệu lịch sử nến và chỉ báo kỹ thuật chứng khoán."""

import logging

import pandas as pd
from app.core.config import settings
from app.models.schemas import (
    StockBar,
    StockHistoryResponse,
    StockIndicatorBar,
    StockIndicatorsResponse,
    StockSummaryResponse,
    StockSymbolInfo,
)
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Metadata rổ cổ phiếu VN30 và các mã trọng tâm
SYMBOL_METADATA = {
    "VIC": {"name": "Tập đoàn Vingroup", "exchange": "HOSE", "is_core": True},
    "HPG": {"name": "Tập đoàn Hòa Phát", "exchange": "HOSE", "is_core": True},
    "FPT": {"name": "Công ty Cổ phần FPT", "exchange": "HOSE", "is_core": True},
    "VNM": {
        "name": "Công ty Cổ phần Sữa Việt Nam (Vinamilk)",
        "exchange": "HOSE",
        "is_core": True,
    },
    "MWG": {
        "name": "Công ty Cổ phần Đầu tư Thế Giới Di Động",
        "exchange": "HOSE",
        "is_core": True,
    },
    "ACB": {"name": "Ngân hàng Á Châu", "exchange": "HOSE", "is_core": False},
    "BID": {
        "name": "Ngân hàng Đầu tư và Phát triển Việt Nam",
        "exchange": "HOSE",
        "is_core": False,
    },
    "CTG": {"name": "Ngân hàng Công Thương Việt Nam", "exchange": "HOSE", "is_core": False},
    "MBB": {"name": "Ngân hàng Quân Đội", "exchange": "HOSE", "is_core": False},
    "TCB": {"name": "Ngân hàng Kỹ Thương Việt Nam", "exchange": "HOSE", "is_core": False},
    "VCB": {"name": "Ngân hàng Ngoại Thương Việt Nam", "exchange": "HOSE", "is_core": False},
    "VHM": {"name": "Công ty Cổ phần Vinhomes", "exchange": "HOSE", "is_core": False},
    "VPB": {"name": "Ngân hàng Việt Nam Thịnh Vượng", "exchange": "HOSE", "is_core": False},
    "SSI": {"name": "Công ty Cổ phần Chứng khoán SSI", "exchange": "HOSE", "is_core": False},
}


def get_available_symbols() -> list[StockSymbolInfo]:
    """Lấy danh sách các mã cổ phiếu được hỗ trợ trong hệ thống."""
    return [
        StockSymbolInfo(
            symbol=sym,
            name=info["name"],
            exchange=info["exchange"],
            is_core=info["is_core"],
        )
        for sym, info in SYMBOL_METADATA.items()
    ]


def load_stock_dataframe(symbol: str) -> pd.DataFrame:
    """Nạp DataFrame lịch sử của một mã cổ phiếu từ panel interim hoặc raw parquet."""
    clean_sym = symbol.upper()

    panel_path = settings.DATA_DIR / "interim" / "panel" / f"Symbol={clean_sym}"
    if panel_path.exists():
        df = pd.read_parquet(panel_path)
        if "Symbol" not in df.columns:
            df["Symbol"] = clean_sym
        return df.sort_values("Date").reset_index(drop=True)

    raw_path = settings.DATA_DIR / "raw" / f"{clean_sym}.parquet"
    if raw_path.exists():
        df = pd.read_parquet(raw_path)
        if "Symbol" not in df.columns:
            df["Symbol"] = clean_sym
        return df.sort_values("Date").reset_index(drop=True)

    raise HTTPException(
        status_code=404,
        detail=f"Không tìm thấy dữ liệu cho mã cổ phiếu '{clean_sym}'.",
    )


def get_stock_history(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 100,
) -> StockHistoryResponse:
    """Truy vấn dữ liệu lịch sử nến OHLCV có phân trang và lọc theo khoảng thời gian."""
    df = load_stock_dataframe(symbol)

    if start_date:
        df = df[df["Date"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["Date"] <= pd.to_datetime(end_date)]

    total_bars = len(df)
    sub_df = df.tail(limit) if limit > 0 else df

    bars = [
        StockBar(
            date=row["Date"].strftime("%Y-%m-%d")
            if hasattr(row["Date"], "strftime")
            else str(row["Date"])[:10],
            open=round(float(row["Open"]), 2),
            high=round(float(row["High"]), 2),
            low=round(float(row["Low"]), 2),
            close=round(float(row["Close"]), 2),
            volume=int(row["Volume"]),
        )
        for _, row in sub_df.iterrows()
    ]

    return StockHistoryResponse(
        symbol=symbol.upper(),
        total_bars=total_bars,
        bars=bars,
    )


def get_stock_indicators(symbol: str, limit: int = 100) -> StockIndicatorsResponse:
    """Truy vấn các chỉ báo kỹ thuật tương đối đã tính toán cho một mã cổ phiếu."""
    clean_sym = symbol.upper()
    df_raw = load_stock_dataframe(clean_sym)

    # Thử gọi hàm compute_features_per_symbol từ vn_stock nếu có, hoặc tính toán nội bộ
    try:
        from vn_stock.features import compute_features_per_symbol

        df_feat = compute_features_per_symbol(df_raw, drop_na=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "Không thể gọi compute_features_per_symbol trực tiếp: %s. Tính toán fallback.", e
        )
        df_feat = _compute_fallback_indicators(df_raw)

    total_bars = len(df_feat)
    sub_df = df_feat.tail(limit) if limit > 0 else df_feat

    indicators = [
        StockIndicatorBar(
            date=row["Date"].strftime("%Y-%m-%d")
            if hasattr(row["Date"], "strftime")
            else str(row["Date"])[:10],
            close=round(float(row["Close"]), 2),
            open_close_ratio=round(float(row.get("Open_Close_Ratio", 0.0)), 4),
            hl_ratio=round(float(row.get("HL_Ratio", 0.0)), 4),
            sma_20_dev=round(float(row.get("SMA_20_Dev", 0.0)), 4),
            sma_50_dev=round(float(row.get("SMA_50_Dev", 0.0)), 4),
            sma_200_dev=round(float(row.get("SMA_200_Dev", 0.0)), 4),
            cv_50=round(float(row.get("CV_50", 0.0)), 4),
            cv_200=round(float(row.get("CV_200", 0.0)), 4),
            rsi_14=round(float(row.get("RSI", 50.0)), 2),
            return_1d=round(float(row.get("Return_1d", 0.0)), 4),
            vol_ratio=round(float(row.get("Vol_Ratio", 1.0)), 4),
            vnindex_return_1d=round(float(row.get("VNINDEX_Return_1d", 0.0)), 4),
        )
        for _, row in sub_df.iterrows()
    ]

    return StockIndicatorsResponse(
        symbol=clean_sym,
        total_bars=total_bars,
        indicators=indicators,
    )


def get_stock_summary(symbol: str) -> StockSummaryResponse:
    """Lấy tóm tắt nhanh về thị giá, biến động và chỉ báo kỹ thuật của phiên gần nhất."""
    clean_sym = symbol.upper()
    df = load_stock_dataframe(clean_sym)
    if len(df) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Mã '{clean_sym}' không có đủ dữ liệu lịch sử để tính tóm tắt.",
        )

    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    c_now = float(last_row["Close"])
    c_prev = float(prev_row["Close"])
    chg_pct = ((c_now - c_prev) / c_prev) * 100.0 if c_prev > 0 else 0.0

    sma20 = float(df["Close"].tail(20).mean())
    sma50 = float(df["Close"].tail(50).mean())
    sma20_dev = ((c_now - sma20) / sma20) * 100.0 if sma20 > 0 else 0.0
    sma50_dev = ((c_now - sma50) / sma50) * 100.0 if sma50 > 0 else 0.0

    # RSI 14
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=14).mean().iloc[-1]
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean().iloc[-1]
    rs = gain / (loss + 1e-9)
    rsi14 = float(100.0 - (100.0 / (1.0 + rs)))

    d_str = (
        last_row["Date"].strftime("%Y-%m-%d")
        if hasattr(last_row["Date"], "strftime")
        else str(last_row["Date"])[:10]
    )

    return StockSummaryResponse(
        symbol=clean_sym,
        latest_date=d_str,
        latest_close=round(c_now, 2),
        prev_close=round(c_prev, 2),
        change_pct=round(chg_pct, 2),
        volume=int(last_row["Volume"]),
        rsi_14=round(rsi14, 2),
        sma_20_dev=round(sma20_dev, 2),
        sma_50_dev=round(sma50_dev, 2),
    )


def _compute_fallback_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Hàm dự phòng tính toán 13 chỉ báo nếu package vn_stock chưa nạp kịp."""
    g = df.sort_values("Date").copy()
    close = g["Close"]
    open_p = g["Open"]
    high = g["High"]
    low = g["Low"]
    vol = g["Volume"]

    g["Open_Close_Ratio"] = (open_p - close) / close
    g["HL_Ratio"] = (high - low) / close
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    g["SMA_20_Dev"] = (close - sma20) / sma20
    g["SMA_50_Dev"] = (close - sma50) / sma50
    g["SMA_200_Dev"] = (close - sma200) / sma200
    g["CV_50"] = close.rolling(50).std() / (sma50 + 1e-9)
    g["CV_200"] = close.rolling(200).std() / (sma200 + 1e-9)

    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    g["RSI"] = 100.0 - (100.0 / (1.0 + (gain / (loss + 1e-9))))
    g["Return_1d"] = close.pct_change()
    g["Vol_Ratio"] = vol / (vol.rolling(20).mean() + 1e-9)
    if "VNINDEX_Return_1d" not in g.columns:
        g["VNINDEX_Return_1d"] = 0.0

    return g.dropna().reset_index(drop=True)
