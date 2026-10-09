"""Module phân chia dữ liệu chuỗi thời gian Walk-Forward Validation đa mã và chuẩn hóa chống rò rỉ thông tin."""

from collections.abc import Sequence
import logging
from typing import Any
import warnings

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from vn_stock.config import DEFAULT_SEQ_LENGTH, STUDY_START_DATE
from vn_stock.features import FEATURE_COLS

logger = logging.getLogger(__name__)


def apply_study_window(
    df: pd.DataFrame,
    start_date: str = STUDY_START_DATE,
    date_col: str = "Date",
) -> pd.DataFrame:
    """
    Cắt gọn tập dữ liệu bảng đa mã về đúng phạm vi cửa sổ nghiên cứu (Study Window).

    Lý do tồn tại hàm:
    - Trong pipeline ML, dữ liệu giá thô cần được thu thập từ FETCH_START_DATE (2022-01-01)
      để cung cấp ~250 phiên giao dịch khởi động (warm-up history) cho các chỉ báo kỹ thuật có cửa sổ
      dài như SMA_200 và CV_200.
    - Hàm compute_features_per_symbol(drop_na=True) phải được tính trên TOÀN BỘ lịch sử này để không
      bị mất các phiên đầu năm 2023.
    - Sau khi đã tính xong đầy đủ đặc trưng, hàm apply_study_window() được gọi để cắt gọn lại dữ liệu,
      chỉ giữ các phiên từ STUDY_START_DATE (2023-01-04) trở đi. Nhờ đó:
      (a) Các đặc trưng kỹ thuật rolling đã hội tụ đầy đủ giá trị ngay từ ngày 2023-01-04 cho cả 5 mã.
      (b) Các tỷ lệ phân chia Walk-Forward (50/60/70%, 15%, 15%) được tính toán nghiêm ngặt trên đúng
          tập các ngày của cửa sổ nghiên cứu, bảo đảm tính nhất quán và khả năng so sánh đối chứng
          với các kết quả thực nghiệm trước đây.

    Args:
        df: DataFrame chứa dữ liệu đặc trưng đã tính toán.
        start_date: Ngày bắt đầu cửa sổ nghiên cứu (mặc định STUDY_START_DATE = "2023-01-04").
        date_col: Tên cột thời gian (mặc định 'Date').

    Returns:
        pd.DataFrame chỉ chứa các dòng có Date >= start_date, đã sắp xếp theo Date và Symbol.
    """
    if date_col not in df.columns:
        raise ValueError(f"DataFrame phải chứa cột '{date_col}' để áp dụng cửa sổ nghiên cứu.")

    target_dt = pd.to_datetime(start_date)
    filtered = df[df[date_col] >= target_dt].copy()

    sort_cols = [date_col]
    if "Symbol" in filtered.columns:
        sort_cols.append("Symbol")

    return filtered.sort_values(sort_cols).reset_index(drop=True)


def create_labels_per_symbol(
    df: pd.DataFrame,
    threshold: float = 0.01,
    close_col: str = "Close",
    symbol_col: str = "Symbol",
    date_col: str = "Date",
) -> pd.DataFrame:
    """
    Tạo nhãn xu hướng 3 lớp Next-Day (T+1) có ngưỡng độc lập theo từng mã cổ phiếu.

    Công thức:
        Next_Return = (Close(t+1) - Close(t)) / Close(t)
        - Nhãn 0 (Giảm): Next_Return <= -threshold
        - Nhãn 1 (Đi ngang): -threshold < Next_Return < threshold
        - Nhãn 2 (Tăng): Next_Return >= threshold

    Quy tắc:
    - Bắt buộc gom nhóm theo từng mã cổ phiếu (groupby Symbol) trước khi shift(-1) để ngăn rò rỉ
      hoặc lấy nhầm giá của mã khác.
    - Dòng cuối cùng của mỗi mã (không có ngày giao dịch tiếp theo t+1 trong lịch sử) sẽ bị loại bỏ
      do Next_Return là NaN.

    Args:
        df: DataFrame chứa dữ liệu đa mã.
        threshold: Ngưỡng lọc nhiễu nhãn xu hướng (mặc định 0.01 tương ứng +-1.0%).
        close_col: Tên cột giá đóng cửa.
        symbol_col: Tên cột mã cổ phiếu.
        date_col: Tên cột ngày giao dịch.

    Returns:
        pd.DataFrame đã có thêm cột 'Label' (kiểu int64).
    """
    if close_col not in df.columns:
        raise ValueError(f"DataFrame phải chứa cột giá đóng cửa '{close_col}'.")
    if symbol_col not in df.columns or date_col not in df.columns:
        raise ValueError(f"DataFrame phải chứa cột '{symbol_col}' và '{date_col}'.")

    dfs = []
    for _, grp in df.groupby(symbol_col):
        g = grp.sort_values(date_col).copy()
        next_close = g[close_col].shift(-1)
        next_return = (next_close - g[close_col]) / g[close_col]

        conditions = [
            next_return <= -threshold,
            (next_return > -threshold) & (next_return < threshold),
            next_return >= threshold,
        ]
        g["Label"] = np.select(conditions, [0, 1, 2], default=np.nan)
        # Loại bỏ dòng cuối cùng của từng mã vì không có phiên t+1
        g = g.dropna(subset=["Label"]).reset_index(drop=True)
        g["Label"] = g["Label"].astype(int)
        dfs.append(g)

    if not dfs:
        return pd.DataFrame(columns=list(df.columns) + ["Label"])

    res = pd.concat(dfs, ignore_index=True)
    return res.sort_values([date_col, symbol_col]).reset_index(drop=True)


def drop_ignored_labels(X: Any, y: np.ndarray) -> tuple[Any, np.ndarray]:
    """
    Hàm lọc tiện ích dùng chung: loại bỏ triệt để các mẫu mang nhãn sentinel -1 (purged boundary)
    trước khi đưa vào huấn luyện mô hình (LSTM, LightGBM, Naive) hoặc tính toán ma trận nhầm lẫn / F1.

    Args:
        X: Mảng đặc trưng 3D của LSTM (ndarray), mảng 2D (ndarray) hoặc DataFrame của LightGBM.
        y: Mảng 1D nhãn mục tiêu (ndarray).

    Returns:
        tuple[X_valid, y_valid] chỉ chứa các mẫu có nhãn hợp lệ (y != -1).
    """
    valid_mask = (y != -1)
    if isinstance(X, pd.DataFrame):
        X_valid = X.loc[valid_mask].reset_index(drop=True)
    elif isinstance(X, np.ndarray):
        X_valid = X[valid_mask]
    else:
        # Hỗ trợ list hoặc cấu trúc sequence khác
        X_valid = [x for idx, x in enumerate(X) if valid_mask[idx]]

    y_valid = y[valid_mask]
    return X_valid, y_valid


def generate_walk_forward_windows(
    df: pd.DataFrame,
    train_ratios: Sequence[float] = (0.50, 0.60, 0.70),
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    date_col: str = "Date",
    symbol_col: str = "Symbol",
) -> list[dict[str, Any]]:
    """
    Tạo các cửa sổ Walk-Forward kiểm định cắt đồng bộ theo danh sách ngày giao dịch duy nhất (unique dates).

    Nguyên tắc phân chia:
    - Mọi mã cổ phiếu đều được cắt tại ĐÚNG CÙNG MỘT NGÀY trong toàn bộ panel.
    - Không shuffle ở bất kỳ bước nào để bảo toàn trật tự thời gian.
    - Quan hệ thời gian:
      + TRONG NỘI BỘ TỪNG CỬA SỔ: Train, Validation và Test hoàn toàn không chồng lấn theo thời gian
        (train_end_date < val_end_date < test_end_date).
      + GIỮA CÁC CỬA SỔ (Expanding Windows): Tập Train mở rộng dần theo thời gian. Do đó, các cửa sổ
        CÓ CHỒNG LẤN LẪN NHAU (vùng test của cửa sổ trước nằm trùm lên vùng train/val/test của cửa sổ sau).
    - Tỷ lệ train/val/test (50/60/70%, 15%, 15%) được tính nghiêm ngặt theo số LƯỢNG NGÀY GIAO DỊCH
      DUY NHẤT (unique dates), TUYỆT ĐỐI KHÔNG TÍNH THEO SỐ DÒNG CỦA DATAFRAME.
      Vì các mã cổ phiếu có thể bắt đầu giao dịch ở các thời điểm khác nhau (hoặc bị loại bỏ do rolling MA ban đầu),
      số dòng thực tế của tập train có thể chiếm tỷ lệ nhỏ hơn tỷ lệ số ngày.
    - Tập test kết thúc tại mốc cắt riêng của từng cửa sổ (te_cut), không lấy đến cuối toàn bộ dữ liệu:
      + Cửa sổ 1: Train 50%, Val 15%, Test 15% (Test kết thúc tại mốc 80% thời gian)
      + Cửa sổ 2: Train 60%, Val 15%, Test 15% (Test kết thúc tại mốc 90% thời gian)
      + Cửa sổ 3: Train 70%, Val 15%, Test 15% (Test kết thúc tại mốc 100% thời gian)

    Args:
        df: DataFrame chứa dữ liệu đa mã (bắt buộc có cột date_col và symbol_col).
        train_ratios: Danh sách các tỷ lệ tập train mở rộng dần (Expanding Windows).
        val_ratio: Tỷ lệ tập validation cho mỗi cửa sổ (mặc định 0.15).
        test_ratio: Tỷ lệ tập test out-of-sample cho mỗi cửa sổ (mặc định 0.15).
        date_col: Tên cột thời gian (mặc định 'Date').
        symbol_col: Tên cột mã cổ phiếu (mặc định 'Symbol').

    Returns:
        list[dict[str, Any]]: Danh sách các cửa sổ, mỗi dict chứa:
            - name: Tên định danh cửa sổ
            - train_ratio: Tỷ lệ train của cửa sổ
            - val_ratio: Tỷ lệ val của cửa sổ
            - test_ratio: Tỷ lệ test của cửa sổ
            - train_df: DataFrame tập train
            - val_df: DataFrame tập val
            - test_df: DataFrame tập test
            - train_end_date: Ngày giao dịch cuối cùng của tập train (pd.Timestamp)
            - val_end_date: Ngày giao dịch cuối cùng của tập val (pd.Timestamp)
            - test_end_date: Ngày giao dịch cuối cùng của tập test (pd.Timestamp)
    """
    if date_col not in df.columns:
        raise ValueError(f"DataFrame phải chứa cột '{date_col}' để chia tập theo thời gian.")
    if symbol_col not in df.columns:
        raise ValueError(f"DataFrame phải chứa cột '{symbol_col}' để quản lý dữ liệu đa mã.")

    # Sắp xếp và lấy danh sách ngày duy nhất trên toàn bộ panel dữ liệu
    unique_dates = np.sort(df[date_col].unique())
    n_dates = len(unique_dates)

    if n_dates == 0:
        raise ValueError("DataFrame không có dữ liệu ngày hợp lệ.")

    all_symbols = set(df[symbol_col].dropna().unique())
    windows = []

    for idx, t_ratio in enumerate(train_ratios, start=1):
        if t_ratio + val_ratio + test_ratio > 1.0 + 1e-9:
            raise ValueError(
                f"Tổng tỷ lệ (train={t_ratio} + val={val_ratio} + test={test_ratio} = "
                f"{t_ratio + val_ratio + test_ratio:.2f}) vượt quá 1.0."
            )

        t_end_idx = int(t_ratio * n_dates)
        v_end_idx = int((t_ratio + val_ratio) * n_dates)
        te_end_idx = min(int((t_ratio + val_ratio + test_ratio) * n_dates), n_dates)

        if t_end_idx <= 0 or v_end_idx <= t_end_idx or te_end_idx <= v_end_idx:
            raise ValueError(
                f"Dữ liệu không đủ số ngày ({n_dates} ngày) để chia cửa sổ "
                f"với tỷ lệ train={t_ratio}, val={val_ratio}, test={test_ratio}."
            )

        train_dates = unique_dates[:t_end_idx]
        val_dates = unique_dates[t_end_idx:v_end_idx]
        test_dates = unique_dates[v_end_idx:te_end_idx]

        train_df = df[df[date_col].isin(train_dates)].copy()
        val_df = df[df[date_col].isin(val_dates)].copy()
        test_df = df[df[date_col].isin(test_dates)].copy()

        train_end_date = pd.Timestamp(unique_dates[t_end_idx - 1])
        val_end_date = pd.Timestamp(unique_dates[v_end_idx - 1])
        test_end_date = pd.Timestamp(unique_dates[te_end_idx - 1])

        # Kiểm tra tính đầy đủ của các mã cổ phiếu trong cửa sổ (cảnh báo niêm yết muộn hoặc thiếu dữ liệu)
        train_symbols = set(train_df[symbol_col].dropna().unique())
        missing_in_train = all_symbols - train_symbols
        if missing_in_train:
            warnings.warn(
                f"Cửa sổ {idx} (Train {t_ratio*100:.0f}%): Các mã {sorted(missing_in_train)} "
                f"hoàn toàn không có dữ liệu trong tập Train (có thể do niêm yết muộn sau {train_end_date}).",
                UserWarning,
                stacklevel=2,
            )

        for sym in train_symbols:
            n_sym_train = len(train_df[train_df[symbol_col] == sym])
            if n_sym_train < DEFAULT_SEQ_LENGTH:
                warnings.warn(
                    f"Cửa sổ {idx}: Mã {sym} chỉ có {n_sym_train} dòng trong tập Train, "
                    f"ít hơn DEFAULT_SEQ_LENGTH={DEFAULT_SEQ_LENGTH}.",
                    UserWarning,
                    stacklevel=2,
                )

        window_dict = {
            "name": f"Window {idx} (Train {int(t_ratio * 100)}%)",
            "train_ratio": float(t_ratio),
            "val_ratio": float(val_ratio),
            "test_ratio": float(test_ratio),
            "train_df": train_df,
            "val_df": val_df,
            "test_df": test_df,
            "train_end_date": train_end_date,
            "val_end_date": val_end_date,
            "test_end_date": test_end_date,
        }
        windows.append(window_dict)

    return windows


def scale_window(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str] = FEATURE_COLS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, StandardScaler]:
    """
    Chuẩn hóa StandardScaler độc lập chống rò rỉ thông tin (Leak-free Preprocessing).

    Quy tắc:
    - StandardScaler CHỈ được fit trên train_df[feature_cols].
    - Transform cho cả 3 tập (train, val, test) bằng scaler đã fit từ train.
    - Cột 'Symbol_Code' (và các cột định danh khác: Symbol, Date, Label, Valid_Label) TUYỆT ĐỐI KHÔNG SCALE,
      được giữ nguyên vẹn giá trị và kiểu dữ liệu gốc.

    Args:
        train_df: DataFrame tập train.
        val_df: DataFrame tập val.
        test_df: DataFrame tập test.
        feature_cols: Danh sách các cột đặc trưng số học cần chuẩn hóa (mặc định 13 cột FEATURE_COLS).

    Returns:
        tuple[train_scaled, val_scaled, test_scaled, scaler]
    """
    missing_cols = [c for c in feature_cols if c not in train_df.columns]
    if missing_cols:
        raise ValueError(f"Tập Train thiếu các cột đặc trưng bắt buộc: {missing_cols}")

    scaler = StandardScaler()
    scaler.fit(train_df[feature_cols])

    train_scaled = train_df.copy()
    val_scaled = val_df.copy()
    test_scaled = test_df.copy()

    train_scaled[feature_cols] = scaler.transform(train_df[feature_cols])

    if not val_df.empty:
        val_scaled[feature_cols] = scaler.transform(val_df[feature_cols])

    if not test_df.empty:
        test_scaled[feature_cols] = scaler.transform(test_df[feature_cols])

    return train_scaled, val_scaled, test_scaled, scaler


def get_warmup_tail(
    prev_split_df: pd.DataFrame,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    symbol_col: str = "Symbol",
    date_col: str = "Date",
) -> pd.DataFrame:
    """
    Trích xuất đúng (seq_length - 1) dòng cuối cùng của MỖI MÃ CỔ PHIẾU từ tập dữ liệu liền trước.

    Dùng làm warmup_df truyền vào create_multivariate_sequences(df, warmup_df=...) trong features.py
    nhằm bảo toàn 100% số mẫu cho tập tiếp theo (Validation hoặc Test) khi chuỗi quan sát kết thúc đúng
    tại ngày thứ i.

    Args:
        prev_split_df: DataFrame của tập liền trước (ví dụ train_scaled hoặc val_scaled).
        seq_length: Độ dài chuỗi quan sát quá khứ (số dòng đuôi cần lấy là seq_length - 1).
        symbol_col: Tên cột mã cổ phiếu.
        date_col: Tên cột ngày giao dịch.

    Returns:
        pd.DataFrame chứa phần đuôi warmup của từng mã, giữ nguyên cấu trúc cột.
    """
    if prev_split_df.empty:
        return pd.DataFrame(columns=prev_split_df.columns)

    if symbol_col not in prev_split_df.columns or date_col not in prev_split_df.columns:
        raise ValueError(f"prev_split_df phải chứa cột '{symbol_col}' và '{date_col}'.")

    warmup_len = seq_length - 1
    if warmup_len <= 0:
        return pd.DataFrame(columns=prev_split_df.columns)

    tails = []
    for sym, grp in prev_split_df.groupby(symbol_col):
        sorted_grp = grp.sort_values(date_col)
        n_rows = len(sorted_grp)
        if n_rows < warmup_len:
            warnings.warn(
                f"Mã {sym} trong tập trước chỉ có {n_rows} dòng, ít hơn warmup_len={warmup_len}. "
                f"Warmup cho mã này sẽ không đủ {warmup_len} bước quan sát.",
                UserWarning,
                stacklevel=2,
            )
        tails.append(sorted_grp.tail(warmup_len))

    if not tails:
        return pd.DataFrame(columns=prev_split_df.columns)

    warmup_df = pd.concat(tails, ignore_index=True)
    return warmup_df


def prepare_all_windows(
    df: pd.DataFrame,
    train_ratios: Sequence[float] = (0.50, 0.60, 0.70),
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    feature_cols: list[str] = FEATURE_COLS,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    purge_boundary: bool = True,
    date_col: str = "Date",
    symbol_col: str = "Symbol",
) -> list[dict[str, Any]]:
    """
    Hàm điều phối toàn diện cho 3 cửa sổ Walk-Forward:
    1. Chia 3 cửa sổ theo ngày duy nhất (generate_walk_forward_windows).
    2. Fit StandardScaler độc lập trên train của từng cửa sổ và transform (scale_window).
    3. Xử lý rò rỉ ranh giới (Purged Boundary): Khi purge_boundary=True, nhãn của ngày cuối Train
       và ngày cuối Val (mỗi mã) được gán thành -1 (sentinel), dòng đặc trưng giữ nguyên để warm-up.
    4. Trích xuất warmup tail cho val và test (get_warmup_tail với seq_length - 1 dòng).

    Args:
        df: DataFrame đầu vào (nếu có cột 'Label' sẽ thực hiện purge boundary).
        train_ratios: Tỷ lệ tập train mở rộng.
        val_ratio: Tỷ lệ tập val.
        test_ratio: Tỷ lệ tập test.
        feature_cols: Danh sách cột đặc trưng cần scale.
        seq_length: Độ dài chuỗi quan sát LSTM (mặc định 20).
        purge_boundary: Nếu True, gán nhãn ngày cuối Train và Val bằng -1 để triệt tiêu rò rỉ.
        date_col: Cột ngày giao dịch.
        symbol_col: Cột mã cổ phiếu.

    Returns:
        list[dict[str, Any]]: Danh sách 3 cửa sổ chuẩn bị sẵn sàng cho huấn luyện và kiểm định.
    """
    raw_windows = generate_walk_forward_windows(
        df=df,
        train_ratios=train_ratios,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        date_col=date_col,
        symbol_col=symbol_col,
    )

    prepared_windows = []
    has_label = "Label" in df.columns

    for win in raw_windows:
        tr_df = win["train_df"].copy()
        va_df = win["val_df"].copy()
        te_df = win["test_df"].copy()

        # Chuẩn hóa dữ liệu chống rò rỉ (fit chỉ trên train)
        train_s, val_s, test_s, scaler = scale_window(
            train_df=tr_df,
            val_df=va_df,
            test_df=te_df,
            feature_cols=feature_cols,
        )

        # Xử lý rò rỉ ranh giới (Purged Boundary)
        if has_label:
            if purge_boundary:
                # Gán nhãn -1 cho ngày cuối cùng của Train và Val (mỗi mã)
                tr_end = win["train_end_date"]
                va_end = win["val_end_date"]

                train_s.loc[train_s[date_col] == tr_end, "Label"] = -1
                val_s.loc[val_s[date_col] == va_end, "Label"] = -1

            # Cột Valid_Label luôn suy ra từ Label != -1
            train_s["Valid_Label"] = (train_s["Label"] != -1)
            val_s["Valid_Label"] = (val_s["Label"] != -1)
            test_s["Valid_Label"] = (test_s["Label"] != -1)

        # Trích xuất warm-up tails (seq_length - 1 dòng đuôi)
        val_warmup = get_warmup_tail(
            prev_split_df=train_s,
            seq_length=seq_length,
            symbol_col=symbol_col,
            date_col=date_col,
        )
        test_warmup = get_warmup_tail(
            prev_split_df=val_s,
            seq_length=seq_length,
            symbol_col=symbol_col,
            date_col=date_col,
        )

        prepared_win = {
            "name": win["name"],
            "train_ratio": win["train_ratio"],
            "val_ratio": win["val_ratio"],
            "test_ratio": win["test_ratio"],
            "train": train_s,
            "val": val_s,
            "test": test_s,
            "val_warmup": val_warmup,
            "test_warmup": test_warmup,
            "scaler": scaler,
            "train_end_date": win["train_end_date"],
            "val_end_date": win["val_end_date"],
            "test_end_date": win["test_end_date"],
        }
        prepared_windows.append(prepared_win)

    return prepared_windows
