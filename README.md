# VN Stock Market Prediction & Strategy Evaluation Platform

Hệ thống dự báo xu hướng thị trường chứng khoán Việt Nam và đánh giá chiến lược đầu tư. Dự án được tổ chức theo kiến trúc **Monorepo** hoàn chỉnh, module Machine Learning tuân thủ nghiêm ngặt chuẩn **Cookiecutter Data Science v2 (CCDS v2)**, cùng khung dịch vụ Backend API (FastAPI), Frontend Web (Next.js) và cơ sở hạ tầng (PostgreSQL & Docker Compose).

---

## 🏛️ Cấu trúc Monorepo

```text
VN_Stock/
├── apps/
│   ├── ml/                      # Machine Learning Service (Chuẩn CCDS v2)
│   │   ├── data/                # Phân cấp: raw/, interim/, processed/, external/
│   │   ├── models/              # Checkpoint mô hình (.pth) và scalers (.pkl)
│   │   ├── notebooks/           # Jupyter Notebooks nghiên cứu & EDA
│   │   ├── vn_stock/            # Package mã nguồn Python chính
│   │   │   ├── config.py        # Cấu hình đường dẫn & siêu tham số
│   │   │   ├── dataset.py       # Ingestion SSI Fast Connect Data & đọc/ghi dữ liệu
│   │   │   ├── features.py      # Tính toán chỉ báo kỹ thuật tài chính
│   │   │   ├── validation.py    # Walk-forward CV & Time-series split
│   │   │   ├── backtest.py      # Simulator kiểm thử giao dịch có thuế phí
│   │   │   └── modeling/        # Kiến trúc PyTorch LSTM, train.py, predict.py
│   │   ├── tests/               # Bộ test tự động (PyTest)
│   │   ├── pyproject.toml       # Quản lý dependencies qua uv
│   │   └── Makefile             # Tự động hóa: data, features, train, backtest, test
│   │
│   ├── api/                     # Backend API (FastAPI)
│   │   ├── app/
│   │   │   ├── main.py          # FastAPI app & endpoint /health
│   │   │   ├── routers/         # Routers nghiệp vụ
│   │   │   └── models/          # Pydantic schemas
│   │   ├── Dockerfile           # Đóng gói container với uv
│   │   └── pyproject.toml
│   │
│   └── web/                     # Frontend Web (Next.js App Router, TypeScript)
│       ├── src/app/             # Giao diện người dùng
│       └── Dockerfile           # Multi-stage production build
│
├── packages/
│   └── shared/                  # Định nghĩa schemas, types dùng chung giữa API và Web
│
├── infra/
│   ├── docker-compose.yml       # Điều phối PostgreSQL 16, API, Web và ML batch job
│   └── migrations/              # Quản lý schema database (Alembic)
│
├── docs/                        # Tài liệu nghiên cứu & kế hoạch đồ án
│   └── GHI_CHU_DO_AN.md
├── references/                  # Mã nguồn & tài liệu tham khảo bổ trợ
├── .github/workflows/           # CI workflow tự động kiểm thử
└── README.md                    # Tài liệu tổng quan dự án
```

---

## 🚀 Hướng Dẫn Vận Hành Từng Thành Phần

### 1. Dịch vụ Học máy & Xử lý Dữ liệu (`apps/ml`)
Quản lý môi trường và gói thư viện bằng **uv**:

```bash
cd apps/ml

# Đồng bộ môi trường và dependencies
uv sync

# Thu thập dữ liệu cổ phiếu mẫu (mặc định VIC)
make data

# Tính toán các chỉ báo kỹ thuật (SMA, RSI, SD, Bollinger Bands,...)
make features

# Huấn luyện mô hình PyTorch LSTM
make train

# Chạy suy luận dự báo phiên T+1 và phát sinh tín hiệu đầu tư
make predict

# Kiểm thử chiến lược đầu tư (Backtesting có trừ 0.15% phí và 0.1% thuế)
make backtest

# Chạy toàn bộ unit test
make test
```

### 2. Backend API (`apps/api`)
Backend cung cấp REST API được xây dựng bằng **FastAPI**:

```bash
cd apps/api

# Cài đặt và khởi chạy máy chủ phát triển
uv run uvicorn app.main:app --reload --port 8000
```
- Swagger UI tài liệu API: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health-check endpoint: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Frontend Web (`apps/web`)
Giao diện người dùng xây dựng bằng **Next.js & TypeScript**:

```bash
cd apps/web

# Khởi chạy server development
npm run dev
```
- Truy cập ứng dụng tại: [http://localhost:3000](http://localhost:3000)

---

## 🐳 Khởi Chạy Toàn Bộ Hệ Thống Với Docker Compose

Chạy toàn bộ cụm dịch vụ Database PostgreSQL, Backend API và Frontend Web chỉ với một lệnh duy nhất:

```bash
cd infra
docker compose up -d --build
```

- **PostgreSQL**: `localhost:5432` (User: `postgres`, Password: `postgres`, DB: `vn_stock`)
- **Backend API**: `http://localhost:8000`
- **Frontend Web**: `http://localhost:3000`
- **ML Training Job**: Có thể kích hoạt batch job khi cần huấn luyện lại:
  ```bash
  docker compose run --rm ml-job
  ```

---

## 🧪 Kiểm Thử Tự Động (CI/CD)

Hệ thống tích hợp GitHub Actions (`.github/workflows/ci.yml`) tự động kiểm tra cú pháp, linting với **Ruff** và chạy **PyTest** cho mỗi lần commit hoặc tạo Pull Request.
