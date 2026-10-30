# VN Stock ML Service (Chuẩn CCDS v2)

Module nghiên cứu, xử lý dữ liệu và huấn luyện mô hình Machine Learning / Deep Learning dự báo thị trường chứng khoán Việt Nam.

## 📁 Cấu trúc thư mục
- `data/`: Lưu trữ dữ liệu phân cấp (`raw/`, `interim/`, `processed/`, `external/`).
- `models/`: Chứa các checkpoint trọng số mô hình (`.pth`) và scaler (`.pkl`).
- `notebooks/`: Jupyter Notebook thử nghiệm và phân tích khám phá (EDA).
- `vn_stock/`: Package mã nguồn Python chính:
  - `config.py`: Đường dẫn, cấu hình siêu tham số và danh mục rổ VN30.
  - `ssi_client.py`: Cổng kết nối SSI Fast Connect Data API và xác thực JWT token.
  - `data_ingestion.py`: Thu thập, kiểm tra 5 tiêu chí toàn vẹn, lưu cache Parquet 2 tầng và nạp nến nối đuôi.
  - `market_session.py`: Quản lý phiên giao dịch Việt Nam theo chuẩn múi giờ UTC+7 và mốc 15:00 kết thúc ATC.
  - `features.py`: Tính toán 13 chỉ báo kỹ thuật tương đối không thứ nguyên và chuỗi trượt 3D.
  - `splitting_data.py`: Chuẩn bị dữ liệu huấn luyện thực chiến & Validation Buffer với Purged Horizon chống data leakage.
  - `backtest.py`: Động cơ Backtesting mô phỏng giao dịch thực tế T+2, trượt giá và chi phí thuế phí.
  - `modeling/`: Kiến trúc PyTorch Global LSTM, LightGBM, train.py, predict.py và XAI explain_shap.py.
- `tests/`: Bộ 96 unit tests tự động với PyTest (100% passed).

## 🚀 Hướng dẫn chạy nhanh (Makefile)
```bash
# Cài đặt môi trường & dependencies
uv sync

# Thu thập dữ liệu cổ phiếu mặc định (VIC)
make data

# Tính toán các chỉ báo kỹ thuật
make features

# Huấn luyện mô hình PyTorch LSTM
make train

# Chạy suy luận dự báo
make predict

# Kiểm thử chiến lược đầu tư Backtest
make backtest

# Chạy toàn bộ unit test
make test
```
