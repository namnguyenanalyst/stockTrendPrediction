"""Module huấn luyện hệ thống mô hình dự báo xu hướng thị trường chứng khoán thực chiến.

Kiến trúc Huấn luyện Thực chiến Liên tục (Continuous Production Retraining):
1. LightGBM Classifier (Gradient Boosting dạng bảng đa mã)
2. PyTorch Global LSTM Classifier (Mạng nơ-ron học sâu chuỗi 3D đa biến với Warm-up)
Tự động đồng bộ nến mới, huấn luyện trên toàn bộ lịch sử đến T-40, thẩm định trên 40 phiên gần nhất và xuất 4 artifacts sản xuất.
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import argparse
import copy
from datetime import datetime
import json
import logging
from pathlib import Path
import pickle
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.utils.class_weight import compute_class_weight
import torch
from torch import nn, optim
from torch.utils.data import DataLoader, TensorDataset
import lightgbm as lgb

from vn_stock.config import (
    DEFAULT_EARLY_STOPPING_ROUNDS,
    DEFAULT_HORIZON_DAYS,
    DEFAULT_LABEL_THRESHOLD,
    DEFAULT_LSTM_BATCH_SIZE,
    DEFAULT_LSTM_DROPOUT,
    DEFAULT_LSTM_EPOCHS,
    DEFAULT_LSTM_HIDDEN_SIZE,
    DEFAULT_LSTM_LR,
    DEFAULT_LSTM_NUM_LAYERS,
    DEFAULT_LSTM_WEIGHT_DECAY,
    DEFAULT_SEQ_LENGTH,
    DEFAULT_TREND_THRESHOLD_3D,
    MODELS_DIR,
    NUM_CLASSES,
    RANDOM_SEED,
)
from vn_stock.data_ingestion import build_panel_dataset, load_panel_dataset
from vn_stock.features import (
    ALL_FEATURE_COLS,
    compute_features_per_symbol,
    create_multivariate_sequences,
)
from vn_stock.modeling.model import GlobalLSTMClassifier, create_lightgbm_model
from vn_stock.splitting_data import (
    apply_study_window,
    create_labels_per_symbol,
    create_multi_day_labels,
    drop_ignored_labels,
    prepare_production_training_data,
)

logger = logging.getLogger(__name__)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    """
    Tính toán bộ chỉ số đo lường hiệu năng phân loại đa lớp chống mất cân bằng.

    Args:
        y_true: Mảng 1D nhãn thực tế.
        y_pred: Mảng 1D nhãn dự báo.

    Returns:
        dict chứa accuracy, macro_f1, weighted_f1, precision_macro, recall_macro và confusion_matrix.
    """
    acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    precision_m = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    recall_m = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    cm = confusion_matrix(y_true, y_pred).tolist()

    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "precision_macro": precision_m,
        "recall_macro": recall_m,
        "confusion_matrix": cm,
    }



def train_production_model(
    symbols: list[str] | str | None = None,
    horizon: int = 3,
    threshold: float = 0.02,
    val_buffer_days: int = 40,
    epochs: int = DEFAULT_LSTM_EPOCHS,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    save_artifacts: bool = True,
    models_dir: Path = MODELS_DIR,
) -> dict[str, Any]:
    """
    Huấn luyện mô hình thực chiến (Production Model) phục vụ dự báo trực tuyến:
    1. Tự động đồng bộ và nạp dữ liệu tới phiên T-1 (hoặc T nếu đã qua 15:00 ATC).
    2. Hỗ trợ huấn luyện trên 5 mã cốt lõi (CORE) hoặc toàn bộ 30 mã VN30 (VN30).
    3. Tạo nhãn xu hướng đa phiên (mặc định T+3 với ngưỡng +-2.0%).
    4. Trích 40 phiên gần nhất làm Validation Buffer để Early Stopping chống overfitting.
    5. Huấn luyện LightGBM và PyTorch Global LSTM trên toàn bộ mẫu.
    6. Lưu trữ artifacts sản xuất và cập nhật mô hình mặc định.
    """
    from vn_stock.config import DEFAULT_SYMBOLS, VN30_SYMBOLS

    if symbols is None or (isinstance(symbols, str) and symbols.upper() in ["VN30", "ALL"]):
        target_symbols = list(VN30_SYMBOLS)
        scope_name = "VN30"
    elif isinstance(symbols, str) and symbols.upper() == "CORE":
        target_symbols = list(DEFAULT_SYMBOLS)
        scope_name = "CORE"
    elif isinstance(symbols, str):
        target_symbols = [symbols.upper()]
        scope_name = "SINGLE"
    elif isinstance(symbols, list):
        target_symbols = [s.upper() for s in symbols]
        scope_name = (
            "VN30"
            if len(target_symbols) >= 20
            else ("CORE" if set(target_symbols) == set(DEFAULT_SYMBOLS) else "CUSTOM")
        )
    else:
        target_symbols = list(VN30_SYMBOLS)
        scope_name = "VN30"

    logger.info("=== BẮT ĐẦU HUẤN LUYỆN MÔ HÌNH THỰC CHIẾN (PRODUCTION MODEL) ===")
    logger.info(
        "Cấu hình: Phạm vi=%s (%d mã), Horizon=T+%d, Ngưỡng=%.1f%%, ValBuffer=%d phiên",
        scope_name,
        len(target_symbols),
        horizon,
        threshold * 100,
        val_buffer_days,
    )

    # Bước 1: Tự động đồng bộ nến thị trường mới nhất và nạp panel dataset
    from vn_stock.data_ingestion import sync_latest_market_data

    try:
        sync_latest_market_data(symbols=target_symbols, force=False)
    except Exception as sync_exc:
        logger.warning("Không thể tự động đồng bộ nến mới trước khi huấn luyện: %s", sync_exc)

    raw_panel = build_panel_dataset(symbols=target_symbols, force_refresh=False)
    feat_df = compute_features_per_symbol(raw_panel, drop_na=True)
    study_df = apply_study_window(feat_df)

    # Bước 2: Tạo nhãn xu hướng đa phiên T+horizon
    labeled_df = create_multi_day_labels(study_df, horizon=horizon, threshold=threshold)

    # Bước 3: Phân chia Train và Val Buffer không rò rỉ
    splits = prepare_production_training_data(
        labeled_df,
        val_buffer_days=val_buffer_days,
        seq_length=seq_length,
    )
    train_df = splits["train"]
    val_df = splits["val"]
    val_warmup = splits["val_warmup"]
    scaler = splits["scaler"]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Bước 4: Huấn luyện LightGBM
    X_tr_lgb, y_tr_lgb = drop_ignored_labels(train_df[ALL_FEATURE_COLS], train_df["Label"].values)
    X_va_lgb, y_va_lgb = drop_ignored_labels(val_df[ALL_FEATURE_COLS], val_df["Label"].values)

    lgb_model = create_lightgbm_model()
    lgb_model.fit(
        X_tr_lgb,
        y_tr_lgb,
        eval_set=[(X_va_lgb, y_va_lgb)],
        callbacks=[lgb.early_stopping(stopping_rounds=DEFAULT_EARLY_STOPPING_ROUNDS, verbose=False)],
    )
    y_pred_lgb = lgb_model.predict(X_va_lgb)
    lgb_metrics = evaluate_predictions(y_va_lgb, y_pred_lgb)
    logger.info(
        "LightGBM Validation F1: %.4f, Acc: %.4f",
        lgb_metrics["macro_f1"],
        lgb_metrics["accuracy"],
    )

    # Bước 5: Huấn luyện PyTorch Global LSTM
    X_tr_seq, y_tr_seq = create_multivariate_sequences(train_df, None, ALL_FEATURE_COLS, seq_length)
    X_va_seq, y_va_seq = create_multivariate_sequences(val_df, val_warmup, ALL_FEATURE_COLS, seq_length)

    X_tr_seq, y_tr_seq = drop_ignored_labels(X_tr_seq, y_tr_seq)
    X_va_seq, y_va_seq = drop_ignored_labels(X_va_seq, y_va_seq)

    tr_loader = DataLoader(
        TensorDataset(
            torch.from_numpy(np.ascontiguousarray(X_tr_seq)),
            torch.from_numpy(np.ascontiguousarray(y_tr_seq)),
        ),
        batch_size=DEFAULT_LSTM_BATCH_SIZE,
        shuffle=True,
    )
    va_loader = DataLoader(
        TensorDataset(
            torch.from_numpy(np.ascontiguousarray(X_va_seq)),
            torch.from_numpy(np.ascontiguousarray(y_va_seq)),
        ),
        batch_size=DEFAULT_LSTM_BATCH_SIZE,
        shuffle=False,
    )

    torch.manual_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    lstm_model = GlobalLSTMClassifier(
        input_size=len(ALL_FEATURE_COLS),
        hidden_size=DEFAULT_LSTM_HIDDEN_SIZE,
        num_layers=DEFAULT_LSTM_NUM_LAYERS,
        num_classes=NUM_CLASSES,
        dropout=DEFAULT_LSTM_DROPOUT,
    ).to(device)

    classes = np.unique(y_tr_seq)
    weights = compute_class_weight(class_weight="balanced", classes=classes, y=y_tr_seq)
    class_weights = torch.tensor(weights, dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.Adam(lstm_model.parameters(), lr=DEFAULT_LSTM_LR, weight_decay=DEFAULT_LSTM_WEIGHT_DECAY)

    best_vloss = float("inf")
    best_weights = copy.deepcopy(lstm_model.state_dict())

    for _ in range(epochs):
        lstm_model.train()
        for bx, by in tr_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            logits = lstm_model(bx)
            loss = criterion(logits, by)
            loss.backward()
            optimizer.step()

        lstm_model.eval()
        vloss, vtotal = 0.0, 0
        with torch.no_grad():
            for bx, by in va_loader:
                bx, by = bx.to(device), by.to(device)
                logits = lstm_model(bx)
                vloss += criterion(logits, by).item() * len(by)
                vtotal += len(by)
        avg_vloss = vloss / max(vtotal, 1)
        if avg_vloss < best_vloss:
            best_vloss = avg_vloss
            best_weights = copy.deepcopy(lstm_model.state_dict())

    lstm_model.load_state_dict(best_weights)
    lstm_model.eval()

    val_preds = []
    with torch.no_grad():
        for bx, _ in va_loader:
            bx = bx.to(device)
            preds = torch.argmax(lstm_model(bx), dim=1)
            val_preds.extend(preds.cpu().numpy())
    lstm_metrics = evaluate_predictions(y_va_seq, np.array(val_preds, dtype=np.int64))
    logger.info(
        "PyTorch LSTM Validation F1: %.4f, Acc: %.4f",
        lstm_metrics["macro_f1"],
        lstm_metrics["accuracy"],
    )

    # Bước 6: Lưu trữ Artifacts
    latest_date_val = raw_panel["Date"].max()
    latest_date_str = (
        latest_date_val.strftime("%Y-%m-%d")
        if hasattr(latest_date_val, "strftime")
        else str(latest_date_val)
    )
    summary = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "scope": scope_name,
        "symbols_count": len(target_symbols),
        "symbols": target_symbols,
        "horizon": f"T+{horizon}",
        "horizon_days": horizon,
        "threshold": threshold,
        "val_buffer_days": val_buffer_days,
        "latest_market_date": latest_date_str,
        "train_samples": int(len(train_df)),
        "val_samples": int(len(val_df)),
        "total_samples": int(len(train_df) + len(val_df)),
        "lightgbm_metrics": lgb_metrics,
        "lstm_metrics": lstm_metrics,
    }

    if save_artifacts:
        models_dir.mkdir(parents=True, exist_ok=True)
        # 1. Lưu theo tên production cụ thể
        prod_lgb_txt = models_dir / f"production_lgb_t{horizon}.txt"
        prod_lgb_pkl = models_dir / f"production_lgb_t{horizon}.pkl"
        prod_lstm_pth = models_dir / f"production_lstm_t{horizon}.pth"
        prod_scaler_pkl = models_dir / f"production_scaler_t{horizon}.pkl"
        prod_info_json = models_dir / f"production_training_info_t{horizon}.json"

        lgb_model.booster_.save_model(str(prod_lgb_txt))
        with open(prod_lgb_pkl, "wb") as f:
            pickle.dump(lgb_model, f)
        torch.save(lstm_model.state_dict(), prod_lstm_pth)
        with open(prod_scaler_pkl, "wb") as f:
            pickle.dump(scaler, f)
        with open(prod_info_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # 2. Cập nhật model mặc định để duy trì tính tương thích
        default_lgb_txt = models_dir / "lightgbm_classifier.txt"
        default_lgb_pkl = models_dir / "lightgbm_classifier.pkl"
        default_lstm_pth = models_dir / "global_lstm_classifier.pth"
        default_scaler_pkl = models_dir / "scaler_window3.pkl"
        default_info_json = models_dir / "production_training_info.json"

        lgb_model.booster_.save_model(str(default_lgb_txt))
        with open(default_lgb_pkl, "wb") as f:
            pickle.dump(lgb_model, f)
        torch.save(lstm_model.state_dict(), default_lstm_pth)
        with open(default_scaler_pkl, "wb") as f:
            pickle.dump(scaler, f)
        with open(default_info_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # Lưu Feature Importance của LightGBM
        feat_imp = {
            col: int(imp) for col, imp in zip(ALL_FEATURE_COLS, lgb_model.feature_importances_)
        }
        feat_imp_path = models_dir / "feature_importance.json"
        with open(feat_imp_path, "w", encoding="utf-8") as f:
            json.dump(feat_imp, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] Đã lưu Artifacts mô hình thực chiến T+{horizon} tại: {models_dir}")
        print(f" - Dữ liệu thị trường chốt tới: {latest_date_str}")
        print(f" - LightGBM Validation Macro F1: {lgb_metrics['macro_f1']:.4f}")
        print(f" - PyTorch LSTM Validation Macro F1: {lstm_metrics['macro_f1']:.4f}")

    return summary


def train_lstm_model(
    symbol: str = "VIC",
    epochs: int = DEFAULT_LSTM_EPOCHS,
    models_dir: Path = MODELS_DIR,
) -> tuple[GlobalLSTMClassifier, float]:
    """
    Hàm giao tiếp: Huấn luyện mô hình thực chiến và trả về Global LSTM model.
    """
    summary = train_production_model(symbols=[symbol], epochs=epochs, models_dir=models_dir)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = GlobalLSTMClassifier().to(device)
    lstm_path = models_dir / "production_lstm_t3.pth"
    if not lstm_path.exists():
        lstm_path = models_dir / "global_lstm_classifier.pth"
    if lstm_path.exists():
        model.load_state_dict(torch.load(lstm_path, map_location=device))
    f1 = summary.get("lstm_metrics", {}).get("macro_f1", 0.0)
    return model, f1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Huấn luyện mô hình thực chiến VN Stock (Production Retraining T+3)."
    )
    parser.add_argument("--symbol", type=str, default=None, help="Mã cổ phiếu cụ thể (tùy chọn)")
    parser.add_argument(
        "--scope",
        type=str,
        default="VN30",
        choices=["VN30", "CORE"],
        help="Phạm vi danh mục huấn luyện: 'VN30' (30 mã rổ chỉ số) hoặc 'CORE' (5 mã cốt lõi)",
    )
    parser.add_argument(
        "--horizon", type=int, default=3, help="Chân trời dự báo (mặc định 3 phiên T+3)"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.02, help="Ngưỡng biến động nhãn (mặc định 0.02 = 2%)"
    )
    parser.add_argument(
        "--val-buffer", type=int, default=40, help="Số ngày đệm validation cho Early Stopping (mặc định 40 phiên)"
    )
    parser.add_argument(
        "--epochs", type=int, default=DEFAULT_LSTM_EPOCHS, help="Số epochs huấn luyện LSTM"
    )
    parser.add_argument(
        "--seq-length", type=int, default=DEFAULT_SEQ_LENGTH, help="Độ dài chuỗi quan sát (mặc định 20)"
    )
    args = parser.parse_args()

    train_symbols = [args.symbol.upper()] if args.symbol else args.scope
    train_production_model(
        symbols=train_symbols,
        horizon=args.horizon,
        threshold=args.threshold,
        val_buffer_days=args.val_buffer,
        epochs=args.epochs,
        seq_length=args.seq_length,
    )

