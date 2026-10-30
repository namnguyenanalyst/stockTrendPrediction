# VN Stock API (FastAPI Backend)

Dịch vụ Backend RESTful API phục vụ các tính năng:
- Tra cứu lịch sử giá nến OHLCV, 13 chỉ báo kỹ thuật và bảng giá thông minh rổ VN30.
- Tiếp nhận yêu cầu suy luận dự báo từ mô hình LightGBM GBDT và PyTorch Global LSTM (`apps/ml`).
- Cung cấp Quỹ đạo dự phóng xu hướng $T+1 \to T+3$ bám sát chu kỳ thanh toán VSDC.
- Thực thi mô phỏng Backtesting cho người dùng trên web với bộ lọc điều kiện DNSE EnTrade X.
- Bộ 45 unit tests tự động bảo đảm độ ổn định cho 100% endpoints và services.

## 🚀 Hướng dẫn chạy cục bộ

```bash
cd apps/api

# Khởi chạy server development với uv
uv run uvicorn app.main:app --reload --port 8000

# Chạy toàn bộ 45 unit tests
uv run pytest -v
```

Truy cập tài liệu OpenAPI Swagger tại: `http://localhost:8000/docs`  
Tài liệu ReDoc tại: `http://localhost:8000/redoc`  
Endpoint kiểm tra sức khỏe: `http://localhost:8000/health`
