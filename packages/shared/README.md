# Shared Package (`packages/shared`)

Thư mục này được thiết kế để lưu trữ và quản lý các định nghĩa schemas, models và types dùng chung giữa **Backend API (`apps/api`)** và **Frontend Web (`apps/web`)**.

## 🎯 Mục đích & Định hướng phát triển
- **Đồng bộ hóa Contract**: Đảm bảo cấu trúc dữ liệu trả về từ API và dữ liệu tiếp nhận ở Web luôn đồng nhất (Type-safety end-to-end).
- **Tránh trùng lặp code**: Thay vì định nghĩa thủ công lại interface trên TypeScript ở Frontend và Pydantic BaseModel ở Backend, thư mục này là nguồn chân lý duy nhất (Single Source of Truth).
- **Tự động sinh mã (Code Generation)**:
  - Xuất OpenAPI spec (`openapi.json`) từ FastAPI.
  - Sử dụng các công cụ như `openapi-typescript` hoặc `orval` để tự động sinh TypeScript types / React Query hooks vào thư mục này.

*Hiện tại thư mục này được giữ khung sẵn sàng, chưa tạo nội dung giả.*
