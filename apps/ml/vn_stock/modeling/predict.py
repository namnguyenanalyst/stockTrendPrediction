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
    DEFAULT_HORIZON_DAYS,
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
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    is_live_synced: bool = False,
) -> dict[str, Any]:
    """
    Thực hiện suy luận dự báo xu hướng thị trường chu kỳ T+3 (khớp với thời gian cổ phiếu về tài khoản)
    và xuất quỹ đạo dự phóng 3 phiên (T+1, T+2, T+3) hỗ trợ ra quyết định thực tế.

    Args:
        symbol: Mã cổ phiếu (ví dụ: 'VIC', 'HPG', 'FPT').
        model_type: 'lstm' hoặc 'lightgbm'.
        seq_length: Độ dài chuỗi quan sát (mặc định 20 phiên).
        models_dir: Thư mục chứa artifact mô hình.
        hidden_size: Số nơ-ron lớp ẩn nếu dùng LSTM.
        num_layers: Số lớp xếp chồng nếu dùng LSTM.
        horizon_days: Chu kỳ nắm giữ mục tiêu (mặc định 3 phiên).
        is_live_synced: Cờ đánh dấu dữ liệu đã được đồng bộ mới nhất từ SSI FastConnect.

    Returns:
        dict chứa:
        - symbol: Mã cổ phiếu
        - date: Ngày của phiên giao dịch gần nhất
        - data_as_of_date: Ngày chốt phiên dữ liệu căn cứ
        - current_price: Thị giá đóng cửa phiên gần nhất
        - model_type: Loại mô hình suy luận ('lstm' hoặc 'lightgbm')
        - predicted_label: Nhãn dự báo (0: Giảm, 1: Đi ngang, 2: Tăng)
        - class_name: Tên xu hướng ("GIẢM", "ĐI NGANG", "TĂNG")
        - signal: Tín hiệu hành động ("BÁN (SELL)", "NẮM GIỮ (HOLD)", "MUA (BUY)")
        - probabilities: Xác suất cho từng lớp {"GIẢM": p0, "ĐI NGANG": p1, "TĂNG": p2}
        - horizon: Kỳ hạn dự báo ("T+3")
        - horizon_days: Số ngày dự phóng (3)
        - is_live_synced: Trạng thái đồng bộ thời gian thực
        - trajectory: Danh sách dự phóng 3 phiên liên tiếp (T+1, T+2, T+3)
        - summary_guidance: Khuyến nghị thực chiến cho nhà đầu tư
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

    # Xây dựng Quỹ đạo dự phóng 3 phiên (Multi-step Trend Trajectory T+1 -> T+3 theo chuẩn FireAnt & vi cấu trúc T+2)
    p_down, p_hold, p_up = float(probs[0]), float(probs[1]), float(probs[2])
    trajectory = []

    # Phiên T+1: Mở vị thế tại giá Open
    pred_1 = int(np.argmax([p_down, p_hold, p_up]))
    trajectory.append({
        "day_offset": 1,
        "day_name": "T+1",
        "predicted_trend": CLASS_NAMES[pred_1],
        "signal": SIGNAL_RECOMMENDATIONS[pred_1],
        "confidence": round(float(max(p_down, p_hold, p_up)), 4),
        "probabilities": {
            CLASS_NAMES[0]: round(p_down, 4),
            CLASS_NAMES[1]: round(p_hold, 4),
            CLASS_NAMES[2]: round(p_up, 4),
        },
        "note": "Khớp lệnh mở vị thế tại giá mở cửa (Open) kèm trượt giá 0.05%.",
    })

    # Phiên T+2: Nắm giữ & chờ cổ phiếu về tài khoản (vị thế được bảo lưu)
    p_up_2 = p_up * 0.92 + 0.08 * (1.0 / 3.0)
    p_down_2 = p_down * 0.92 + 0.08 * (1.0 / 3.0)
    p_hold_2 = max(0.0, 1.0 - p_up_2 - p_down_2)
    pred_2 = int(np.argmax([p_down_2, p_hold_2, p_up_2]))
    trajectory.append({
        "day_offset": 2,
        "day_name": "T+2",
        "predicted_trend": CLASS_NAMES[pred_2],
        "signal": "NẮM GIỮ (HOLD)",
        "confidence": round(float(max(p_down_2, p_hold_2, p_up_2)), 4),
        "probabilities": {
            CLASS_NAMES[0]: round(p_down_2, 4),
            CLASS_NAMES[1]: round(p_hold_2, 4),
            CLASS_NAMES[2]: round(p_up_2, 4),
        },
        "note": "Cổ phiếu đang về tài khoản theo chu kỳ thanh toán T+2 (khóa vị thế bán theo luật sàn).",
    })

    # Phiên T+3: Cổ phiếu khả dụng trong tài khoản
    p_up_3 = p_up * 0.85 + 0.15 * (1.0 / 3.0)
    p_down_3 = p_down * 0.85 + 0.15 * (1.0 / 3.0)
    p_hold_3 = max(0.0, 1.0 - p_up_3 - p_down_3)
    pred_3 = int(np.argmax([p_down_3, p_hold_3, p_up_3]))
    trajectory.append({
        "day_offset": 3,
        "day_name": "T+3",
        "predicted_trend": CLASS_NAMES[pred_3],
        "signal": SIGNAL_RECOMMENDATIONS[pred_3],
        "confidence": round(float(max(p_down_3, p_hold_3, p_up_3)), 4),
        "probabilities": {
            CLASS_NAMES[0]: round(p_down_3, 4),
            CLASS_NAMES[1]: round(p_hold_3, 4),
            CLASS_NAMES[2]: round(p_up_3, 4),
        },
        "note": "Cổ phiếu khả dụng. Sẵn sàng hiện thực hóa lợi nhuận hoặc quản trị rủi ro.",
    })

    if pred_label == 2:
        guidance = "Khuyến nghị MUA: Dự báo chu kỳ T+3 duy trì xu hướng TĂNG. Lập kế hoạch mở vị thế tại Open T+1 và chốt lời tại T+3 sau khi trừ 0.4% thuế phí."
    elif pred_label == 0:
        guidance = "Cảnh báo GIẢM: Rủi ro điều chỉnh trong chu kỳ nắm giữ. Không mở vị thế mua mới; ưu tiên bảo toàn vốn."
    else:
        guidance = "Thị trường ĐI NGANG: Xu hướng tích lũy hẹp. Khuyến nghị giữ tiền mặt và quan sát điểm bứt phá."

    return {
        "symbol": clean_sym,
        "date": latest_date,
        "data_as_of_date": latest_date,
        "current_price": round(latest_close, 2),
        "model_type": model_type.lower(),
        "predicted_label": pred_label,
        "class_name": class_name,
        "signal": signal,
        "probabilities": prob_dict,
        "horizon": f"T+{horizon_days}",
        "horizon_days": horizon_days,
        "is_live_synced": is_live_synced,
        "trajectory": trajectory,
        "summary_guidance": guidance,
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
