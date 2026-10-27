"""Module huấn luyện và kiểm định hệ thống mô hình dự báo xu hướng thị trường chứng khoán.

Bao gồm hệ thống đối chứng 3 tầng qua 3 cửa sổ Walk-Forward Expanding Windows:
1. Naive Baseline (DummyClassifier - đoán lớp đa số)
2. LightGBM Classifier (Gradient Boosting dạng bảng đa mã)
3. PyTorch Global LSTM Classifier (Mạng nơ-ron học sâu chuỗi 3D đa biến với Warm-up)
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
from sklearn.dummy import DummyClassifier
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
    prepare_all_windows,
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


def train_naive_baseline(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str] = ALL_FEATURE_COLS,
) -> tuple[DummyClassifier, dict[str, Any], np.ndarray]:
    """
    Huấn luyện và đánh giá mô hình Naive Baseline (DummyClassifier) làm mốc sàn đối chứng.
    """
    X_tr = train_df[feature_cols]
    y_tr = train_df["Label"].values
    X_te = test_df[feature_cols]
    y_te = test_df["Label"].values

    # Loại bỏ nhãn ranh giới -1
    X_tr, y_tr = drop_ignored_labels(X_tr, y_tr)
    X_te, y_te = drop_ignored_labels(X_te, y_te)

    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(X_tr, y_tr)
    y_pred = dummy.predict(X_te)

    metrics = evaluate_predictions(y_te, y_pred)
    return dummy, metrics, y_pred


def train_lightgbm_window(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str] = ALL_FEATURE_COLS,
    custom_params: dict[str, Any] | None = None,
    early_stopping_rounds: int = DEFAULT_EARLY_STOPPING_ROUNDS,
) -> tuple[lgb.LGBMClassifier, dict[str, Any], np.ndarray]:
    """
    Huấn luyện mô hình LightGBM Classifier trên một cửa sổ Walk-Forward với Early Stopping.
    """
    X_tr, y_tr = drop_ignored_labels(train_df[feature_cols], train_df["Label"].values)
    X_va, y_va = drop_ignored_labels(val_df[feature_cols], val_df["Label"].values)
    X_te, y_te = drop_ignored_labels(test_df[feature_cols], test_df["Label"].values)

    model = create_lightgbm_model(custom_params)
    model.fit(
        X_tr,
        y_tr,
        eval_set=[(X_va, y_va)],
        callbacks=[lgb.early_stopping(stopping_rounds=early_stopping_rounds, verbose=False)],
    )

    y_pred = model.predict(X_te)
    metrics = evaluate_predictions(y_te, y_pred)
    return model, metrics, y_pred


def train_lstm_window(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    val_warmup_df: pd.DataFrame | None = None,
    test_warmup_df: pd.DataFrame | None = None,
    feature_cols: list[str] = ALL_FEATURE_COLS,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    hidden_size: int = DEFAULT_LSTM_HIDDEN_SIZE,
    num_layers: int = DEFAULT_LSTM_NUM_LAYERS,
    dropout: float = DEFAULT_LSTM_DROPOUT,
    epochs: int = DEFAULT_LSTM_EPOCHS,
    lr: float = DEFAULT_LSTM_LR,
    batch_size: int = DEFAULT_LSTM_BATCH_SIZE,
    weight_decay: float = DEFAULT_LSTM_WEIGHT_DECAY,
    random_seed: int = RANDOM_SEED,
    device: torch.device | None = None,
) -> tuple[GlobalLSTMClassifier, dict[str, Any], np.ndarray]:
    """
    Huấn luyện mô hình PyTorch Global LSTM Classifier trên một cửa sổ Walk-Forward.
    Bảo toàn 100% mẫu cho Val và Test nhờ kỹ thuật Warm-up sequence tail.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Tạo chuỗi trượt 3D kèm Warm-up
    X_tr_seq, y_tr_seq = create_multivariate_sequences(train_df, None, feature_cols, seq_length)
    X_va_seq, y_va_seq = create_multivariate_sequences(
        val_df, val_warmup_df, feature_cols, seq_length
    )
    X_te_seq, y_te_seq = create_multivariate_sequences(
        test_df, test_warmup_df, feature_cols, seq_length
    )

    # Loại bỏ nhãn ranh giới -1
    X_tr_seq, y_tr_seq = drop_ignored_labels(X_tr_seq, y_tr_seq)
    X_va_seq, y_va_seq = drop_ignored_labels(X_va_seq, y_va_seq)
    X_te_seq, y_te_seq = drop_ignored_labels(X_te_seq, y_te_seq)

    # Khởi tạo DataLoader an toàn với torch.from_numpy (Zero-copy, tránh xung đột OpenMP)
    tr_loader = DataLoader(
        TensorDataset(
            torch.from_numpy(np.ascontiguousarray(X_tr_seq)),
            torch.from_numpy(np.ascontiguousarray(y_tr_seq)),
        ),
        batch_size=batch_size,
        shuffle=True,
    )
    va_loader = DataLoader(
        TensorDataset(
            torch.from_numpy(np.ascontiguousarray(X_va_seq)),
            torch.from_numpy(np.ascontiguousarray(y_va_seq)),
        ),
        batch_size=batch_size,
        shuffle=False,
    )
    te_loader = DataLoader(
        TensorDataset(
            torch.from_numpy(np.ascontiguousarray(X_te_seq)),
            torch.from_numpy(np.ascontiguousarray(y_te_seq)),
        ),
        batch_size=batch_size,
        shuffle=False,
    )

    # Khởi tạo mạng & Optimizer
    torch.manual_seed(random_seed)
    np.random.seed(random_seed)
    model = GlobalLSTMClassifier(
        input_size=len(feature_cols),
        hidden_size=hidden_size,
        num_layers=num_layers,
        num_classes=NUM_CLASSES,
        dropout=dropout,
    ).to(device)

    # Tính toán trọng số lớp cân bằng chống hiện tượng dự báo sụp đổ về lớp đa số
    classes = np.unique(y_tr_seq)
    weights = compute_class_weight(class_weight="balanced", classes=classes, y=y_tr_seq)
    class_weights = torch.tensor(weights, dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    best_val_loss = float("inf")
    best_weights = copy.deepcopy(model.state_dict())

    # Vòng lặp huấn luyện với Early Stopping theo validation loss
    for _ in range(epochs):
        model.train()
        for bx, by in tr_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            logits = model(bx)
            loss = criterion(logits, by)
            loss.backward()
            optimizer.step()

        model.eval()
        vloss, vtotal = 0.0, 0
        with torch.no_grad():
            for bx, by in va_loader:
                bx, by = bx.to(device), by.to(device)
                logits = model(bx)
                vloss += criterion(logits, by).item() * len(by)
                vtotal += len(by)
        avg_vloss = vloss / max(vtotal, 1)

        if avg_vloss < best_val_loss:
            best_val_loss = avg_vloss
            best_weights = copy.deepcopy(model.state_dict())

    # Khôi phục trọng số tối ưu nhất
    model.load_state_dict(best_weights)
    model.eval()

    # Dự báo trên tập kiểm thử
    test_preds = []
    with torch.no_grad():
        for bx, _ in te_loader:
            bx = bx.to(device)
            preds = torch.argmax(model(bx), dim=1)
            test_preds.extend(preds.cpu().numpy())

    y_pred_arr = np.array(test_preds, dtype=np.int64)
    metrics = evaluate_predictions(y_te_seq, y_pred_arr)
    return model, metrics, y_pred_arr


def train_walk_forward_pipeline(
    df: pd.DataFrame | None = None,
    epochs: int = DEFAULT_LSTM_EPOCHS,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    save_artifacts: bool = True,
    models_dir: Path = MODELS_DIR,
    horizon: int = DEFAULT_HORIZON_DAYS,
    threshold: float = DEFAULT_TREND_THRESHOLD_3D,
) -> dict[str, Any]:
    """
    Quy trình điều phối toàn diện huấn luyện và kiểm định Walk-Forward 3 cửa sổ:
    1. Chuẩn bị dữ liệu bảng đa mã và nhãn xu hướng 3 lớp có ngưỡng (chuẩn chu kỳ T+3).
    2. Chia 3 cửa sổ Walk-Forward chuẩn hóa độc lập (Zero Lookahead Bias).
    3. Huấn luyện đối chứng Naive Baseline -> LightGBM -> PyTorch LSTM.
    4. Tính toán bảng tổng hợp Mean ± Std qua 3 cửa sổ.
    5. Lưu trữ artifact trọng số mô hình, scaler và báo cáo metrics.
    """
    # Bước 1: Nạp và chuẩn bị dữ liệu
    if df is None:
        try:
            raw_panel = load_panel_dataset()
        except FileNotFoundError:
            logger.info("Chưa có panel dataset, đang khởi tạo build_panel_dataset()...")
            raw_panel = build_panel_dataset()

        feat_df = compute_features_per_symbol(raw_panel, drop_na=True)
        study_df = apply_study_window(feat_df)
        labeled_df = create_multi_day_labels(study_df, horizon=horizon, threshold=threshold)
    else:
        labeled_df = df.copy()

    # Bước 2: Chuẩn bị 3 cửa sổ Walk-Forward
    windows = prepare_all_windows(
        df=labeled_df,
        seq_length=seq_length,
        purge_boundary=True,
    )

    naive_window_results = []
    lgb_window_results = []
    lstm_window_results = []

    trained_lgb_models = []
    trained_lstm_models = []

    print("\n" + "=" * 80)
    print("BẮT ĐẦU HUẤN LUYỆN WALK-FORWARD VALIDATION (3 EXPANDING WINDOWS)")
    print("=" * 80)

    for i, win in enumerate(windows):
        win_name = win["name"]
        print(
            f"\n▶ Đang xử lý {win_name} (Train: {len(win['train'])} | Val: {len(win['val'])} | Test: {len(win['test'])})..."
        )

        # 1. Naive Baseline
        _, naive_metrics, _ = train_naive_baseline(win["train"], win["test"], ALL_FEATURE_COLS)
        naive_window_results.append({"window": win_name, **naive_metrics})
        print(
            f"  [1/3] Naive Baseline:  Accuracy = {naive_metrics['accuracy'] * 100:.2f}% | Macro F1 = {naive_metrics['macro_f1']:.4f}"
        )

        # 2. LightGBM Classifier
        lgb_model, lgb_metrics, _ = train_lightgbm_window(
            win["train"], win["val"], win["test"], ALL_FEATURE_COLS
        )
        lgb_window_results.append({"window": win_name, **lgb_metrics})
        trained_lgb_models.append(lgb_model)
        print(
            f"  [2/3] LightGBM Model:  Accuracy = {lgb_metrics['accuracy'] * 100:.2f}% | Macro F1 = {lgb_metrics['macro_f1']:.4f}"
        )

        # 3. PyTorch Global LSTM Classifier
        lstm_model, lstm_metrics, _ = train_lstm_window(
            train_df=win["train"],
            val_df=win["val"],
            test_df=win["test"],
            val_warmup_df=win.get("val_warmup"),
            test_warmup_df=win.get("test_warmup"),
            feature_cols=ALL_FEATURE_COLS,
            seq_length=seq_length,
            epochs=epochs,
        )
        lstm_window_results.append({"window": win_name, **lstm_metrics})
        trained_lstm_models.append(lstm_model)
        print(
            f"  [3/3] PyTorch LSTM:    Accuracy = {lstm_metrics['accuracy'] * 100:.2f}% | Macro F1 = {lstm_metrics['macro_f1']:.4f}"
        )

    # Bước 3: Tổng hợp Mean ± Std qua 3 cửa sổ
    naive_f1s = [r["macro_f1"] for r in naive_window_results]
    lgb_f1s = [r["macro_f1"] for r in lgb_window_results]
    lstm_f1s = [r["macro_f1"] for r in lstm_window_results]

    summary = {
        "naive": {
            "mean_macro_f1": float(np.mean(naive_f1s)),
            "std_macro_f1": float(np.std(naive_f1s)),
            "windows": naive_window_results,
        },
        "lightgbm": {
            "mean_macro_f1": float(np.mean(lgb_f1s)),
            "std_macro_f1": float(np.std(lgb_f1s)),
            "windows": lgb_window_results,
        },
        "lstm": {
            "mean_macro_f1": float(np.mean(lstm_f1s)),
            "std_macro_f1": float(np.std(lstm_f1s)),
            "windows": lstm_window_results,
        },
    }

    print("\n" + "=" * 80)
    print("BẢNG TỔNG KẾT SO SÁNH HIỆU NĂNG QUA 3 CỬA SỔ WALK-FORWARD (MACRO F1)")
    print("=" * 80)
    print(
        f"1. Naive Baseline:  Mean Macro F1 = {summary['naive']['mean_macro_f1']:.4f} ± {summary['naive']['std_macro_f1']:.4f}"
    )
    print(
        f"2. LightGBM:        Mean Macro F1 = {summary['lightgbm']['mean_macro_f1']:.4f} ± {summary['lightgbm']['std_macro_f1']:.4f}"
    )
    print(
        f"3. PyTorch LSTM:    Mean Macro F1 = {summary['lstm']['mean_macro_f1']:.4f} ± {summary['lstm']['std_macro_f1']:.4f}"
    )

    # Bước 4: Lưu trữ Artifacts mô hình Cửa sổ 3 (Cửa sổ đại diện cho sản xuất)
    if save_artifacts:
        models_dir.mkdir(parents=True, exist_ok=True)

        # Lưu checkpoint weights PyTorch LSTM
        best_lstm = trained_lstm_models[-1]
        lstm_path = models_dir / "global_lstm_classifier.pth"
        torch.save(best_lstm.state_dict(), lstm_path)
        print(f"\nĐã lưu checkpoint PyTorch LSTM: {lstm_path}")

        # Lưu model LightGBM (ưu tiên định dạng Booster native text chống xung đột OpenMP)
        best_lgb = trained_lgb_models[-1]
        lgb_txt_path = models_dir / "lightgbm_classifier.txt"
        best_lgb.booster_.save_model(str(lgb_txt_path))
        print(f"Đã lưu model LightGBM native: {lgb_txt_path}")

        lgb_path = models_dir / "lightgbm_classifier.pkl"
        with open(lgb_path, "wb") as f:
            import pickle

            pickle.dump(best_lgb, f)
        print(f"Đã lưu model LightGBM pickle: {lgb_path}")

        # Lưu Scaler của Cửa sổ 3
        scaler_path = models_dir / "scaler_window3.pkl"
        with open(scaler_path, "wb") as f:
            import pickle

            pickle.dump(windows[-1]["scaler"], f)
        print(f"Đã lưu Scaler Cửa sổ 3: {scaler_path}")

        # Lưu Feature Importance của LightGBM
        feat_imp = {
            col: int(imp) for col, imp in zip(ALL_FEATURE_COLS, best_lgb.feature_importances_)
        }
        feat_imp_path = models_dir / "feature_importance.json"
        with open(feat_imp_path, "w", encoding="utf-8") as f:
            json.dump(feat_imp, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu Feature Importance: {feat_imp_path}")

        # Lưu báo cáo tổng kết metrics
        metrics_path = models_dir / "training_metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu Báo cáo metrics: {metrics_path}")

    return summary


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
    Hàm giao tiếp tương thích ngược: chạy pipeline Walk-Forward và trả về mô hình Global LSTM.
    """
    summary = train_walk_forward_pipeline(epochs=epochs, models_dir=models_dir)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = GlobalLSTMClassifier().to(device)
    lstm_path = models_dir / "global_lstm_classifier.pth"
    if lstm_path.exists():
        model.load_state_dict(torch.load(lstm_path, map_location=device))
    return model, summary["lstm"]["mean_macro_f1"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Huấn luyện mô hình VN Stock (Walk-Forward hoặc Production T+3)."
    )
    parser.add_argument("--symbol", type=str, default=None, help="Mã cổ phiếu (tùy chọn)")
    parser.add_argument(
        "--scope",
        type=str,
        default="VN30",
        choices=["VN30", "CORE"],
        help="Phạm vi danh mục huấn luyện: 'VN30' (30 mã rổ chỉ số) hoặc 'CORE' (5 mã cốt lõi)",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Huấn luyện mô hình thực chiến (100% dữ liệu đến T/T-1, nhãn T+3)",
    )
    parser.add_argument(
        "--horizon", type=int, default=3, help="Chân trời dự báo (mặc định 3 phiên T+3)"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.02, help="Ngưỡng biến động nhãn (mặc định 0.02 = 2%)"
    )
    parser.add_argument(
        "--val-buffer", type=int, default=40, help="Số ngày đệm validation cho Early Stopping"
    )
    parser.add_argument(
        "--epochs", type=int, default=DEFAULT_LSTM_EPOCHS, help="Số epochs huấn luyện LSTM"
    )
    parser.add_argument(
        "--seq-length", type=int, default=DEFAULT_SEQ_LENGTH, help="Độ dài chuỗi quan sát"
    )
    args = parser.parse_args()

    if args.production:
        train_symbols = [args.symbol.upper()] if args.symbol else args.scope
        train_production_model(
            symbols=train_symbols,
            horizon=args.horizon,
            threshold=args.threshold,
            val_buffer_days=args.val_buffer,
            epochs=args.epochs,
            seq_length=args.seq_length,
        )
    else:
        train_walk_forward_pipeline(epochs=args.epochs, seq_length=args.seq_length)

