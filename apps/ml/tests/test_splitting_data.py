"""Unit tests cho module phân chia dữ liệu thực chiến và chuẩn hóa chống rò rỉ (splitting_data.py)."""

import numpy as np
import pandas as pd
import pytest

from vn_stock.config import SYMBOL_TO_CODE
from vn_stock.features import ALL_FEATURE_COLS, FEATURE_COLS, create_multivariate_sequences
from vn_stock.splitting_data import (
    apply_study_window,
    create_labels_per_symbol,
    create_multi_day_labels,
    drop_ignored_labels,
    get_warmup_tail,
    prepare_production_training_data,
    scale_window,
)


@pytest.fixture
def dummy_panel_data():
    """Tạo bộ dữ liệu giả lập chuẩn gồm 3 mã cổ phiếu qua 200 ngày giao dịch liên tục."""
    dates = pd.date_range("2024-01-01", periods=200, freq="B")
    symbols = ["VIC", "HPG", "FPT"]
    rows = []

    for d in dates:
        for sym in symbols:
            row = {
                "Date": d,
                "Symbol": sym,
                "Symbol_Code": SYMBOL_TO_CODE.get(sym, 0),
                "Close": 50.0 + float(np.random.normal(0, 1)),
                "Label": int(np.random.choice([0, 1, 2])),
            }
            # Tạo 13 cột đặc trưng tương đối với giá trị số học giả lập
            for col in FEATURE_COLS:
                row[col] = float(np.random.normal(loc=0.0, scale=1.0))
            rows.append(row)

    df = pd.DataFrame(rows)
    return df


def test_scaler_fit_strictly_on_train_only(dummy_panel_data):
    """Xác nhận StandardScaler CHỈ fit trên train_df, không bị rò rỉ phân phối từ val."""
    res = prepare_production_training_data(dummy_panel_data, val_buffer_days=40)
    scaler = res["scaler"]

    # Lấy dữ liệu train thô trước khi scale
    t_end_idx = dummy_panel_data["Date"].nunique() - 40
    train_dates = np.sort(dummy_panel_data["Date"].unique())[:t_end_idx]
    tr_raw = dummy_panel_data[dummy_panel_data["Date"].isin(train_dates)]

    expected_means = tr_raw[FEATURE_COLS].mean().values
    expected_scales = tr_raw[FEATURE_COLS].std(ddof=0).values

    np.testing.assert_allclose(scaler.mean_, expected_means, rtol=1e-5)
    np.testing.assert_allclose(scaler.scale_, expected_scales, rtol=1e-5)

    # Sau scale, train phải có mean xấp xỉ 0 và std xấp xỉ 1
    np.testing.assert_allclose(res["train"][FEATURE_COLS].mean().values, 0.0, atol=1e-5)
    np.testing.assert_allclose(res["train"][FEATURE_COLS].std(ddof=0).values, 1.0, atol=1e-5)


def test_symbol_code_never_scaled(dummy_panel_data):
    """Xác nhận cột Symbol_Code (và Date, Symbol, Label) TUYỆT ĐỐI không bị scale hay thay đổi kiểu dữ liệu."""
    res = prepare_production_training_data(dummy_panel_data, val_buffer_days=40)
    tr_s = res["train"]
    va_s = res["val"]

    for df_split in [tr_s, va_s]:
        assert np.issubdtype(df_split["Symbol_Code"].dtype, np.integer)
        assert df_split["Symbol_Code"].min() >= 0
        assert "Date" in df_split.columns
        assert "Symbol" in df_split.columns


def test_get_warmup_tail_sample_preservation(dummy_panel_data):
    """
    Theo thiết kế thực chiến:
    get_warmup_tail trả đúng (seq_length - 1) dòng cuối mỗi mã từ Train,
    và khi truyền vào create_multivariate_sequences cho Val, số mẫu sinh ra đúng bằng
    chính xác số ngày giao dịch của tập Val (mỗi mã), không thừa không thiếu.
    """
    seq_len = 20
    warmup_len = seq_len - 1  # 19 dòng
    res = prepare_production_training_data(
        dummy_panel_data,
        val_buffer_days=40,
        seq_length=seq_len,
    )

    val_s = res["val"]
    val_warmup = res["val_warmup"]

    # Warmup gồm đúng 3 mã x 19 dòng = 57 dòng
    assert len(val_warmup) == 3 * warmup_len

    val_days_per_sym = len(val_s[val_s["Symbol"] == "VIC"])
    assert val_days_per_sym == 40

    x_val_seq, y_val_seq = create_multivariate_sequences(
        df=val_s,
        warmup_df=val_warmup,
        feature_cols=ALL_FEATURE_COLS,
        seq_length=seq_len,
    )
    # Tổng số mẫu sinh ra: đúng 3 mã x 40 ngày = 120 mẫu, shape (120, 20, 14)
    assert len(x_val_seq) == 3 * val_days_per_sym == 120
    assert len(y_val_seq) == 120
    assert x_val_seq.shape == (120, seq_len, len(ALL_FEATURE_COLS))


def test_sequence_ends_at_day_i_and_label_is_day_i():
    """
    Kiểm chứng chuẩn xác chuỗi và nhãn:
    - Chuỗi cho dòng i (kết thúc tại ngày t) lấy features[i - seq_length + 1 : i + 1], tức gồm cả ngày t.
    - Nhãn gán cho chuỗi là nhãn tại dòng i.
    """
    seq_length = 3
    dates = pd.date_range("2024-01-01", periods=6, freq="B")

    rows = []
    for t, d in enumerate(dates):
        rows.append({
            "Date": d,
            "Symbol": "AAA",
            "F1": float(t),
            "Label": int(100 + t),
        })
    df_test = pd.DataFrame(rows)

    x_arr, y_arr = create_multivariate_sequences(
        df=df_test,
        warmup_df=None,
        feature_cols=["F1"],
        seq_length=seq_length,
    )

    assert len(x_arr) == 4
    assert len(y_arr) == 4

    np.testing.assert_array_equal(x_arr[0].flatten(), [0.0, 1.0, 2.0])
    assert y_arr[0] == 102

    np.testing.assert_array_equal(x_arr[1].flatten(), [1.0, 2.0, 3.0])
    assert y_arr[1] == 103


def test_create_labels_per_symbol():
    """Kiểm tra create_labels_per_symbol gán nhãn theo từng mã và loại bỏ dòng cuối cùng."""
    df_raw = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-01", "2024-01-02", "2024-01-03"]),
        "Symbol": ["A", "A", "A", "B", "B", "B"],
        "Close": [10.0, 10.5, 10.2, 20.0, 19.0, 19.5],
    })

    df_labeled = create_labels_per_symbol(df_raw, threshold=0.01)
    # Dòng cuối mỗi mã bị purge vì không có phiên tương lai
    assert len(df_labeled) == 4
    assert "Label" in df_labeled.columns

    a_labels = df_labeled[df_labeled["Symbol"] == "A"]["Label"].values
    b_labels = df_labeled[df_labeled["Symbol"] == "B"]["Label"].values
    np.testing.assert_array_equal(a_labels, [2, 0])
    np.testing.assert_array_equal(b_labels, [0, 2])


def test_drop_ignored_labels():
    """Kiểm tra drop_ignored_labels loại bỏ đúng nhãn -1 cho cả 3D LSTM lẫn 2D/DataFrame."""
    # 1. Kiểm tra với mảng 3D LSTM
    X_3d = np.array([[[1.0], [2.0]], [[3.0], [4.0]], [[5.0], [6.0]]])  # shape (3, 2, 1)
    y_3d = np.array([0, -1, 2])
    X_clean_3d, y_clean_3d = drop_ignored_labels(X_3d, y_3d)
    assert len(y_clean_3d) == 2
    np.testing.assert_array_equal(y_clean_3d, [0, 2])
    assert X_clean_3d.shape == (2, 2, 1)

    # 2. Kiểm tra với DataFrame
    df_2d = pd.DataFrame({"A": [10, 20, 30], "B": [1, 2, 3]})
    y_2d = np.array([1, -1, 0])
    df_clean, y_clean_df = drop_ignored_labels(df_2d, y_2d)
    assert len(df_clean) == 2
    np.testing.assert_array_equal(y_clean_df, [1, 0])
    assert list(df_clean["A"]) == [10, 30]


def test_apply_study_window_preserves_features_and_truncates():
    """apply_study_window giữ đúng các dòng có Date >= start_date."""
    dates = pd.date_range("2022-01-01", "2023-06-01", freq="B")
    df_raw = pd.DataFrame({
        "Date": dates,
        "Symbol": "AAA",
        "Close": np.linspace(10.0, 50.0, len(dates)),
    })
    df_raw["SMA_10"] = df_raw["Close"].rolling(10).mean()

    df_study = apply_study_window(df_raw, start_date="2023-01-04")
    assert (df_study["Date"] >= pd.to_datetime("2023-01-04")).all()
    assert df_study["Date"].min() == pd.to_datetime("2023-01-04")

    orig_first_val = df_raw[df_raw["Date"] == pd.to_datetime("2023-01-04")]["SMA_10"].values[0]
    study_first_val = df_study[df_study["Date"] == pd.to_datetime("2023-01-04")]["SMA_10"].values[0]
    assert orig_first_val == study_first_val
    assert not np.isnan(study_first_val)


def test_create_multi_day_labels():
    """Kiểm tra gán nhãn đa phiên (T+3) và cơ chế Purge 3 phiên cuối."""
    dates = pd.date_range("2024-01-01", periods=10)
    df = pd.DataFrame({
        "Date": dates,
        "Symbol": ["VIC"] * 10,
        "Close": [100.0, 100.0, 100.0, 105.0, 100.0, 95.0, 100.0, 100.0, 100.0, 100.0],
    })

    labeled_df = create_multi_day_labels(df, horizon=3, threshold=0.02)
    # 10 dòng trừ 3 dòng cuối bị PURGE = 7 dòng
    assert len(labeled_df) == 7
    assert "Label" in labeled_df.columns
    assert "Target_Return" in labeled_df.columns

    # Tại index 0: giá 100 -> 3 ngày sau giá là 105 (+5%) >= 2% -> Nhãn 2 (TĂNG)
    assert labeled_df.iloc[0]["Label"] == 2
    assert pytest.approx(labeled_df.iloc[0]["Target_Return"]) == 0.05

    # Tại index 2: giá 100 -> 3 ngày sau giá là 95 (-5%) <= -2% -> Nhãn 0 (GIẢM)
    assert labeled_df.iloc[2]["Label"] == 0


def test_create_multi_day_labels_validation_errors():
    """Kiểm tra bắt lỗi cột bắt buộc khi tạo nhãn đa phiên."""
    df_no_close = pd.DataFrame({"Date": ["2024-01-01"], "Symbol": ["VIC"]})
    with pytest.raises(ValueError, match="chứa cột giá đóng cửa"):
        create_multi_day_labels(df_no_close)

    df_no_sym = pd.DataFrame({"Date": ["2024-01-01"], "Close": [100.0]})
    with pytest.raises(ValueError, match="chứa cột 'Symbol'"):
        create_multi_day_labels(df_no_sym)


def test_prepare_production_training_data(dummy_panel_data):
    """Kiểm tra quy trình chuẩn bị dữ liệu huấn luyện sản xuất (Production Retraining)."""
    res = prepare_production_training_data(
        dummy_panel_data,
        val_buffer_days=40,
        seq_length=10,
    )

    assert "train" in res
    assert "val" in res
    assert "val_warmup" in res
    assert "scaler" in res

    # 200 ngày - 40 ngày buffer = 160 ngày train, 40 ngày val
    unique_train_dates = res["train"]["Date"].nunique()
    unique_val_dates = res["val"]["Date"].nunique()
    assert unique_train_dates == 160
    assert unique_val_dates == 40

    # Kiểm tra val_warmup có đủ seq_length - 1 = 9 phiên cho mỗi mã
    assert len(res["val_warmup"]) == 3 * 9


def test_prepare_production_training_data_insufficient_dates():
    """Kiểm tra báo lỗi khi tổng số ngày không đủ tạo validation buffer."""
    df_short = pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=10),
        "Symbol": ["VIC"] * 10,
        "Close": [100.0] * 10,
    })
    for col in FEATURE_COLS:
        df_short[col] = 1.0

    with pytest.raises(ValueError, match="không đủ để tạo validation buffer"):
        prepare_production_training_data(df_short, val_buffer_days=40)
