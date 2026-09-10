"""Module nạp mô hình đã lưu, thực hiện suy luận (inference) và đưa ra khuyến nghị đầu tư."""

import argparse
import pickle
from pathlib import Path
from typing import Dict, Any

import numpy as np
import torch

from vn_stock.config import (
    DEFAULT_HIDDEN_SIZE,
    DEFAULT_INPUT_SIZE,
    DEFAULT_NUM_LAYERS,
    DEFAULT_OUTPUT_SIZE,
    DEFAULT_SEQ_LENGTH,
    DEFAULT_SYMBOL,
    MODELS_DIR,
)
from vn_stock.dataset import fetch_stock_data, load_local_data
from vn_stock.modeling.model import PredictionModel


def predict_next_day(
    symbol: str = DEFAULT_SYMBOL,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    models_dir: Path = MODELS_DIR,
) -> Dict[str, Any]:
    """Dự báo mức giá đóng cửa phiên tiếp theo và xác định tín hiệu Mua/Bán/Nắm giữ."""
    model_path = models_dir / f"model_{symbol.upper()}.pth"
    scaler_path = models_dir / f"scaler_{symbol.upper()}.pkl"

    if not model_path.exists() or not scaler_path.exists():
        raise FileNotFoundError(
            f"Chưa tìm thấy checkpoint mô hình cho {symbol}. Hãy chạy lệnh huấn luyện trước!"
        )

    # Nạp scaler và mô hình
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = PredictionModel(
        input_size=DEFAULT_INPUT_SIZE,
        hidden_size=DEFAULT_HIDDEN_SIZE,
        num_layers=DEFAULT_NUM_LAYERS,
        output_size=DEFAULT_OUTPUT_SIZE,
    ).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    # Nạp chuỗi giá gần nhất
    df = load_local_data(symbol)
    if df is None:
        df = fetch_stock_data(symbol)

    close_col = "Close" if "Close" in df.columns else "Giá đóng cửa"
    recent_prices = df[close_col].values.astype(float)
    if len(recent_prices) < seq_length:
        raise ValueError(f"Dữ liệu cần tối thiểu {seq_length} phiên.")

    last_window = recent_prices[-seq_length:].reshape(-1, 1)
    scaled_window = scaler.transform(last_window)

    x_input = torch.FloatTensor(scaled_window.reshape(1, seq_length, 1)).to(device)
    with torch.no_grad():
        scaled_pred = model(x_input).cpu().numpy()

    predicted_price = float(scaler.inverse_transform(scaled_pred)[0, 0])
    current_price = float(recent_prices[-1])
    pct_change = ((predicted_price - current_price) / current_price) * 100

    # Phân loại tín hiệu
    if pct_change > 1.5:
        signal = "MUA (BUY)"
    elif pct_change < -1.5:
        signal = "BÁN (SELL)"
    else:
        signal = "NẮM GIỮ (HOLD)"

    return {
        "symbol": symbol.upper(),
        "current_price": round(current_price, 2),
        "predicted_price": round(predicted_price, 2),
        "pct_change": round(pct_change, 2),
        "signal": signal,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dự báo giá cổ phiếu phiên tiếp theo.")
    parser.add_argument("--symbol", type=str, default=DEFAULT_SYMBOL, help="Mã cổ phiếu")
    args = parser.parse_args()
    try:
        res = predict_next_day(symbol=args.symbol)
        print(f"=== KẾT QUẢ DỰ BÁO {res['symbol']} ===")
        print(f"Giá hiện tại: {res['current_price']}")
        print(f"Giá dự báo T+1: {res['predicted_price']} ({res['pct_change']:+.2f}%)")
        print(f"Khuyến nghị: {res['signal']}")
    except Exception as err:
        print(f"Lỗi: {err}")
