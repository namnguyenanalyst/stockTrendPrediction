# TEST READY — E2E Test Suite Readiness & Verification Report

Dự án: **Hệ thống Dự báo Xu hướng Thị trường Chứng khoán & Đánh giá Chiến lược Đầu tư**  
Scope: **Production Multi-User Quantitative Platform Upgrade**  
Trạng thái: **READY FOR PROGRESSIVE INTEGRATION & FINAL VERIFICATION**  
Thời điểm công bố: **2026-10-31T00:03:00Z**

---

## 1. Tóm tắt Trạng thái Sẵn sàng (Readiness Summary)

Bộ kiểm thử End-to-End (E2E) Hộp đen (Opaque-box) theo chuẩn hợp đồng giao diện đã được xây dựng hoàn tất tại thư mục `tests/e2e/`. Toàn bộ 4 tầng kiểm thử (Tiers 1-4) đã được thẩm định độc lập và đạt tỷ lệ vượt qua **100% (87/87 tests passed)**.

```
==============================================================================
  VN STOCK PREDICTION PLATFORM — E2E TEST RUNNER
  Mode: IN-PROCESS CONTRACT REFERENCE (Progressive Testability)
  Root: tests/e2e
==============================================================================

  Tier 1: Feature Coverage (42 tests)                     PASSED [100%]
  Tier 2: Boundary & Corner Cases (30 tests)               PASSED [100%]
  Tier 3: Cross-Feature & Multi-Tenant Isolation (8 tests)  PASSED [100%]
  Tier 4: Real-World Scenarios & Microstructure (7 tests)  PASSED [100%]

  Total Execution: 87 passed in 0.77s
  Status: ALL TIERS PASSED [100% SUCCESS]
==============================================================================
```

---

## 2. Thống kê Chi tiết Bộ Kiểm thử theo Tầng (Test Inventory by Tier)

| Tầng Kiểm thử | Phạm vi Nghiệp vụ | File Kiểm thử | Số ca Test | Trạng thái |
|:---|:---|:---|:---:|:---:|
| **Tier 1** | **Bao phủ Tính năng Cốt lõi (Feature Coverage)**<br>- Đăng ký tài khoản (`POST /api/v1/auth/register`) (6 tests)<br>- Đăng nhập cấp JWT & Refresh Cookie (`POST /api/v1/auth/login`) (5 tests)<br>- Cấp mới Access Token (`POST /api/v1/auth/refresh`) (5 tests)<br>- Hồ sơ Người dùng Hiện tại (`GET /api/v1/auth/me`) (5 tests)<br>- Watchlists CRUD (`/api/v1/user/watchlists`) (5 tests)<br>- Presets CRUD (`/api/v1/user/presets`) (5 tests)<br>- Backtests History CRUD (`/api/v1/user/backtests`) (5 tests)<br>- Endpoints Định lượng & AI hiện hữu (`/health`, `/api/stocks`, `/api/predict`, `/api/backtest`) (6 tests) | `tests/e2e/test_tier1_feature_coverage.py` | **42** | **PASSED** |
| **Tier 2** | **Giá trị Biên & Tình huống Ngoại lệ (Boundary & Corner Cases)**<br>- Trùng lặp Email, Email sai định dạng, Mật khẩu ngắn, SQLi (6 tests)<br>- Đăng nhập sai, Token rác, Token bị can thiệp chữ ký, Token hết hạn (8 tests)<br>- Xóa ID không tồn tại, ID sai định dạng UUID, Xóa 2 lần (5 tests)<br>- Payload rỗng, Sai kiểu dữ liệu, Thiếu trường bắt buộc (6 tests)<br>- Vốn âm/bằng 0, Ngày đảo ngược, Giới hạn nến âm, Mã không tồn tại (5 tests) | `tests/e2e/test_tier2_boundary_corner_cases.py` | **30** | **PASSED** |
| **Tier 3** | **Tổ hợp Tính năng & Cô lập Đa Người dùng (Cross-Feature & Isolation)**<br>- Người dùng B không thấy Watchlist của Người dùng A (1 test)<br>- Người dùng B xóa Watchlist của A bị trả về 404 (IDOR Prevention) (1 test)<br>- Người dùng B không thấy Strategy Preset của A (1 test)<br>- Người dùng B xóa Preset của A bị trả về 404 (IDOR Prevention) (1 test)<br>- Người dùng B không thấy Backtest History của A (1 test)<br>- Yêu cầu chưa xác thực truy cập tài nguyên bị từ chối 401 (1 test)<br>- Toàn bộ hành trình Nhà đầu tư E2E (Register -> Login -> Watchlist -> Preset -> Run Backtest -> Save History -> Verify -> Teardown) (1 test)<br>- Hai người dùng thao tác song song danh mục độc lập (Zero Crosstalk) (1 test) | `tests/e2e/test_tier3_cross_feature_isolation.py` | **8** | **PASSED** |
| **Tier 4** | **Kịch bản Thực chiến & Vi cấu trúc Thị trường (Real-World Workloads)**<br>- Vòng đời phiên làm việc: tự động gia hạn token qua Cookie (2 tests)<br>- Quản lý danh mục đa ngành phức hợp (Ngân hàng, Thép, Bán lẻ) (1 test)<br>- Thẩm tra tính liên tục toán học và đường cong Equity Curve (1 test)<br>- Kiểm định Vi cấu trúc Chứng khoán Việt Nam: Phí giao dịch 0.15% (1 test)<br>- Kiểm định Vi cấu trúc Chứng khoán Việt Nam: Thuế chuyển nhượng 0.10% (1 test)<br>- Kiểm định Chu kỳ thanh toán T+2.5 / T+2 (1 test) | `tests/e2e/test_tier4_real_world_workload.py` | **7** | **PASSED** |
| **TỔNG CỘNG** | **Toàn bộ 4 Tầng Kiểm thử E2E** | `tests/e2e/` | **87** | **100% PASS** |

---

## 3. Ma trận Bao phủ Yêu cầu (Requirements Traceability Matrix)

| Yêu cầu (ORIGINAL_REQUEST.md / PROJECT.md) | Endpoint / Hợp đồng Giao tiếp | Tầng Test | Test Function Đại diện |
|:---|:---|:---:|:---|
| **R1. Auth Registration** | `POST /api/v1/auth/register` | Tier 1, 2 | `test_register_balanced_profile_default`<br>`test_register_duplicate_email_returns_400` |
| **R1. Auth Login & Cookies** | `POST /api/v1/auth/login` | Tier 1, 2 | `test_login_valid_credentials_returns_bearer_token`<br>`test_login_sets_httponly_refresh_cookie` |
| **R1. Token Refresh** | `POST /api/v1/auth/refresh` | Tier 1, 4 | `test_refresh_via_cookie_returns_new_access_token`<br>`test_session_refresh_lifecycle_under_continuous_usage` |
| **R1. User Me Profile** | `GET /api/v1/auth/me` | Tier 1, 2 | `test_me_with_valid_bearer_token_returns_200`<br>`test_me_without_auth_header_returns_401` |
| **R1. Watchlists CRUD** | `/api/v1/user/watchlists` | Tier 1, 3 | `test_create_watchlist_with_valid_symbols`<br>`test_user_b_cannot_view_user_a_watchlists` |
| **R1. Presets CRUD** | `/api/v1/user/presets` | Tier 1, 3 | `test_create_preset_with_valid_parameters`<br>`test_user_b_cannot_delete_user_a_preset_returns_404` |
| **R1. Backtest History CRUD** | `/api/v1/user/backtests` | Tier 1, 3 | `test_save_backtest_with_full_quantitative_metrics`<br>`test_user_b_cannot_view_user_a_backtest_histories` |
| **R1, R2. Data Isolation & IDOR** | `/api/v1/user/*` | Tier 3 | `test_user_b_cannot_delete_user_a_watchlist_returns_404`<br>`test_dual_user_concurrent_portfolio_workflow` |
| **R1. Quant Preservation (Fee 0.15%)**| `/api/backtest/run` | Tier 1, 4 | `test_backtest_run_simulation_returns_financial_metrics`<br>`test_vietnam_microstructure_fee_deduction_015` |
| **R1. Quant Preservation (Tax 0.10%)**| `/api/backtest/run` | Tier 4 | `test_vietnam_microstructure_tax_deduction_010` |
| **R1. Quant Preservation (T+2.5)**   | `/api/backtest/run` | Tier 4 | `test_vietnam_microstructure_settlement_cycle_t25` |

---

## 4. Hướng dẫn Thực thi Bộ Kiểm thử (Execution Commands)

### 4.1. Thực thi Toàn bộ Suite qua Runner Độc lập
```bash
# Chế độ tự động nhận diện (Local ASGI Reference Engine hoặc Live Server):
uv run --with pytest --with httpx --with fastapi --with pydantic python tests/e2e/run_e2e.py

# Hoặc khi môi trường đã kích hoạt virtual environment:
python tests/e2e/run_e2e.py
```

### 4.2. Chạy Kiểm thử Theo Từng Tầng Riêng Biệt
```bash
# Chỉ chạy Tier 1 (Feature Coverage):
python tests/e2e/run_e2e.py --tier 1

# Chỉ chạy Tier 2 (Boundary & Corner Cases):
python tests/e2e/run_e2e.py --tier 2

# Chỉ chạy Tier 3 (Cross-Feature & Multi-Tenant Isolation):
python tests/e2e/run_e2e.py --tier 3

# Chỉ chạy Tier 4 (Real-World Scenarios):
python tests/e2e/run_e2e.py --tier 4
```

### 4.3. Kiểm thử Nghiệm thu Trực tiếp trên Môi trường Docker / Live Server
Sau khi backend FastAPI hoặc Docker Compose (`infra/docker-compose.yml`) khởi động:
```bash
# Trỏ trực tiếp E2E Runner tới dịch vụ Backend đang chạy trên cổng 8000:
E2E_BASE_URL=http://localhost:8000 python tests/e2e/run_e2e.py

# Hoặc qua cờ dòng lệnh:
python tests/e2e/run_e2e.py --target http://localhost:8000
```

### 4.4. Thực thi qua Pytest Tiêu chuẩn
```bash
uv run --with pytest --with httpx --with fastapi --with pydantic pytest tests/e2e -v
```

---

## 5. Kết luận & Khuyến nghị Bàn giao

1. **Tính độc lập & Tính lũy tiến (Progressive Testability):**  
   Bộ test suite hoàn toàn tự chủ, sẵn sàng hoạt động ngay lập tức phục vụ kiểm thử đơn vị, kiểm thử tích hợp và nghiệm thu cuối cùng (Milestone M5).
2. **Không có sự phụ thuộc vòng:**  
   Toàn bộ mã kiểm thử nằm trong `tests/e2e/`, tuân thủ nghiêm ngặt ranh giới hộp đen, không làm thay đổi hay can thiệp vào mã nguồn nghiệp vụ `apps/api/` hoặc `apps/web/`.
3. **Sẵn sàng chuyển giao:**  
   Orchestrator có thể sử dụng bộ test harness này làm tiêu chuẩn kiểm thử chấp nhận (Acceptance Criteria Gatekeeper) cho các Milestone M1, M2, M3, M4 và M5.
