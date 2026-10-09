"""Unit tests cho module phân chia dữ liệu walk-forward và chuẩn hóa chống rò rỉ (splitting_data.py)."""

import numpy as np
import pandas as pd
import pytest

from vn_stock.config import SYMBOL_TO_CODE
from vn_stock.features import ALL_FEATURE_COLS, FEATURE_COLS, create_multivariate_sequences
from vn_stock.splitting_data import (
    apply_study_window,
    create_labels_per_symbol,
    drop_ignored_labels,
    generate_walk_forward_windows,
    get_warmup_tail,
    prepare_all_windows,
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


def test_walk_forward_dates_synchronous_across_symbols(dummy_panel_data):
    """Xác nhận mốc cắt theo ngày giống nhau tuyệt đối cho mọi mã trong cùng 1 cửa sổ."""
    windows = generate_walk_forward_windows(dummy_panel_data)
    assert len(windows) == 3

    for win in windows:
        train_df = win["train_df"]
        val_df = win["val_df"]
        test_df = win["test_df"]

        tr_end = win["train_end_date"]
        va_end = win["val_end_date"]
        te_end = win["test_end_date"]

        # Mỗi mã trong từng tập phải có ngày kết thúc đúng bằng ngày kết thúc chung của tập đó
        for sym in ["VIC", "HPG", "FPT"]:
            sym_tr = train_df[train_df["Symbol"] == sym]
            sym_va = val_df[val_df["Symbol"] == sym]
            sym_te = test_df[test_df["Symbol"] == sym]

            assert sym_tr["Date"].max() == tr_end
            assert sym_va["Date"].max() == va_end
            assert sym_te["Date"].max() == te_end


def test_test_cutoff_dates_expanding_windows(dummy_panel_data):
    """
    Xác nhận tập test kết thúc tại mốc cắt riêng (te_cut) cho từng cửa sổ:
    - Cửa sổ 1 kết thúc ở 80% (ngày thứ 160), Cửa sổ 2 ở 90% (ngày thứ 180), Cửa sổ 3 ở 100% (ngày thứ 200).
    - Trong nội bộ từng cửa sổ: train_end < val_end < test_end (không chồng lấn).
    - Giữa các cửa sổ: test_end tăng dần, dữ liệu gối đầu mở rộng (Expanding Windows có chồng lấn giữa các cửa sổ).
    """
    windows = generate_walk_forward_windows(
        dummy_panel_data,
        train_ratios=[0.50, 0.60, 0.70],
        val_ratio=0.15,
        test_ratio=0.15,
    )

    unique_dates = np.sort(dummy_panel_data["Date"].unique())
    assert len(unique_dates) == 200

    # Cửa sổ 1: 50% train (0-99), 15% val (100-129), 15% test (130-159) -> te_cut ở ngày idx 159 (80% mốc)
    win1 = windows[0]
    assert win1["train_end_date"] == unique_dates[99]
    assert win1["val_end_date"] == unique_dates[129]
    assert win1["test_end_date"] == unique_dates[159]
    assert win1["train_end_date"] < win1["val_end_date"] < win1["test_end_date"]

    # Cửa sổ 2: 60% train (0-119), 15% val (120-149), 15% test (150-179) -> te_cut ở ngày idx 179 (90% mốc)
    win2 = windows[1]
    assert win2["train_end_date"] == unique_dates[119]
    assert win2["val_end_date"] == unique_dates[149]
    assert win2["test_end_date"] == unique_dates[179]
    assert win2["train_end_date"] < win2["val_end_date"] < win2["test_end_date"]

    # Cửa sổ 3: 70% train (0-139), 15% val (140-169), 15% test (170-199) -> te_cut ở ngày idx 199 (100% mốc)
    win3 = windows[2]
    assert win3["train_end_date"] == unique_dates[139]
    assert win3["val_end_date"] == unique_dates[169]
    assert win3["test_end_date"] == unique_dates[199]
    assert win3["train_end_date"] < win3["val_end_date"] < win3["test_end_date"]

    # Thứ tự ngày test_end tăng dần qua 3 cửa sổ
    assert win1["test_end_date"] < win2["test_end_date"] < win3["test_end_date"]


def test_scaler_fit_strictly_on_train_only(dummy_panel_data):
    """Xác nhận StandardScaler CHỈ fit trên train_df, không bị rò rỉ phân phối từ val/test."""
    windows = generate_walk_forward_windows(dummy_panel_data)
    win = windows[0]

    tr_df = win["train_df"].copy()
    va_df = win["val_df"].copy()
    te_df = win["test_df"].copy()

    # Thổi phồng giá trị ở val và test để kiểm tra scaler có bị ảnh hưởng không
    va_df[FEATURE_COLS] += 1000.0
    te_df[FEATURE_COLS] += 2000.0

    tr_s, va_s, te_s, scaler = scale_window(tr_df, va_df, te_df, FEATURE_COLS)

    # Thống kê của scaler phải khớp 100% với train_df gốc
    expected_means = tr_df[FEATURE_COLS].mean().values
    expected_scales = tr_df[FEATURE_COLS].std(ddof=0).values

    np.testing.assert_allclose(scaler.mean_, expected_means, rtol=1e-5)
    np.testing.assert_allclose(scaler.scale_, expected_scales, rtol=1e-5)

    # Sau scale, train phải có mean xấp xỉ 0 và std xấp xỉ 1
    np.testing.assert_allclose(tr_s[FEATURE_COLS].mean().values, 0.0, atol=1e-5)
    np.testing.assert_allclose(tr_s[FEATURE_COLS].std(ddof=0).values, 1.0, atol=1e-5)

    # Đảm bảo val_s và te_s được transform bởi scaler đã fit
    assert not va_s.empty
    assert not te_s.empty


def test_symbol_code_never_scaled(dummy_panel_data):
    """Xác nhận cột Symbol_Code (và Date, Symbol, Label) TUYỆT ĐỐI không bị scale hay thay đổi kiểu dữ liệu."""
    windows = generate_walk_forward_windows(dummy_panel_data)
    win = windows[0]

    tr_df, va_df, te_df = win["train_df"], win["val_df"], win["test_df"]
    tr_s, va_s, te_s, _ = scale_window(tr_df, va_df, te_df, FEATURE_COLS)

    for orig, scaled in [(tr_df, tr_s), (va_df, va_s), (te_df, te_s)]:
        # Symbol_Code giữ nguyên 100% giá trị và kiểu int
        pd.testing.assert_series_equal(orig["Symbol_Code"], scaled["Symbol_Code"])
        assert np.issubdtype(scaled["Symbol_Code"].dtype, np.integer)
        pd.testing.assert_series_equal(orig["Symbol"], scaled["Symbol"])
        pd.testing.assert_series_equal(orig["Date"], scaled["Date"])
        pd.testing.assert_series_equal(orig["Label"], scaled["Label"])


def test_get_warmup_tail_sample_preservation(dummy_panel_data):
    """
    Theo thiết kế A2 (chuỗi kết thúc đúng ngày i):
    get_warmup_tail trả đúng (seq_length - 1) dòng cuối mỗi mã,
    và khi truyền vào create_multivariate_sequences, số mẫu sinh ra đúng bằng
    chính xác số ngày giao dịch của tập đó (mỗi mã), không thừa không thiếu.
    """
    seq_len = 20
    warmup_len = seq_len - 1  # 19 dòng
    windows = generate_walk_forward_windows(dummy_panel_data)
    win = windows[0]

    tr_df, va_df, te_df = win["train_df"], win["val_df"], win["test_df"]
    tr_s, va_s, te_s, _ = scale_window(tr_df, va_df, te_df, FEATURE_COLS)

    # Lấy warmup tail cho val từ train_s (seq_length - 1 dòng mỗi mã)
    val_warmup = get_warmup_tail(tr_s, seq_length=seq_len)
    assert len(val_warmup) == 3 * warmup_len  # 3 mã x 19 dòng = 57 dòng

    # Kiểm tra từng mã
    for sym in ["VIC", "HPG", "FPT"]:
        warm_sym = val_warmup[val_warmup["Symbol"] == sym]
        assert len(warm_sym) == warmup_len
        tr_sym = tr_s[tr_s["Symbol"] == sym].sort_values("Date")
        pd.testing.assert_series_equal(
            warm_sym["Date"].reset_index(drop=True),
            tr_sym["Date"].tail(warmup_len).reset_index(drop=True),
        )

    # Dùng create_multivariate_sequences với warmup_df theo A2
    val_days_per_sym = len(va_s[va_s["Symbol"] == "VIC"])
    assert val_days_per_sym == 30

    x_val_seq, y_val_seq = create_multivariate_sequences(
        df=va_s,
        warmup_df=val_warmup,
        feature_cols=ALL_FEATURE_COLS,
        seq_length=seq_len,
    )
    # Tổng số mẫu sinh ra: đúng 3 mã x 30 ngày = 90 mẫu, shape (90, 20, 14)
    assert len(x_val_seq) == 3 * val_days_per_sym == 90
    assert len(y_val_seq) == 90
    assert x_val_seq.shape == (90, seq_len, len(ALL_FEATURE_COLS))

    # Tương tự kiểm tra cho test_s với warmup từ val_s
    test_warmup = get_warmup_tail(va_s, seq_length=seq_len)
    assert len(test_warmup) == 3 * warmup_len

    test_days_per_sym = len(te_s[te_s["Symbol"] == "VIC"])
    assert test_days_per_sym == 30

    x_te_seq, y_te_seq = create_multivariate_sequences(
        df=te_s,
        warmup_df=test_warmup,
        feature_cols=ALL_FEATURE_COLS,
        seq_length=seq_len,
    )
    assert len(x_te_seq) == 3 * test_days_per_sym == 90
    assert len(y_te_seq) == 90
    assert x_te_seq.shape == (90, seq_len, len(ALL_FEATURE_COLS))


def test_warning_on_late_listing_stock(dummy_panel_data):
    """
    Kiểm tra xử lý rõ ràng (phát cảnh báo UserWarning) khi có mã cổ phiếu niêm yết muộn
    (không có dữ liệu trong tập Train của cửa sổ), không âm thầm bỏ qua.
    """
    late_dates = np.sort(dummy_panel_data["Date"].unique())[-20:]
    late_rows = []
    for d in late_dates:
        row = {
            "Date": d,
            "Symbol": "NEW",
            "Symbol_Code": 99,
            "Close": 50.0,
            "Label": 1,
        }
        for col in FEATURE_COLS:
            row[col] = 0.5
        late_rows.append(row)

    df_late = pd.concat([dummy_panel_data, pd.DataFrame(late_rows)], ignore_index=True)

    with pytest.warns(UserWarning, match="hoàn toàn không có dữ liệu trong tập Train"):
        generate_walk_forward_windows(df_late)


def test_prepare_all_windows_pipeline_integrity(dummy_panel_data):
    """Xác nhận pipeline trọn gói prepare_all_windows trả đủ 3 dict hoàn chỉnh."""
    prepared = prepare_all_windows(dummy_panel_data, purge_boundary=True)
    assert len(prepared) == 3

    for i, win in enumerate(prepared):
        assert f"Window {i+1}" in win["name"]
        assert isinstance(win["train"], pd.DataFrame)
        assert isinstance(win["val"], pd.DataFrame)
        assert isinstance(win["test"], pd.DataFrame)
        assert isinstance(win["val_warmup"], pd.DataFrame)
        assert isinstance(win["test_warmup"], pd.DataFrame)
        assert win["train_end_date"] < win["val_end_date"] < win["test_end_date"]
        assert win["scaler"] is not None

        # Không có NaN trong các cột đặc trưng sau scale
        assert not win["train"][FEATURE_COLS].isna().any().any()
        assert not win["val"][FEATURE_COLS].isna().any().any()
        assert not win["test"][FEATURE_COLS].isna().any().any()


def test_sequence_ends_at_day_i_and_label_is_day_i():
    """
    Kiểm chứng chuẩn xác theo thiết kế A2:
    - Chuỗi cho dòng i (kết thúc tại ngày t) lấy features[i - seq_length + 1 : i + 1], tức gồm cả ngày t.
    - Nhãn gán cho chuỗi là nhãn tại dòng i (tính từ Close(t+1) - Close(t)).
    - Không bị lệch 1 ngày.
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

    # Không có warmup: start_idx = seq_length - 1 = 2
    # len(df_test) = 6 dòng (t=0, 1, 2, 3, 4, 5)
    # Số mẫu sinh ra: 6 - 2 = 4 mẫu (tại i = 2, 3, 4, 5)
    x_arr, y_arr = create_multivariate_sequences(
        df=df_test,
        warmup_df=None,
        feature_cols=["F1"],
        seq_length=seq_length,
    )

    assert len(x_arr) == 4
    assert len(y_arr) == 4

    # Mẫu 0 tại i = 2 (ngày t = 2):
    # Chuỗi lấy [2 - 3 + 1 : 2 + 1] = [0 : 3] -> gồm ngày 0, 1, 2 (kết thúc ĐÚNG ngày 2)
    # Nhãn lấy labels[2] = 102 (nhãn của ngày 2)
    np.testing.assert_array_equal(x_arr[0].flatten(), [0.0, 1.0, 2.0])
    assert y_arr[0] == 102

    # Mẫu 1 tại i = 3 (ngày t = 3):
    # Chuỗi lấy [1 : 4] -> gồm ngày 1, 2, 3 (kết thúc ĐÚNG ngày 3)
    # Nhãn lấy labels[3] = 103 (nhãn của ngày 3)
    np.testing.assert_array_equal(x_arr[1].flatten(), [1.0, 2.0, 3.0])
    assert y_arr[1] == 103


def test_create_labels_per_symbol():
    """Kiểm tra create_labels_per_symbol gán nhãn theo từng mã và loại bỏ dòng cuối cùng."""
    df_raw = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-01", "2024-01-02", "2024-01-03"]),
        "Symbol": ["A", "A", "A", "B", "B", "B"],
        "Close": [10.0, 10.5, 10.2, 20.0, 19.0, 19.5],  # A: +5% (nhãn 2), -2.85% (nhãn 0); B: -5% (nhãn 0), +2.6% (nhãn 2)
    })

    df_labeled = create_labels_per_symbol(df_raw, threshold=0.01)
    # Dòng cuối mỗi mã (2024-01-03) bị dropna vì không có t+1
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


def test_purge_boundary_true_masks_single_label_per_symbol(dummy_panel_data):
    """(i) Xác nhận purge_boundary=True làm mất đúng 1 nhãn mỗi mã ở cuối train và cuối val."""
    prepared = prepare_all_windows(dummy_panel_data, purge_boundary=True)
    win1 = prepared[0]

    tr = win1["train"]
    va = win1["val"]
    te = win1["test"]

    tr_end = win1["train_end_date"]
    va_end = win1["val_end_date"]

    # Đúng 3 mã bị gán Label = -1 và Valid_Label = False tại ngày tr_end
    tr_purged = tr[tr["Date"] == tr_end]
    assert len(tr_purged) == 3
    assert (tr_purged["Label"] == -1).all()
    assert (~tr_purged["Valid_Label"]).all()

    # Các ngày trước tr_end vẫn Valid_Label = True
    tr_valid = tr[tr["Date"] < tr_end]
    assert (tr_valid["Label"] != -1).all()
    assert (tr_valid["Valid_Label"]).all()

    # Đúng 3 mã bị gán Label = -1 và Valid_Label = False tại ngày va_end
    va_purged = va[va["Date"] == va_end]
    assert len(va_purged) == 3
    assert (va_purged["Label"] == -1).all()
    assert (~va_purged["Valid_Label"]).all()

    # Test không bị purge ở đuôi
    assert (te["Label"] != -1).all()
    assert (te["Valid_Label"]).all()


def test_purge_boundary_preserves_warmup_and_samples(dummy_panel_data):
    """(ii) Xác nhận warm-up vẫn đúng seq_length - 1 dòng và số chuỗi sinh ra bằng đúng số ngày của tập."""
    seq_len = 20
    warmup_len = seq_len - 1  # 19 dòng
    prepared = prepare_all_windows(dummy_panel_data, seq_length=seq_len, purge_boundary=True)
    win1 = prepared[0]

    # Warmup vẫn đủ 3 mã x 19 dòng = 57 dòng
    assert len(win1["val_warmup"]) == 3 * warmup_len
    assert len(win1["test_warmup"]) == 3 * warmup_len

    # Số chuỗi sinh ra cho val vẫn đủ 3 x 30 = 90 chuỗi
    x_val_seq, y_val_seq = create_multivariate_sequences(
        df=win1["val"],
        warmup_df=win1["val_warmup"],
        feature_cols=ALL_FEATURE_COLS,
        seq_length=seq_len,
    )
    assert len(x_val_seq) == 90
    assert len(y_val_seq) == 90

    # Lọc bỏ nhãn -1 qua drop_ignored_labels
    x_clean, y_clean = drop_ignored_labels(x_val_seq, y_val_seq)
    # Val mất đúng 3 mẫu (1 mẫu mỗi mã ở ngày cuối val) -> còn 87 mẫu
    assert len(x_clean) == 87
    assert len(y_clean) == 87
    assert (y_clean != -1).all()


def test_purge_boundary_false_matches_unpurged_behavior(dummy_panel_data):
    """(iii) Xác nhận purge_boundary=False giữ nguyên vẹn 100% nhãn gốc, không có nhãn nào bằng -1."""
    prepared = prepare_all_windows(dummy_panel_data, purge_boundary=False)
    win1 = prepared[0]

    # Cả train, val, test đều không có nhãn nào bị gán -1
    assert (win1["train"]["Label"] != -1).all()
    assert (win1["val"]["Label"] != -1).all()
    assert (win1["test"]["Label"] != -1).all()

    assert (win1["train"]["Valid_Label"]).all()
    assert (win1["val"]["Valid_Label"]).all()
    assert (win1["test"]["Valid_Label"]).all()


def test_apply_study_window_preserves_features_and_truncates():
    """(a) apply_study_window giữ đúng các dòng có Date >= start_date và đặc trưng giống hệt khi tính trên toàn lịch sử."""
    dates = pd.date_range("2022-01-01", "2023-06-01", freq="B")
    df_raw = pd.DataFrame({
        "Date": dates,
        "Symbol": "AAA",
        "Close": np.linspace(10.0, 50.0, len(dates)),
    })
    # Tính đặc trưng rolling trên toàn bộ dải
    df_raw["SMA_10"] = df_raw["Close"].rolling(10).mean()

    # Cắt từ ngày 2023-01-04
    df_study = apply_study_window(df_raw, start_date="2023-01-04")

    # Xác nhận các dòng trước 2023-01-04 bị loại bỏ
    assert (df_study["Date"] >= pd.to_datetime("2023-01-04")).all()
    assert df_study["Date"].min() == pd.to_datetime("2023-01-04")

    # Giá trị đặc trưng của ngày đầu tiên (2023-01-04) giống hệt 100% giá trị đã tính trước khi cắt
    orig_first_val = df_raw[df_raw["Date"] == pd.to_datetime("2023-01-04")]["SMA_10"].values[0]
    study_first_val = df_study[df_study["Date"] == pd.to_datetime("2023-01-04")]["SMA_10"].values[0]
    assert orig_first_val == study_first_val
    assert not np.isnan(study_first_val)


