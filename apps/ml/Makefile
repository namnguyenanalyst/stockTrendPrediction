#################################################################################
# VN_STOCK ML MAKEFILE (CCDS v2)                                                #
#################################################################################

PYTHON ?= python3

.PHONY: help
help:
	@echo "Danh sách các lệnh hỗ trợ trong apps/ml:"
	@echo "  make data      - Thu thập và lưu dữ liệu chứng khoán vào data/raw/"
	@echo "  make features  - Tính toán các chỉ báo kỹ thuật tài chính"
	@echo "  make train     - Huấn luyện mô hình PyTorch LSTM và lưu checkpoint"
	@echo "  make predict   - Chạy suy luận dự báo mức giá phiên tiếp theo"
	@echo "  make backtest  - Kiểm thử chiến lược giao dịch với chi phí thuế phí"
	@echo "  make test      - Chạy toàn bộ unit test với pytest"
	@echo "  make lint      - Kiểm tra mã nguồn với ruff"
	@echo "  make format    - Tự động format mã nguồn với ruff"
	@echo "  make clean     - Dọn dẹp cache và file biên dịch"

## Thu thập dữ liệu cổ phiếu vào data/raw/
.PHONY: data
data:
	$(PYTHON) -c "from vn_stock.dataset import fetch_stock_data; df = fetch_stock_data('VIC'); print(f'Đã tải {len(df)} dòng dữ liệu VIC')"

## Tính toán các chỉ báo kỹ thuật
.PHONY: features
features:
	$(PYTHON) -c "from vn_stock.dataset import load_local_data; from vn_stock.features import compute_technical_indicators; df = load_local_data('VIC'); res = compute_technical_indicators(df); print(f'Đã tính {len(res.columns)} cột chỉ báo kỹ thuật')"

## Huấn luyện mô hình PyTorch LSTM
.PHONY: train
train:
	$(PYTHON) -m vn_stock.modeling.train --symbol VIC --epochs 30

## Chạy suy luận dự báo T+1
.PHONY: predict
predict:
	$(PYTHON) -m vn_stock.modeling.predict --symbol VIC

## Kiểm thử chiến lược giao dịch Backtesting
.PHONY: backtest
backtest:
	$(PYTHON) -c "import numpy as np; from vn_stock.dataset import load_local_data; from vn_stock.backtest import run_simple_backtest; df = load_local_data('VIC'); prices = df['Close'].values if 'Close' in df.columns else df['Giá đóng cửa'].values; m = run_simple_backtest(prices=prices[-200:], predictions=prices[-200:] * 1.02); print(f'Backtest Return: {m.total_return_pct}% | MDD: {m.max_drawdown_pct}% | WinRate: {m.win_rate_pct}%')"

## Chạy unit tests
.PHONY: test
test:
	$(PYTHON) -m pytest tests

## Kiểm tra linting với ruff
.PHONY: lint
lint:
	ruff check .

## Format code với ruff
.PHONY: format
format:
	ruff format .

## Dọn dẹp các file cache
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
