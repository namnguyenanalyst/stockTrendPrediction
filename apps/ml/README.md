# VN Stock ML Service (Chuẩn CCDS v2)

Module nghiên cứu, xử lý dữ liệu và huấn luyện mô hình Machine Learning / Deep Learning dự báo thị trường chứng khoán Việt Nam.

## 📁 Cấu trúc thư mục
- `data/`: Lưu trữ dữ liệu phân cấp (`raw/`, `interim/`, `processed/`, `external/`).
- `models/`: Chứa các checkpoint trọng số mô hình (`.pth`) và scaler (`.pkl`).
- `notebooks/`: Jupyter Notebook thử nghiệm và phân tích khám phá (EDA).
- `vn_stock/`: Package mã nguồn Python chính:
  - `config.py`: Đường dẫn và siêu tham số hệ thống.
  - `dataset.py`: Tải dữ liệu qua SSI Fast Connect Data API và đọc cache local.
  - `features.py`: Tính toán chỉ báo kỹ thuật (SMA, RSI, SD, Bollinger Bands,...).
  - `validation.py`: Chia tập chuỗi thời gian & Walk-forward validation chống data leakage.
  - `backtest.py`: Mô phỏng chiến lược đầu tư với phí & thuế thực tế tại VN.
  - `modeling/`: Kiến trúc PyTorch LSTM (`model.py`), huấn luyện (`train.py`), suy luận (`predict.py`).
- `tests/`: Bộ kiểm thử tự động với PyTest.

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
