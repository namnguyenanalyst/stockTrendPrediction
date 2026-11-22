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
import threading
from typing import Any

logger = logging.getLogger(__name__)

# Bộ nhớ đệm mô hình thread-safe trong RAM kèm mtime polling và fallback khi file hỏng
_cache_lock = threading.Lock()
_model_cache: dict[tuple, tuple[Any, Any, dict[str, int], dict]] = {}


def clear_model_cache() -> None:
    """Xóa bộ nhớ đệm mô hình trong RAM (phục vụ kiểm thử hot-reload)."""
    with _cache_lock:
        _model_cache.clear()


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
    SUPPORTED_INDICES,
)
from vn_stock.data_ingestion import (
    fetch_daily_index,
    fetch_stock_data,
    load_local_data,
    load_panel_dataset,
)
from vn_stock.features import (
    ALL_FEATURE_COLS,
    FEATURE_COLS,
    compute_features_per_symbol,
    transform_model_features,
)
from vn_stock.market_session import (
    get_future_trading_days,
    get_target_market_date,
    get_target_market_session_info,
)


def _resolve_artifact_paths(
    model_type: str,
    models_dir: Path,
    horizon: int,
) -> tuple[Path, Path]:
    """Xác định đường dẫn file scaler và model tương ứng trên đĩa."""
    m_type = model_type.lower()
    if m_type not in ("lstm", "lightgbm", "lgb"):
        raise ValueError(
            f"Loại mô hình không hợp lệ: '{model_type}'. Chỉ hỗ trợ 'lstm' hoặc 'lightgbm'."
        )

    scaler_path = models_dir / f"production_scaler_t{horizon}.pkl"
    if not scaler_path.exists() and horizon == 3:
        scaler_path = models_dir / "scaler_window3.pkl"
    if not scaler_path.exists():
        raise FileNotFoundError(
            f"Chưa tìm thấy scaler tại {models_dir}. Hãy chạy huấn luyện trước bằng `uv run python -m vn_stock.modeling.train --production`."
        )

    if m_type == "lstm":
        model_path = models_dir / f"production_lstm_t{horizon}.pth"
        if not model_path.exists() and horizon == 3:
            model_path = models_dir / "global_lstm_classifier.pth"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Chưa tìm thấy checkpoint LSTM tại {models_dir}. Hãy chạy huấn luyện trước!"
            )
        return scaler_path, model_path

    prod_txt = models_dir / f"production_lgb_t{horizon}.txt"
    prod_pkl = models_dir / f"production_lgb_t{horizon}.pkl"
    def_txt = models_dir / "lightgbm_classifier.txt"
    def_pkl = models_dir / "lightgbm_classifier.pkl"
    candidates = [prod_txt, prod_pkl] + ([def_txt, def_pkl] if horizon == 3 else [])
    for candidate in candidates:
        if candidate.exists():
            return scaler_path, candidate
    raise FileNotFoundError(
        f"Chưa tìm thấy model LightGBM tại {models_dir}. Hãy chạy huấn luyện trước!"
    )


def _load_raw_artifacts(
    model_type: str,
    scaler_path: Path,
    model_path: Path,
    hidden_size: int,
    num_layers: int,
) -> tuple[Any, Any]:
    """Đọc dữ liệu nhị phân từ đĩa để sinh model và scaler."""
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    m_type = model_type.lower()
    if m_type == "lstm":
        import torch

        from vn_stock.modeling.model import GlobalLSTMClassifier

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = GlobalLSTMClassifier(
            input_size=len(ALL_FEATURE_COLS),
            hidden_size=hidden_size,
            num_layers=num_layers,
        ).to(device)
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        return model, scaler

    if m_type in ("lightgbm", "lgb"):
        import lightgbm as lgb

        if str(model_path).endswith(".txt"):
            model = lgb.Booster(model_file=str(model_path))
        else:
            with open(model_path, "rb") as f:
                model = pickle.load(f)
        return model, scaler

    raise ValueError(f"Loại mô hình không hợp lệ: '{model_type}'")


def load_prediction_snapshot(
    model_type: str = "lstm",
    models_dir: Path = MODELS_DIR,
    horizon: int = 3,
    hidden_size: int = DEFAULT_LSTM_HIDDEN_SIZE,
    num_layers: int = DEFAULT_LSTM_NUM_LAYERS,
) -> tuple[Any, Any, dict]:
    """Load model/scaler/metadata from the same committed generation."""
    import json

    from vn_stock.modeling.artifacts import resolve_bundle

    models_dir = Path(models_dir)
    model_type = model_type.lower()
    if model_type.lower() not in ("lightgbm", "lgb", "lstm"):
        raise ValueError(f"Loại mô hình không hợp lệ: {model_type}")
    cache_key = (model_type.lower(), horizon, str(models_dir.resolve()), hidden_size, num_layers)
    with _cache_lock:
        cached = _model_cache.get(cache_key)
        try:
            pointer = models_dir / f"production_bundle_t{horizon}.json"
            if pointer.exists():
                files = resolve_bundle(models_dir, horizon)
                scaler_path = files[f"production_scaler_t{horizon}.pkl"]
                name = f"production_lstm_t{horizon}.pth" if model_type == "lstm" else f"production_lgb_t{horizon}.txt"
                model_path = files.get(name) or files[f"production_lgb_t{horizon}.pkl"]
                info_path = files[f"production_training_info_t{horizon}.json"]
            else:
                scaler_path, model_path = _resolve_artifact_paths(model_type, models_dir, horizon)
                info_path = models_dir / f"production_training_info_t{horizon}.json"
            paths = [scaler_path, model_path] + ([info_path] if info_path.exists() else [])
            mtimes = {str(p): p.stat().st_mtime_ns for p in paths}
            if cached is not None and cached[2] == mtimes:
                return cached[0], cached[1], cached[3]
            info = json.loads(info_path.read_text()) if info_path.exists() else {}
            model, scaler = _load_raw_artifacts(
                model_type=model_type, scaler_path=scaler_path, model_path=model_path,
                hidden_size=info.get("hidden_size", hidden_size),
                num_layers=info.get("num_layers", num_layers),
            )
            import hashlib
            generation = model_path.parent.name if pointer.exists() else hashlib.sha256(
                b"".join(hashlib.sha256(p.read_bytes()).digest() for p in paths)
            ).hexdigest()[:16]
            info = {**info, "artifact_generation": generation, "serving_status": "healthy"}
            _model_cache[cache_key] = (model, scaler, mtimes, info)
            return model, scaler, info
        except Exception:
            if cached is None:
                raise
            logger.exception("Artifact reload failed; retaining the complete cached generation.")
            return cached[0], cached[1], {**cached[3], "serving_status": "degraded_cached_generation"}


def load_prediction_artifacts(
    model_type: str = "lstm", models_dir: Path = MODELS_DIR, horizon: int = 3,
    hidden_size: int = DEFAULT_LSTM_HIDDEN_SIZE, num_layers: int = DEFAULT_LSTM_NUM_LAYERS,
) -> tuple[Any, Any]:
    model, scaler, _ = load_prediction_snapshot(
        model_type, models_dir, horizon, hidden_size, num_layers,
    )
    return model, scaler


def prepare_inference_features(
    symbol: str = DEFAULT_SYMBOL,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    raw_snapshot: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, float, str]:
    """
    Nạp dữ liệu lịch sử và tính toán bộ 13 đặc trưng tương đối + Symbol_Code cho một mã cổ phiếu hoặc chỉ số.

    Returns:
        tuple[df_features, latest_close_price, latest_date_str]
    """
    clean_sym = symbol.upper()
    df_raw = None
    if raw_snapshot is not None:
        required = {"Date", "Symbol", "Open", "High", "Low", "Close", "Volume", "VNINDEX_Return_1d"}
        if raw_snapshot.empty or not required.issubset(raw_snapshot.columns):
            raise ValueError("Incomplete explicit inference snapshot.")
        if set(raw_snapshot.Symbol.astype(str).str.upper()) != {clean_sym}:
            raise ValueError("Inference snapshot symbol does not match the request.")
        df_raw = raw_snapshot.copy(deep=True).sort_values("Date")
        if pd.to_datetime(df_raw.Date).duplicated().any():
            raise ValueError("Duplicate dates in explicit inference snapshot.")

    # 1. Hỗ trợ nạp chỉ số thị trường (VNINDEX, VN30, HNX30, ...)
    if raw_snapshot is None and clean_sym in SUPPORTED_INDICES:
        idx_df = load_local_data(clean_sym)
        if idx_df is not None:
            # Chuẩn hóa cột giá đóng cửa cho chỉ số nếu chỉ có VNINDEX_Close
            for c in idx_df.columns:
                if "Close" in c and c != "Close":
                    idx_df["Close"] = idx_df[c]
            if "Close" in idx_df.columns:
                if "Open" not in idx_df.columns:
                    idx_df["Open"] = idx_df["Close"]
                if "High" not in idx_df.columns:
                    idx_df["High"] = idx_df["Close"]
                if "Low" not in idx_df.columns:
                    idx_df["Low"] = idx_df["Close"]
                if "Volume" not in idx_df.columns:
                    idx_df["Volume"] = 10_000_000.0
                if "Symbol" not in idx_df.columns:
                    idx_df["Symbol"] = clean_sym
                if "VNINDEX_Return_1d" not in idx_df.columns:
                    idx_df["VNINDEX_Return_1d"] = idx_df["Close"].pct_change().fillna(0.0)
                df_raw = idx_df

        if df_raw is None or len(df_raw) < 50:
            try:
                raw_idx = fetch_daily_index(clean_sym)
                c_col = [c for c in raw_idx.columns if "Close" in c][0]
                idx_df = pd.DataFrame()
                idx_df["Date"] = raw_idx["Date"]
                idx_df["Close"] = raw_idx[c_col]
                idx_df["Open"] = idx_df["Close"]
                idx_df["High"] = idx_df["Close"]
                idx_df["Low"] = idx_df["Close"]
                idx_df["Volume"] = 10_000_000.0
                idx_df["Symbol"] = clean_sym
                idx_df["VNINDEX_Return_1d"] = idx_df["Close"].pct_change().fillna(0.0)
                df_raw = idx_df
            except Exception as e:
                logger.warning("Không thể nạp chỉ số %s: %s", clean_sym, e)

    target_date_str = get_target_market_date()
    target_dt = pd.to_datetime(target_date_str)

    # 2. Thử nạp từ panel interim (nếu đã đủ nến tới target_date)
    if df_raw is None:
        try:
            panel_cand = load_panel_dataset(symbols=[clean_sym])
            if panel_cand is not None and not panel_cand.empty:
                max_panel_dt = pd.to_datetime(panel_cand["Date"]).max()
                if max_panel_dt >= target_dt:
                    df_raw = panel_cand
                else:
                    logger.info(
                        "Dữ liệu panel của %s mới đến %s, mục tiêu là %s. Tự động đồng bộ nến mới từ SSI...",
                        clean_sym,
                        max_panel_dt.strftime("%Y-%m-%d"),
                        target_date_str,
                    )
        except (FileNotFoundError, ValueError, KeyError) as err:
            logger.debug("Không thể nạp dữ liệu từ panel: %s", err)

    # 3. Fallback nếu panel chưa có hoặc thiếu nến phiên mục tiêu: nạp/kéo từ SSI và merge VNINDEX
    if raw_snapshot is None and (df_raw is None or df_raw.empty or len(df_raw) < 200):
        try:
            stock_df = fetch_stock_data(clean_sym, end_date=target_date_str)
        except Exception as e:
            logger.warning("Không thể kéo SSI trực tiếp cho %s: %s. Dùng cache cục bộ.", clean_sym, e)
            stock_df = load_local_data(clean_sym)
            if stock_df is None:
                raise

        try:
            vnindex_df = fetch_daily_index("VNINDEX", end_date=target_date_str)
        except Exception as e:
            logger.warning("Không thể kéo VNINDEX từ SSI: %s. Dùng cache cục bộ.", e)
            vnindex_df = load_local_data("VNINDEX")

        if vnindex_df is not None:
            vn_clean = vnindex_df.sort_values("Date").copy()
            close_col = "VNINDEX_Close" if "VNINDEX_Close" in vn_clean.columns else "Close"
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

    df_raw = df_raw[pd.to_datetime(df_raw["Date"]) <= target_dt].copy()

    # Tính toán bộ đặc trưng
    df_feat = compute_features_per_symbol(df_raw, drop_na=True)
    if len(df_feat) < seq_length:
        raise ValueError(
            f"Mã {clean_sym} chỉ có {len(df_feat)} phiên hợp lệ, không đủ tối thiểu seq_length={seq_length}."
        )
    if not np.isfinite(df_feat[FEATURE_COLS].to_numpy()).all():
        raise ValueError(f"Mã {clean_sym} có đặc trưng không hữu hạn.")

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
    raw_snapshot: pd.DataFrame | None = None,
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
    model, scaler, training_info = load_prediction_snapshot(
        model_type=model_type,
        models_dir=models_dir,
        horizon=horizon_days,
        hidden_size=hidden_size,
        num_layers=num_layers,
    )
    if training_info.get("seq_length", seq_length) != seq_length:
        raise ValueError("Requested sequence length differs from the trained artifact.")
    df_feat, latest_close, latest_date = prepare_inference_features(
        clean_sym, seq_length=seq_length, raw_snapshot=raw_snapshot
    )

    # Chuẩn hóa 13 đặc trưng số học bằng scaler (Symbol_Code giữ nguyên)
    scaled_df = transform_model_features(df_feat, scaler)

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

    # Xây dựng Quỹ đạo dự phóng 3 phiên (Multi-step Trend Trajectory T+1 -> T+3 theo vi cấu trúc T+2.5 Việt Nam)
    p_down, p_hold, p_up = float(probs[0]), float(probs[1]), float(probs[2])
    future_days = get_future_trading_days(latest_date, count=horizon_days)
    trajectory = []

    # Phiên T+1: Khớp lệnh mở vị thế tại giá mở cửa (Open)
    pred_1 = int(np.argmax([p_down, p_hold, p_up]))
    trajectory.append({
        "day_offset": 1,
        "day_name": "T+1",
        "date": future_days[0]["date"] if future_days else "",
        "target_date": future_days[0]["date"] if future_days else "",
        "formatted_target_date": future_days[0]["formatted_date"] if future_days else "",
        "predicted_trend": CLASS_NAMES[pred_1],
        "signal": SIGNAL_RECOMMENDATIONS[pred_1],
        "confidence": round(float(max(p_down, p_hold, p_up)), 4),
        "probabilities": {
            CLASS_NAMES[0]: round(p_down, 4),
            CLASS_NAMES[1]: round(p_hold, 4),
            CLASS_NAMES[2]: round(p_up, 4),
        },
        "note": f"Khớp lệnh mở vị thế tại giá Open phiên {future_days[0]['formatted_date'] if future_days else 'T+1'} kèm trượt giá 0.05% nếu có tín hiệu MUA.",
    })

    # Phiên T+2: Nắm giữ & chờ cổ phiếu về tài khoản (vị thế được bảo lưu theo quy chế VSDC)
    trajectory.append({
        "day_offset": 2,
        "day_name": "T+2",
        "date": future_days[1]["date"] if len(future_days) > 1 else "",
        "target_date": future_days[1]["date"] if len(future_days) > 1 else "",
        "formatted_target_date": future_days[1]["formatted_date"] if len(future_days) > 1 else "",
        "predicted_trend": CLASS_NAMES[pred_1],
        "signal": "NẮM GIỮ (HOLD)",
        "confidence": round(float(max(p_down, p_hold, p_up)), 4),
        "probabilities": {
            CLASS_NAMES[0]: round(p_down, 4),
            CLASS_NAMES[1]: round(p_hold, 4),
            CLASS_NAMES[2]: round(p_up, 4),
        },
        "note": f"Cổ phiếu đang về tài khoản trong phiên {future_days[1]['formatted_date'] if len(future_days) > 1 else 'T+2'} (khóa vị thế bán theo quy chế VSDC).",
    })

    # Phiên T+3: Cổ phiếu khả dụng trong tài khoản - Đạt tới chân trời dự phóng đích
    trajectory.append({
        "day_offset": 3,
        "day_name": "T+3",
        "date": future_days[2]["date"] if len(future_days) > 2 else "",
        "target_date": future_days[2]["date"] if len(future_days) > 2 else "",
        "formatted_target_date": future_days[2]["formatted_date"] if len(future_days) > 2 else "",
        "predicted_trend": CLASS_NAMES[pred_label],
        "signal": SIGNAL_RECOMMENDATIONS[pred_label],
        "confidence": round(float(max(p_down, p_hold, p_up)), 4),
        "probabilities": {
            CLASS_NAMES[0]: round(p_down, 4),
            CLASS_NAMES[1]: round(p_hold, 4),
            CLASS_NAMES[2]: round(p_up, 4),
        },
        "note": f"Cổ phiếu khả dụng phiên {future_days[2]['formatted_date'] if len(future_days) > 2 else 'T+3'}. Sẵn sàng hiện thực hóa lợi nhuận hoặc quản trị rủi ro.",
    })

    if pred_label == 2:
        guidance = "Khuyến nghị MUA: Dự báo chu kỳ T+3 duy trì xu hướng TĂNG. Lập kế hoạch mở vị thế tại Open T+1 và chốt lời tại T+3 sau khi trừ 0.4% thuế phí."
    elif pred_label == 0:
        guidance = "Cảnh báo GIẢM: Rủi ro điều chỉnh trong chu kỳ nắm giữ T+3. Không mở vị thế mua mới; ưu tiên bảo toàn vốn."
    else:
        guidance = "Thị trường ĐI NGANG: Xu hướng tích lũy trong chu kỳ T+3. Khuyến nghị giữ tiền mặt và quan sát điểm bứt phá."

    for step, day in zip(trajectory, future_days):
        step["holiday_calendar_verified"] = day["holiday_calendar_verified"]

    session_info = get_target_market_session_info()

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
        "data_quality": {"historical_adjustment_status": "unverified",
                         "source_provenance": "SSI_request_snapshot" if raw_snapshot is not None
                         else "local_dataset_not_independently_verified"},
        "trajectory": trajectory,
        "summary_guidance": guidance,
        "training_info": training_info,
        "market_session_label": session_info["status_label"],
    }


def predict_next_day(
    symbol: str = DEFAULT_SYMBOL,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    models_dir: Path = MODELS_DIR,
) -> dict[str, Any]:
    """
    Hàm giao tiếp tương thích ngược: chuyển hướng gọi `predict_trend` chu kỳ T+3 mặc định.
    Khuyến nghị sử dụng trực tiếp `predict_trend(symbol=..., horizon_days=3)`.
    """
    return predict_trend(
        symbol=symbol, model_type="lstm", seq_length=seq_length, models_dir=models_dir
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Dự báo xu hướng cổ phiếu chu kỳ T+3 và Quỹ đạo 3 phiên (T+1 -> T+3)."
    )
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
        print(f"KẾT QUẢ DỰ BÁO XU HƯỚNG T+3 CHO MÃ {res['symbol']} ({res['model_type'].upper()})")
        print("=" * 55)
        print(f"Ngày gần nhất:       {res['date']}")
        print(f"Giá đóng cửa:        {res['current_price']:,.2f} VNĐ")
        print(f"Dự báo xu hướng:     {res['class_name']} (Nhãn {res['predicted_label']})")
        print(f"Khuyến nghị:         {res['signal']}")
        print(f"Kỳ hạn:              {res['horizon']} ({res['horizon_days']} phiên)")
        print("Phân bổ xác suất:")
        for k, v in res["probabilities"].items():
            print(f"  - {k:<10}: {v * 100:.2f}%")
        if res.get("trajectory"):
            print("-" * 55)
            print("Quỹ đạo dự phóng 3 phiên (T+1 -> T+3):")
            for step in res["trajectory"]:
                print(
                    f"  * {step['day_name']} ({step.get('date', 'N/A')}): {step['predicted_trend']} - {step['signal']}"
                )
        print("=" * 55)
    except (FileNotFoundError, ValueError, RuntimeError, KeyError) as err:
        print(f"Lỗi: {err}")
