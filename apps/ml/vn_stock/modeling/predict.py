"""Module nạp mô hình đã lưu, thực hiện suy luận (inference) và đưa ra khuyến nghị đầu tư.

Hỗ trợ suy luận xu hướng thị trường 3 lớp (0: Giảm, 1: Đi ngang, 2: Tăng) cho:
- PyTorch Global LSTM Classifier (dựa trên chuỗi 3D đa biến 20 phiên)
- LightGBM Classifier (dựa trên đặc trưng dạng bảng tại phiên gần nhất)
"""

import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import argparse
import logging
from pathlib import Path
import pickle
from typing import Any

logger = logging.getLogger(__name__)


import numpy as np
import pandas as pd

from vn_stock.config import (
    CLASS_NAMES,
    DEFAULT_LSTM_HIDDEN_SIZE,
    DEFAULT_LSTM_NUM_LAYERS,
    DEFAULT_SEQ_LENGTH,
    DEFAULT_SYMBOL,
    MODELS_DIR,
    SIGNAL_RECOMMENDATIONS,
)
from vn_stock.data_ingestion import fetch_stock_data, load_local_data, load_panel_dataset
from vn_stock.features import ALL_FEATURE_COLS, FEATURE_COLS, compute_features_per_symbol


def load_prediction_artifacts(
    model_type: str = "lstm",
    models_dir: Path = MODELS_DIR,
    hidden_size: int = DEFAULT_LSTM_HIDDEN_SIZE,
    num_layers: int = DEFAULT_LSTM_NUM_LAYERS,
) -> tuple[Any, Any]:
    """
    Nạp mô hình đã huấn luyện (LSTM hoặc LightGBM) và Scaler chuẩn hóa từ thư mục models/.

    Args:
        model_type: Loại mô hình ('lstm' hoặc 'lightgbm').
        models_dir: Thư mục chứa artifact.
        hidden_size: Số nơ-ron lớp ẩn của LSTM.
        num_layers: Số lớp xếp chồng của LSTM.

    Returns:
        tuple[model, scaler]
    """
    scaler_path = models_dir / "scaler_window3.pkl"
    if not scaler_path.exists():
        raise FileNotFoundError(
            f"Chưa tìm thấy scaler tại {scaler_path}. Hãy chạy huấn luyện trước bằng `make train` hoặc python -m vn_stock.modeling.train."
        )

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    if model_type.lower() == "lstm":
        import torch

        from vn_stock.modeling.model import GlobalLSTMClassifier

        model_path = models_dir / "global_lstm_classifier.pth"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Chưa tìm thấy checkpoint LSTM tại {model_path}. Hãy chạy huấn luyện trước!"
            )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = GlobalLSTMClassifier(
            input_size=len(ALL_FEATURE_COLS),
            hidden_size=hidden_size,
            num_layers=num_layers,
        ).to(device)
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        return model, scaler

    elif model_type.lower() in ("lightgbm", "lgb"):
        import lightgbm as lgb

        lgb_txt_path = models_dir / "lightgbm_classifier.txt"
        lgb_pkl_path = models_dir / "lightgbm_classifier.pkl"
        if lgb_txt_path.exists():
            model = lgb.Booster(model_file=str(lgb_txt_path))
        elif lgb_pkl_path.exists():
            with open(lgb_pkl_path, "rb") as f:
                model = pickle.load(f)
        else:
            raise FileNotFoundError(
                f"Chưa tìm thấy model LightGBM tại {lgb_txt_path}. Hãy chạy huấn luyện trước!"
            )
        return model, scaler

    else:
        raise ValueError(
            f"Loại mô hình không hợp lệ: '{model_type}'. Chỉ hỗ trợ 'lstm' hoặc 'lightgbm'."
        )


def prepare_inference_features(
    symbol: str = DEFAULT_SYMBOL,
    seq_length: int = DEFAULT_SEQ_LENGTH,
) -> tuple[pd.DataFrame, float, str]:
    """
    Nạp dữ liệu lịch sử và tính toán bộ 13 đặc trưng tương đối + Symbol_Code cho một mã cổ phiếu.

    Returns:
        tuple[df_features, latest_close_price, latest_date_str]
    """
    clean_sym = symbol.upper()

    # 1. Thử nạp từ panel interim (đã có sẵn cột VNINDEX_Return_1d)
    df_raw = None
    try:
        df_raw = load_panel_dataset(symbols=[clean_sym])
    except (FileNotFoundError, ValueError, KeyError) as err:
        logger.debug("Không thể nạp dữ liệu từ panel: %s", err)

    # 2. Fallback nếu panel chưa có: nạp từ raw và merge VNINDEX
    if df_raw is None or df_raw.empty or len(df_raw) < 200:
        stock_df = load_local_data(clean_sym)
        if stock_df is None:
            stock_df = fetch_stock_data(clean_sym)

        vnindex_df = load_local_data("VNINDEX")
        if vnindex_df is not None:
            vn_clean = vnindex_df.sort_values("Date").copy()
            close_col = "Close" if "Close" in vn_clean.columns else "Giá đóng cửa"
            vn_clean["VNINDEX_Return_1d"] = vn_clean[close_col].pct_change()
            df_raw = pd.merge(
                stock_df,
                vn_clean[["Date", "VNINDEX_Return_1d"]],
                on="Date",
                how="left",
            )
            df_raw["VNINDEX_Return_1d"] = df_raw["VNINDEX_Return_1d"].fillna(0.0)
        else:
            df_raw = stock_df.copy()
            df_raw["VNINDEX_Return_1d"] = 0.0

    if "Symbol" not in df_raw.columns:
        df_raw["Symbol"] = clean_sym

    # Tính toán bộ đặc trưng
    df_feat = compute_features_per_symbol(df_raw, drop_na=True)
    if len(df_feat) < seq_length:
        raise ValueError(
            f"Mã {clean_sym} chỉ có {len(df_feat)} phiên hợp lệ, không đủ tối thiểu seq_length={seq_length}."
        )

    latest_row = df_feat.iloc[-1]
    latest_close = float(latest_row["Close"])
    latest_date = str(pd.to_datetime(latest_row["Date"]).strftime("%Y-%m-%d"))

    return df_feat, latest_close, latest_date


def predict_trend(
    symbol: str = DEFAULT_SYMBOL,
    model_type: str = "lstm",
    seq_length: int = DEFAULT_SEQ_LENGTH,
    models_dir: Path = MODELS_DIR,
    hidden_size: int = DEFAULT_LSTM_HIDDEN_SIZE,
    num_layers: int = DEFAULT_LSTM_NUM_LAYERS,
) -> dict[str, Any]:
    """
    Thực hiện suy luận dự báo xu hướng thị trường phiên kế tiếp (T+1) và xuất tín hiệu đầu tư.

    Args:
        symbol: Mã cổ phiếu (ví dụ: 'VIC', 'HPG', 'FPT').
        model_type: 'lstm' hoặc 'lightgbm'.
        seq_length: Độ dài chuỗi quan sát (mặc định 20 phiên).
        models_dir: Thư mục chứa artifact mô hình.
        hidden_size: Số nơ-ron lớp ẩn nếu dùng LSTM.
        num_layers: Số lớp xếp chồng nếu dùng LSTM.

    Returns:
        dict chứa:
        - symbol: Mã cổ phiếu
        - date: Ngày của phiên giao dịch gần nhất
        - current_price: Thị giá đóng cửa phiên gần nhất
        - model_type: Loại mô hình suy luận ('lstm' hoặc 'lightgbm')
        - predicted_label: Nhãn dự báo (0: Giảm, 1: Đi ngang, 2: Tăng)
        - class_name: Tên xu hướng ("GIẢM", "ĐI NGANG", "TĂNG")
        - signal: Tín hiệu hành động ("BÁN (SELL)", "NẮM GIỮ (HOLD)", "MUA (BUY)")
        - probabilities: Xác suất cho từng lớp {"GIẢM": p0, "ĐI NGANG": p1, "TĂNG": p2}
        - horizon: Kỳ hạn dự báo ("T+1")
    """
    clean_sym = symbol.upper()
    model, scaler = load_prediction_artifacts(
        model_type=model_type,
        models_dir=models_dir,
        hidden_size=hidden_size,
        num_layers=num_layers,
    )
    df_feat, latest_close, latest_date = prepare_inference_features(
        clean_sym, seq_length=seq_length
    )

    # Chuẩn hóa 13 đặc trưng số học bằng scaler (Symbol_Code giữ nguyên)
    scaled_df = df_feat.copy()
    scaled_df[FEATURE_COLS] = scaler.transform(df_feat[FEATURE_COLS])

    if model_type.lower() == "lstm":
        import torch

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        recent_window = scaled_df[ALL_FEATURE_COLS].tail(seq_length).values.astype(np.float32)
        x_tensor = torch.from_numpy(
            np.ascontiguousarray(recent_window.reshape(1, seq_length, -1))
        ).to(device)

        with torch.no_grad():
            probs = model.predict_proba(x_tensor).cpu().numpy()[0]

    else:
        last_row = scaled_df[ALL_FEATURE_COLS].tail(1)
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(last_row)[0]
        else:
            probs = model.predict(last_row)[0]

    pred_label = int(np.argmax(probs))
    class_name = CLASS_NAMES.get(pred_label, "KHÔNG XÁC ĐỊNH")
    signal = SIGNAL_RECOMMENDATIONS.get(pred_label, "NẮM GIỮ (HOLD)")

    prob_dict = {
        CLASS_NAMES[0]: round(float(probs[0]), 4),
        CLASS_NAMES[1]: round(float(probs[1]), 4),
        CLASS_NAMES[2]: round(float(probs[2]), 4),
    }

    return {
        "symbol": clean_sym,
        "date": latest_date,
        "current_price": round(latest_close, 2),
        "model_type": model_type.lower(),
        "predicted_label": pred_label,
        "class_name": class_name,
        "signal": signal,
        "probabilities": prob_dict,
        "horizon": "T+1",
    }


def predict_next_day(
    symbol: str = DEFAULT_SYMBOL,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    models_dir: Path = MODELS_DIR,
) -> dict[str, Any]:
    """
    Hàm giao tiếp tương thích ngược: gọi `predict_trend` với mô hình LSTM mặc định.
    """
    return predict_trend(
        symbol=symbol, model_type="lstm", seq_length=seq_length, models_dir=models_dir
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dự báo xu hướng cổ phiếu phiên tiếp theo (T+1).")
    parser.add_argument(
        "--symbol", type=str, default=DEFAULT_SYMBOL, help="Mã cổ phiếu (ví dụ: VIC, HPG)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="lstm",
        choices=["lstm", "lightgbm"],
        help="Loại mô hình (lstm hoặc lightgbm)",
    )
    args = parser.parse_args()

    try:
        res = predict_trend(symbol=args.symbol, model_type=args.model)
        print("\n" + "=" * 55)
        print(f"KẾT QUẢ DỰ BÁO XU HƯỚNG T+1 CHO MÃ {res['symbol']} ({res['model_type'].upper()})")
        print("=" * 55)
        print(f"Ngày gần nhất:       {res['date']}")
        print(f"Giá đóng cửa:        {res['current_price']:,.2f} VNĐ")
        print(f"Dự báo xu hướng:     {res['class_name']} (Nhãn {res['predicted_label']})")
        print(f"Khuyến nghị:         {res['signal']}")
        print("Phân bổ xác suất:")
        for k, v in res["probabilities"].items():
            print(f"  - {k:<10}: {v * 100:.2f}%")
        print("=" * 55)
    except (FileNotFoundError, ValueError, RuntimeError, KeyError) as err:
        print(f"Lỗi: {err}")
