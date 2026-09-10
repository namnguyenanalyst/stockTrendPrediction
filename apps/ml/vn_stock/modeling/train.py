"""Module huấn luyện mô hình PyTorch LSTM và lưu trữ checkpoint trọng số."""

import argparse
import pickle
from pathlib import Path
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler

from vn_stock.config import (
    DEFAULT_EPOCHS,
    DEFAULT_HIDDEN_SIZE,
    DEFAULT_INPUT_SIZE,
    DEFAULT_LEARNING_RATE,
    DEFAULT_NUM_LAYERS,
    DEFAULT_OUTPUT_SIZE,
    DEFAULT_SEQ_LENGTH,
    DEFAULT_SYMBOL,
    MODELS_DIR,
)
from vn_stock.dataset import fetch_stock_data, load_local_data
from vn_stock.features import create_sequences
from vn_stock.modeling.model import PredictionModel
from vn_stock.validation import time_series_split


def train_lstm_model(
    symbol: str = DEFAULT_SYMBOL,
    seq_length: int = DEFAULT_SEQ_LENGTH,
    hidden_size: int = DEFAULT_HIDDEN_SIZE,
    num_layers: int = DEFAULT_NUM_LAYERS,
    epochs: int = DEFAULT_EPOCHS,
    lr: float = DEFAULT_LEARNING_RATE,
    models_dir: Path = MODELS_DIR,
) -> Tuple[PredictionModel, float]:
    """Quy trình chuẩn hóa, tạo chuỗi thời gian, huấn luyện và lưu checkpoint mô hình."""
    # Nạp dữ liệu
    df = load_local_data(symbol)
    if df is None:
        df = fetch_stock_data(symbol)

    close_col = "Close" if "Close" in df.columns else "Giá đóng cửa"
    raw_prices = df[close_col].values.astype(float).reshape(-1, 1)

    # Chuẩn hóa dữ liệu bằng StandardScaler (giữ đúng logic notebook)
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(raw_prices)

    # Phân chia dữ liệu theo chuỗi thời gian
    train_size = int(len(scaled_data) * 0.8)
    train_data = scaled_data[:train_size]
    test_data = scaled_data[train_size:]

    x_train, y_train = create_sequences(train_data, seq_length)
    if len(test_data) > seq_length:
        x_test, y_test = create_sequences(test_data, seq_length)
    else:
        x_test, y_test = x_train, y_train

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    x_train_t = torch.FloatTensor(x_train).to(device)
    y_train_t = torch.FloatTensor(y_train).to(device)
    x_test_t = torch.FloatTensor(x_test).to(device)

    model = PredictionModel(
        input_size=DEFAULT_INPUT_SIZE,
        hidden_size=hidden_size,
        num_layers=num_layers,
        output_size=DEFAULT_OUTPUT_SIZE,
    ).to(device)

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        outputs = model(x_train_t)
        optimizer.zero_grad()
        loss = criterion(outputs, y_train_t)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0 or epoch == epochs - 1:
            print(f"Epoch [{epoch + 1}/{epochs}], Loss: {loss.item():.4f}")

    # Đánh giá RMSE trên tập test
    model.eval()
    with torch.no_grad():
        test_pred = model(x_test_t).cpu().numpy()

    test_pred_inv = scaler.inverse_transform(test_pred)
    y_test_inv = scaler.inverse_transform(y_test)
    rmse = float(np.sqrt(np.mean((y_test_inv - test_pred_inv) ** 2)))
    print(f"Hoàn thành huấn luyện {symbol}! RMSE trên test: {rmse:.4f}")

    # Lưu model và scaler vào thư mục models/
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / f"model_{symbol.upper()}.pth"
    scaler_path = models_dir / f"scaler_{symbol.upper()}.pkl"

    torch.save(model.state_dict(), model_path)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"Đã lưu checkpoint: {model_path}")
    print(f"Đã lưu scaler: {scaler_path}")

    return model, rmse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Huấn luyện mô hình dự báo cổ phiếu.")
    parser.add_argument("--symbol", type=str, default=DEFAULT_SYMBOL, help="Mã cổ phiếu (ví dụ VIC)")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="Số epochs")
    args = parser.parse_args()
    train_lstm_model(symbol=args.symbol, epochs=args.epochs)
