"""Kiểm thử tích hợp cho cơ chế Model Hot-reload và Khả năng chịu lỗi (Fault-tolerant Fallback).

Xác minh:
1. ModelCache tự động phát hiện artifact mới trên đĩa qua mtime polling và nạp lại mô hình mà không cần khởi động lại tiến trình.
2. Khi file artifact trên đĩa bị hỏng (corrupted binary), ModelCache ghi log lỗi và giữ lại mô hình cũ đang hoạt động trong RAM để tiếp tục phục vụ suy luận liên tục.
3. Kiểm thử hoạt động trơn tru cho cả hai kiến trúc: LightGBM Classifier và PyTorch Global LSTM Classifier.
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path
import pickle
import time

import numpy as np
import pytest
from sklearn.preprocessing import StandardScaler
import torch

from vn_stock.features import ALL_FEATURE_COLS
from vn_stock.modeling.model import GlobalLSTMClassifier
from vn_stock.modeling.predict import (
    clear_model_cache,
    load_prediction_artifacts,
)
from vn_stock.modeling.train import _atomic_save_artifact


@pytest.fixture(autouse=True)
def clean_cache_before_and_after():
    """Tự động xóa ModelCache trước và sau mỗi test case."""
    clear_model_cache()
    yield
    clear_model_cache()


def test_lightgbm_hot_reload_and_corrupted_fallback(tmp_path: Path):
    """Kiểm tra quy trình hot-reload LightGBM và fallback an toàn khi file artifact bị hỏng."""
    import lightgbm as lgb

    # 1. Khởi tạo Scaler chuẩn hóa
    scaler = StandardScaler()
    dummy_features = np.ones((10, len(ALL_FEATURE_COLS) - 1))
    scaler.fit(dummy_features)
    scaler_path = tmp_path / "production_scaler_t3.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    # 2. Tạo Mô hình V1: LightGBM huấn luyện dự báo nhãn 2 (TĂNG)
    X_v1 = np.random.randn(30, len(ALL_FEATURE_COLS))
    y_v1 = np.array([2] * 20 + [0] * 5 + [1] * 5)
    model_v1 = lgb.LGBMClassifier(n_estimators=10, random_state=42, verbose=-1, n_jobs=1)
    model_v1.fit(X_v1, y_v1)

    def _save_lgb(p: Path, m: lgb.LGBMClassifier) -> None:
        with open(p, "wb") as f:
            pickle.dump(m, f)

    lgb_pkl = tmp_path / "production_lgb_t3.pkl"
    _atomic_save_artifact(lgb_pkl, lambda p: _save_lgb(p, model_v1))

    # Nạp Model V1 lần đầu
    loaded_m1, loaded_s1 = load_prediction_artifacts(
        model_type="lightgbm",
        models_dir=tmp_path,
        horizon=3,
    )
    assert loaded_m1 is not None
    assert loaded_s1 is not None

    test_input = np.ones((1, len(ALL_FEATURE_COLS)))
    pred_v1 = loaded_m1.predict(test_input)[0]

    # 3. Tạo Mô hình V2: Huấn luyện dự báo nhãn 0 (GIẢM)
    time.sleep(0.05)  # Đảm bảo mtime mới hơn
    y_v2 = np.array([0] * 20 + [1] * 5 + [2] * 5)
    model_v2 = lgb.LGBMClassifier(n_estimators=10, random_state=100, verbose=-1, n_jobs=1)
    model_v2.fit(X_v1, y_v2)

    # Ghi đè nguyên tử Model V2 lên đĩa
    _atomic_save_artifact(lgb_pkl, lambda p: _save_lgb(p, model_v2))

    # Nạp lại: Không restart process, ModelCache phải nhận diện mtime thay đổi và hot-reload V2
    loaded_m2, _ = load_prediction_artifacts(
        model_type="lightgbm",
        models_dir=tmp_path,
        horizon=3,
    )
    assert loaded_m2 is not loaded_m1, "Model V2 phải là instance mới được hot-reload từ đĩa"
    pred_v2 = loaded_m2.predict(test_input)[0]
    assert pred_v2 != pred_v1, "Dự báo của Model V2 phải khác Model V1"

    # 4. Ghi đè file trên đĩa bằng dữ liệu rác/hỏng (Corrupted File)
    time.sleep(0.05)
    with open(lgb_pkl, "wb") as f:
        f.write(b"CORRUPTED_BINARY_NOT_A_VALID_PICKLE_OR_BOOSTER_123456789")

    # Nạp lại: Phải kích hoạt Fallback giữ Model V2 trong RAM, không quăng ngoại lệ làm crash
    loaded_fallback, _ = load_prediction_artifacts(
        model_type="lightgbm",
        models_dir=tmp_path,
        horizon=3,
    )
    assert loaded_fallback is loaded_m2, "Khi file hỏng, hệ thống phải giữ nguyên Model V2 từ RAM"
    pred_fallback = loaded_fallback.predict(test_input)[0]
    assert pred_fallback == pred_v2, "Dự báo vẫn hoạt động bình thường trên model cũ"


def test_lstm_hot_reload_and_corrupted_fallback(tmp_path: Path):
    """Kiểm tra quy trình hot-reload PyTorch LSTM và fallback an toàn khi file state_dict bị hỏng."""
    # 1. Scaler
    scaler = StandardScaler()
    scaler.fit(np.zeros((5, len(ALL_FEATURE_COLS) - 1)))
    scaler_path = tmp_path / "production_scaler_t3.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    # 2. LSTM Model V1
    model_v1 = GlobalLSTMClassifier(
        input_size=len(ALL_FEATURE_COLS),
        hidden_size=32,
        num_layers=2,
    )
    lstm_pth = tmp_path / "production_lstm_t3.pth"
    _atomic_save_artifact(lstm_pth, lambda p: torch.save(model_v1.state_dict(), p))

    loaded_m1, _ = load_prediction_artifacts(
        model_type="lstm",
        models_dir=tmp_path,
        horizon=3,
        hidden_size=32,
        num_layers=2,
    )
    assert loaded_m1 is not None

    # Lấy trọng số fc đầu tiên của V1 để so sánh
    w1 = loaded_m1.fc[0].weight.data.clone()

    # 3. Tạo LSTM Model V2 với trọng số khác biệt hoàn toàn
    time.sleep(0.05)
    model_v2 = GlobalLSTMClassifier(
        input_size=len(ALL_FEATURE_COLS),
        hidden_size=32,
        num_layers=2,
    )
    with torch.no_grad():
        model_v2.fc[0].weight.fill_(99.0)

    _atomic_save_artifact(lstm_pth, lambda p: torch.save(model_v2.state_dict(), p))

    # Hot-reload LSTM Model V2
    loaded_m2, _ = load_prediction_artifacts(
        model_type="lstm",
        models_dir=tmp_path,
        horizon=3,
        hidden_size=32,
        num_layers=2,
    )
    w2 = loaded_m2.fc[0].weight.data.clone()
    assert not torch.allclose(w1, w2), "Trọng số model V2 phải khác V1 sau khi hot-reload"
    assert torch.allclose(w2, torch.tensor(99.0)), "Trọng số model V2 phải là 99.0"

    # 4. Ghi đè file .pth bằng dữ liệu nhị phân hỏng
    time.sleep(0.05)
    with open(lstm_pth, "wb") as f:
        f.write(b"CORRUPTED_TORCH_STATE_DICT_HEADER_CRASH")

    # Gọi lại hàm nạp: Không được crash, phải giữ lại Model V2 đang có trong RAM
    loaded_fallback, _ = load_prediction_artifacts(
        model_type="lstm",
        models_dir=tmp_path,
        horizon=3,
        hidden_size=32,
        num_layers=2,
    )
    assert loaded_fallback is loaded_m2
    assert torch.allclose(loaded_fallback.fc[0].weight.data, torch.tensor(99.0))


def test_first_time_corrupted_artifact_raises(tmp_path: Path):
    """Khi chưa có model trong RAM mà file trên đĩa đã bị hỏng, phải raise exception hợp lệ."""
    scaler = StandardScaler()
    scaler.fit(np.zeros((5, len(ALL_FEATURE_COLS) - 1)))
    scaler_path = tmp_path / "production_scaler_t3.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    corrupt_pth = tmp_path / "production_lstm_t3.pth"
    with open(corrupt_pth, "wb") as f:
        f.write(b"CORRUPT_BYTES_NO_CACHE")

    with pytest.raises((RuntimeError, ValueError, EOFError, pickle.UnpicklingError)):
        load_prediction_artifacts(
            model_type="lstm",
            models_dir=tmp_path,
            horizon=3,
        )
