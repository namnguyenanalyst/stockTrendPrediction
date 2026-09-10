# VN Stock API (FastAPI Backend)

Dịch vụ Backend API phục vụ các tính năng:
- Tra cứu lịch sử giá và chỉ báo kỹ thuật chứng khoán.
- Tiếp nhận yêu cầu suy luận dự báo từ mô hình PyTorch / XGBoost (`apps/ml`).
- Thực thi mô phỏng backtesting cho người dùng trên web.

## 🚀 Hướng dẫn chạy cục bộ

```bash
cd apps/api

# Cài đặt môi trường với uv
uv venv
source .venv/bin/activate
uv pip install -e .

# Chạy server ở chế độ development
uvicorn app.main:app --reload --port 8000
```

Truy cập tài liệu OpenAPI Swagger tại: `http://localhost:8000/docs`
Endpoint kiểm tra sức khỏe: `http://localhost:8000/health`
