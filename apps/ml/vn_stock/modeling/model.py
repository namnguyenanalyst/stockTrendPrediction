import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
from typing import Any

import torch
from torch import nn
import torch.nn.functional as F
import lightgbm as lgb

from vn_stock.config import (
    DEFAULT_LGB_PARAMS,
    DEFAULT_LSTM_DROPOUT,
    DEFAULT_LSTM_HIDDEN_SIZE,
    DEFAULT_LSTM_INPUT_SIZE,
    DEFAULT_LSTM_NUM_LAYERS,
    NUM_CLASSES,
)


class GlobalLSTMClassifier(nn.Module):
    """
    Mô hình học sâu PyTorch Global LSTM Classifier phân loại xu hướng 3 lớp đa biến.

    Kiến trúc theo chuẩn Notebook 2.0 (Walking Skeleton v2.1):
    - LSTM 2 lớp đa biến (batch_first=True, dropout=0.2).
    - Fully Connected Head: Linear(hidden_size, 32) -> ReLU -> Dropout(0.2) -> Linear(32, num_classes).
    - Đầu ra: Logits phân loại 3 lớp (0: Giảm, 1: Đi ngang, 2: Tăng).
    """

    def __init__(
        self,
        input_size: int = DEFAULT_LSTM_INPUT_SIZE,
        hidden_size: int = DEFAULT_LSTM_HIDDEN_SIZE,
        num_layers: int = DEFAULT_LSTM_NUM_LAYERS,
        num_classes: int = NUM_CLASSES,
        dropout: float = DEFAULT_LSTM_DROPOUT,
    ):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_classes = num_classes

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass của mô hình.

        Args:
            x: Tensor đầu vào shape (batch_size, seq_length, input_size).

        Returns:
            Tensor logits shape (batch_size, num_classes).
        """
        out, _ = self.lstm(x)
        # Trích xuất vector ẩn của bước thời gian cuối cùng
        last_step_out = out[:, -1, :]
        logits = self.fc(last_step_out)
        return logits

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Tính toán phân bổ xác suất Softmax cho 3 lớp."""
        logits = self.forward(x)
        return F.softmax(logits, dim=-1)


def create_lightgbm_model(custom_params: dict[str, Any] | None = None) -> lgb.LGBMClassifier:
    """
    Khởi tạo mô hình LightGBM Classifier dạng bảng đa mã chuẩn thực nghiệm Notebook 2.0.

    Args:
        custom_params: Bộ tham số tùy biến nếu muốn ghi đè DEFAULT_LGB_PARAMS.

    Returns:
        Instance của lgb.LGBMClassifier sẵn sàng fit.
    """
    params = dict(DEFAULT_LGB_PARAMS)
    if custom_params:
        params.update(custom_params)
    return lgb.LGBMClassifier(**params)


class PredictionModel(nn.Module):
    """
    Mô hình LSTM hồi quy đơn biến cũ (giữ lại nhằm tương thích ngược nếu có module cũ gọi).
    Khuyến nghị sử dụng GlobalLSTMClassifier cho bài toán phân loại xu hướng 3 lớp có ngưỡng.
    """

    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 32,
        num_layers: int = 2,
        output_size: int = 1,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out
