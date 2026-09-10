"""Định nghĩa kiến trúc mạng nơ-ron PyTorch LSTM dự báo chuỗi thời gian giá cổ phiếu."""

import torch
import torch.nn as nn


class PredictionModel(nn.Module):
    """Mô hình LSTM 2 lớp dự báo giá cổ phiếu (kế thừa chính xác từ notebook)."""

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
        # Khởi tạo trạng thái ẩn (hidden state) và ô nhớ (cell state)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)

        out, _ = self.lstm(x, (h0, c0))
        # Lấy đầu ra của bước thời gian cuối cùng
        out = self.fc(out[:, -1, :])
        return out
