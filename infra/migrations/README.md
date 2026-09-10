# Database Migrations (`infra/migrations`)

Thư mục này được sử dụng để lưu trữ các script chuyển đổi và quản lý schema cơ sở dữ liệu (Database Schema Migrations), do Backend API (`apps/api`) chịu trách nhiệm quản trị (sử dụng công cụ như Alembic với SQLAlchemy / SQLModel).

## 🗄️ Luồng vận hành đề xuất
1. Khi định nghĩa mô hình bảng mới tại `apps/api/app/models/`:
   ```bash
   cd apps/api
   alembic revision --autogenerate -m "create_initial_stock_tables"
   ```
2. Áp dụng migration lên cơ sở dữ liệu PostgreSQL:
   ```bash
   alembic upgrade head
   ```

*Hiện tại thư mục này được để trống làm khung chờ, sẵn sàng khi bắt đầu phát triển tầng ORM/Database.*
