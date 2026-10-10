"""Kiểm thử tự động cho subpackage vn_stock.modeling."""

import pickle
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler
import torch

from vn_stock.config import NUM_CLASSES
from vn_stock.features import ALL_FEATURE_COLS, FEATURE_COLS

from vn_stock.modeling.model import (
    GlobalLSTMClassifier,
    PredictionModel,
    create_lightgbm_model,
)
from vn_stock.modeling.predict import (
    load_prediction_artifacts,
    predict_trend,
)
from vn_stock.modeling.train import (
    evaluate_predictions,
    train_lightgbm_window,
    train_lstm_window,
    train_naive_baseline,
)


@pytest.fixture
def mock_panel_data():
    """Tạo tập dữ liệu mock giả lập 2 mã cổ phiếu phục vụ kiểm thử nhanh."""
    dates = pd.date_range("2023-01-01", periods=60, freq="B")
    records = []
    for sym_idx, sym in enumerate(["VIC", "HPG"]):
        for i, dt in enumerate(dates):
            row = {
                "Date": dt,
                "Symbol": sym,
                "Close": 50.0 + i * 0.1 + sym_idx * 5.0,
                "Label": i % 3,  # Nhãn 0, 1, 2
            }
            # Tạo 13 đặc trưng số học
            for f in FEATURE_COLS:
                row[f] = np.sin(i * 0.2 + sym_idx) * 0.05
            row["Symbol_Code"] = sym_idx
            records.append(row)
    df = pd.DataFrame(records).sort_values(["Date", "Symbol"]).reset_index(drop=True)
    return df


def test_global_lstm_classifier_architecture():
    """Kiểm thử cấu trúc mạng GlobalLSTMClassifier và tính toán xác suất Softmax."""
    batch_size = 16
    seq_length = 20
    input_size = 14
    hidden_size = 32

    model = GlobalLSTMClassifier(
        input_size=input_size,
        hidden_size=hidden_size,
        num_layers=2,
        num_classes=NUM_CLASSES,
        dropout=0.1,
    )

    x = torch.randn(batch_size, seq_length, input_size)
    logits = model(x)
    assert logits.shape == (batch_size, NUM_CLASSES)

    probs = model.predict_proba(x)
    assert probs.shape == (batch_size, NUM_CLASSES)
    # Xác suất phải >= 0 và tổng mỗi dòng xấp xỉ 1.0
    assert torch.all(probs >= 0.0)
    assert torch.allclose(probs.sum(dim=-1), torch.ones(batch_size), atol=1e-5)


def test_legacy_prediction_model():
    """Kiểm tra mô hình PredictionModel cũ vẫn hoạt động tương thích ngược."""
    model = PredictionModel(input_size=1, hidden_size=16, num_layers=1, output_size=1)
    x = torch.randn(4, 10, 1)
    out = model(x)
    assert out.shape == (4, 1)


def test_create_lightgbm_model():
    """Kiểm tra factory tạo mô hình LightGBM Classifier."""
    model = create_lightgbm_model({"n_estimators": 50, "max_depth": 3})
    assert model.n_estimators == 50
    assert model.max_depth == 3
    assert model.n_jobs == 1


def test_evaluate_predictions():
    """Kiểm tra hàm đánh giá bộ chỉ số đa lớp."""
    y_true = np.array([0, 1, 2, 0, 1, 2, 1, 1])
    y_pred = np.array([0, 1, 2, 0, 2, 1, 1, 1])

    metrics = evaluate_predictions(y_true, y_pred)
    assert "accuracy" in metrics
    assert "macro_f1" in metrics
    assert "weighted_f1" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["accuracy"] == 6 / 8
    assert len(metrics["confusion_matrix"]) == 3


def test_train_naive_baseline(mock_panel_data):
    """Kiểm thử huấn luyện và đánh giá mô hình Naive Dummy."""
    train_df = mock_panel_data.iloc[:40]
    test_df = mock_panel_data.iloc[40:]

    dummy, metrics, y_pred = train_naive_baseline(train_df, test_df, ALL_FEATURE_COLS)
    assert metrics["accuracy"] >= 0.0
    assert len(y_pred) == len(test_df)


def test_train_lightgbm_window(mock_panel_data):
    """Kiểm thử huấn luyện LightGBM trên một cửa sổ mock."""
    train_df = mock_panel_data.iloc[:60]
    val_df = mock_panel_data.iloc[60:90]
    test_df = mock_panel_data.iloc[90:]

    model, metrics, y_pred = train_lightgbm_window(
        train_df,
        val_df,
        test_df,
        ALL_FEATURE_COLS,
        custom_params={"n_estimators": 10, "max_depth": 3, "min_child_samples": 2},
        early_stopping_rounds=5,
    )
    assert len(y_pred) == len(test_df)
    assert "macro_f1" in metrics
    assert hasattr(model, "feature_importances_")


def test_train_lstm_window(mock_panel_data):
    """Kiểm thử huấn luyện PyTorch LSTM trên một cửa sổ mock."""
    train_df = mock_panel_data.iloc[:60].copy()
    val_df = mock_panel_data.iloc[60:90].copy()
    test_df = mock_panel_data.iloc[90:].copy()

    model, metrics, y_pred = train_lstm_window(
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
        val_warmup_df=train_df,
        test_warmup_df=val_df,
        feature_cols=ALL_FEATURE_COLS,
        seq_length=10,
        hidden_size=16,
        num_layers=1,
        epochs=2,
        batch_size=16,
    )
    assert len(y_pred) > 0
    assert "macro_f1" in metrics
    assert isinstance(model, GlobalLSTMClassifier)


def test_predict_trend_with_artifacts(tmp_path, mock_panel_data):
    """Kiểm thử chức năng suy luận predict_trend với artifacts giả lập."""
    # 1. Tạo mock artifacts
    scaler = StandardScaler()
    scaler.fit(mock_panel_data[FEATURE_COLS])
    scaler_path = tmp_path / "scaler_window3.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    # Mock LSTM
    lstm_model = GlobalLSTMClassifier(input_size=len(ALL_FEATURE_COLS), hidden_size=16, num_layers=1)
    lstm_path = tmp_path / "global_lstm_classifier.pth"
    torch.save(lstm_model.state_dict(), lstm_path)

    # Mock LightGBM
    lgb_model = create_lightgbm_model({"n_estimators": 5, "min_child_samples": 2})
    lgb_model.fit(mock_panel_data[ALL_FEATURE_COLS], mock_panel_data["Label"])
    lgb_path = tmp_path / "lightgbm_classifier.pkl"
    with open(lgb_path, "wb") as f:
        pickle.dump(lgb_model, f)

    # 2. Test load_prediction_artifacts
    loaded_lstm, _ = load_prediction_artifacts(
        "lstm", models_dir=tmp_path, hidden_size=16, num_layers=1
    )
    assert isinstance(loaded_lstm, GlobalLSTMClassifier)

    loaded_lgb, _ = load_prediction_artifacts("lightgbm", models_dir=tmp_path)
    assert hasattr(loaded_lgb, "predict_proba")

    # 3. Test predict_trend với mock features
    with patch("vn_stock.modeling.predict.prepare_inference_features") as mock_prep:
        mock_prep.return_value = (mock_panel_data, 55.0, "2023-03-31")

        # Test dự báo với LSTM
        res_lstm = predict_trend(
            symbol="VIC",
            model_type="lstm",
            seq_length=10,
            models_dir=tmp_path,
            hidden_size=16,
            num_layers=1,
        )

        assert res_lstm["symbol"] == "VIC"
        assert res_lstm["model_type"] == "lstm"
        assert res_lstm["predicted_label"] in (0, 1, 2)
        assert res_lstm["class_name"] in ("GIẢM", "ĐI NGANG", "TĂNG")
        assert res_lstm["signal"] in ("BÁN (SELL)", "NẮM GIỮ (HOLD)", "MUA (BUY)")
        assert len(res_lstm["probabilities"]) == 3

        # Test dự báo với LightGBM
        res_lgb = predict_trend(symbol="VIC", model_type="lightgbm", seq_length=10, models_dir=tmp_path)
        assert res_lgb["symbol"] == "VIC"
        assert res_lgb["model_type"] == "lightgbm"
        assert res_lgb["predicted_label"] in (0, 1, 2)
        assert sum(res_lgb["probabilities"].values()) == pytest.approx(1.0, abs=1e-2)
