# Test Infrastructure & Strategy Specification

Dự án: **Hệ thống Dự báo Xu hướng Thị trường Chứng khoán & Đánh giá Chiến lược Đầu tư**  
Scope: **Production Multi-User Quantitative Platform (Phase 5 & E2E Testing Track)**  
Quy chuẩn: **Opaque-Box Requirement-Driven Multi-Tier Testing Infrastructure**

---

## 1. Triết lý & Phương pháp luận Kiểm thử (Test Philosophy & Methodologies)

Hệ thống kiểm thử End-to-End (E2E) được thiết kế theo nguyên tắc **Hộp đen tuyệt đối (Opaque-box Testing)** và **Dẫn dắt bởi yêu cầu (Requirement-driven Testing)**:
1. **Opaque-Box Boundaries (Biên giao tiếp Hộp đen):**
   - Mọi ca kiểm thử tương tác với hệ thống chỉ thông qua ranh giới giao thức HTTP công khai (REST API endpoints), HTTP status codes, JSON payload, Authorization Headers và HTTP-only Cookies.
   - Tuyệt đối không import trực tiếp database session nội bộ hoặc can thiệp trực tiếp vào ORM models trong luồng kiểm thử E2E; toàn bộ việc tạo lập, truy vấn, xác thực và dọn dẹp dữ liệu đều đi qua API chính thức.
2. **Category-Partition Method (Phương pháp Phân hoạch Danh mục):**
   - Phân tích không gian đầu vào thành các lớp tương đương (equivalence classes): tham số hợp lệ, tham số thiếu, tham số vượt ngưỡng, định dạng sai, và các loại quyền người dùng (`trader`, `admin`, `unauthenticated`).
3. **Boundary Value Analysis (BVA - Phân tích Giá trị Biên):**
   - Tập trung vào các điểm biên nhạy cảm: vốn đầu tư tối thiểu/tối đa, chu kỳ thanh toán chứng khoán Việt Nam ($T+2.5$, $T+2$, $T+3$), chuỗi nến lịch sử tối thiểu (5 nến), độ dài mật khẩu, token hết hạn tại ranh giới thời gian (0 giây vs 1 giây), và danh sách mã rỗng `[]`.
4. **Pairwise / Combinatorial Testing (Kiểm thử Tổ hợp Cặp):**
   - Phối hợp các chiều biến: `risk_profile` (`conservative`, `balanced`, `aggressive`) $\times$ `strategy_type` (`macd_crossover`, `bollinger_breakout`, `ensemble_ai`) $\times$ `role` (`trader`, `admin`) để đảm bảo phát hiện lỗi giao thoa dữ liệu.
5. **Workload & Multi-Tenant Scenario Testing (Kiểm thử Kịch bản Đa người dùng):**
   - Mô phỏng hành trình nhà đầu tư thực tế (Real-world Investor Lifecycle) từ đăng ký, đăng nhập, nạp danh mục theo dõi, cấu hình chiến lược, chạy backtest và lưu nhật ký.
   - Thẩm tra cô lập dữ liệu tuyệt đối giữa các người dùng (Zero Cross-Tenant Leakage & IDOR Prevention).

---

## 2. Ánh xạ Danh mục Tính năng (Feature Inventory Test Mapping)

Bảng ánh xạ từ **PROJECT.md § Feature Inventory** sang các kịch bản kiểm thử E2E:

| Feature # | Tên Tính năng | Endpoint / Contract | File Kiểm thử E2E | Số ca Test tối thiểu |
|:---:|:---|:---|:---|:---:|
| **F4, F5** | Đăng ký Người dùng mới | `POST /api/v1/auth/register` | `tests/e2e/test_tier1_feature_coverage.py` | 6 tests |
| **F4, F5** | Đăng nhập & Cấp JWT Token | `POST /api/v1/auth/login` | `tests/e2e/test_tier1_feature_coverage.py` | 5 tests |
| **F4, F5** | Cấp mới Access Token (Refresh) | `POST /api/v1/auth/refresh` | `tests/e2e/test_tier1_feature_coverage.py` | 5 tests |
| **F4, F5** | Hồ sơ Người dùng Hiện tại | `GET /api/v1/auth/me` | `tests/e2e/test_tier1_feature_coverage.py` | 5 tests |
| **F6** | Quản lý Watchlists Cá nhân | `GET`, `POST`, `DELETE /api/v1/user/watchlists` | `tests/e2e/test_tier1_feature_coverage.py` | 5 tests |
| **F6** | Quản lý Chiến lược Cá nhân (Presets) | `GET`, `POST`, `DELETE /api/v1/user/presets` | `tests/e2e/test_tier1_feature_coverage.py` | 5 tests |
| **F6** | Nhật ký Kiểm thử (Backtest History) | `GET`, `POST /api/v1/user/backtests` | `tests/e2e/test_tier1_feature_coverage.py` | 5 tests |
| **F7** | Tích hợp Định lượng & Suy luận AI | `/health`, `/api/stocks/*`, `/api/predict/*`, `/api/backtest/*` | `tests/e2e/test_tier1_feature_coverage.py` | 6 tests |
| **F4, F5** | Biên Đăng ký & Xác thực (Duplicate, Email, Malformed) | Auth Error Handlers (`400`, `401`, `422`) | `tests/e2e/test_tier2_boundary_corner_cases.py` | 7 tests |
| **F4, F5** | Biên Token JWT (Expired, Tampered, Missing) | JWT Authentication Guards (`401`) | `tests/e2e/test_tier2_boundary_corner_cases.py` | 6 tests |
| **F6** | Biên Xóa Tài nguyên & IDOR (Non-existent UUID, Bad format) | Resource Access Guards (`404`, `422`) | `tests/e2e/test_tier2_boundary_corner_cases.py` | 5 tests |
| **F6** | Biên Dữ liệu Cá nhân hóa (Rỗng, Sai kiểu, Schema lỗi) | Pydantic Request Validation (`422`) | `tests/e2e/test_tier2_boundary_corner_cases.py` | 5 tests |
| **F7** | Biên Định lượng & Thị trường (Vốn âm, Ngày đảo ngược) | Quant Validation (`400`, `422`) | `tests/e2e/test_tier2_boundary_corner_cases.py` | 5 tests |
| **F5, F6** | Cô lập Đa người dùng (Tenant Isolation & IDOR) | User A vs User B Isolation (`404`) | `tests/e2e/test_tier3_cross_feature_isolation.py` | 6 tests |
| **F5, F6, F7** | Hành trình Toàn diện Nhà đầu tư (Investor Journey) | Reg $\rightarrow$ Login $\rightarrow$ Preset $\rightarrow$ Backtest $\rightarrow$ Save | `tests/e2e/test_tier3_cross_feature_isolation.py` | 2 tests |
| **F4, F5** | Vòng đời Phiên thực tế & Tự động Gia hạn Token | Refresh Token Cookie lifecycle | `tests/e2e/test_tier4_real_world_workload.py` | 2 tests |
| **F6** | Quản lý Danh mục Đa chủ đề Phức hợp | Multiple watchlists per account | `tests/e2e/test_tier4_real_world_workload.py` | 2 tests |
| **F7** | Kiểm định Vi cấu trúc Chứng khoán VN (Phí, Thuế, T+2) | Fee 0.15%, Tax 0.10%, Lot 100, Equity Curve | `tests/e2e/test_tier4_real_world_workload.py` | 3 tests |

---

## 3. Kiến trúc Test Runner & Môi trường Thực thi

### 3.1. Cấu trúc Thư mục `tests/e2e/`
```
tests/e2e/
├── __init__.py
├── conftest.py                             # PyTest fixtures: clients, authentication helpers, test data generators
├── client.py                               # Lớp E2EClient đồng bộ/bất đồng bộ quản lý Bearer headers & Cookie jar
├── mock_server.py                          # In-process Contract Reference ASGI Server (phục vụ Progressive Testability)
├── test_tier1_feature_coverage.py          # Tier 1: Bao phủ toàn bộ tính năng cốt lõi (>=5 tests/feature)
├── test_tier2_boundary_corner_cases.py     # Tier 2: Biên giá trị, lỗi xác thực, lỗi dữ liệu, IDOR (>=5 tests/group)
├── test_tier3_cross_feature_isolation.py   # Tier 3: Tổ hợp tính năng & cô lập dữ liệu người dùng User A vs User B
├── test_tier4_real_world_workload.py       # Tier 4: Kịch bản thực chiến, gia hạn token, vi cấu trúc thị trường VN
└── run_e2e.py                              # CLI Test Runner độc lập với báo cáo trực quan và exit code chuẩn
```

### 3.2. Cơ chế Thực thi Linh hoạt (Dual-Mode Execution Architecture)
Hệ thống kiểm thử hỗ trợ 2 chế độ vận hành liền mạch thông qua biến môi trường `E2E_BASE_URL`:

1. **Chế độ Trực tuyến (Live Target Mode):**
   - Khi có dịch vụ backend đang chạy (ví dụ `http://localhost:8000` hoặc trong Docker container `vn_stock_api`).
   - `E2EClient` thực hiện kết nối HTTP thực sự qua mạng, gửi nhận gói tin JSON và Cookies.
   - Thích hợp cho nghiệm thu môi trường tích hợp và Docker Compose (Milestone M4 & M5).

2. **Chế độ Thẩm tra Khế ước Độc lập (In-Process Contract Reference Mode):**
   - Khi chạy trong môi trường CI cục bộ hoặc trước khi backend hoàn tất triển khai (Milestone E2E).
   - `E2EClient` sử dụng `httpx.ASGITransport` kết nối trực tiếp với ứng dụng chuẩn mực `contract_reference_app` được xây dựng bám sát 100% đặc tả tại `PROJECT.md § Interface Contracts`.
   - Đảm bảo kiểm tra toàn diện logic phân tích cú pháp HTTP, mã trạng thái `200`, `201`, `204`, `400`, `401`, `404`, `422`, mã hóa Bcrypt, ký xác thực JWT và cô lập người dùng ngay lập tức mà không phụ thuộc vào trạng thái cơ sở dữ liệu bên ngoài.

---

## 4. Đặc tả 4 Tầng Kiểm thử (The 4-Tier Test Matrix)

### Tier 1: Bao phủ Tính năng (Feature Coverage)
- **Mục tiêu:** Kiểm tra đường thuận lợi (Happy Path) và các biến thể hợp lệ của mọi endpoint.
- **Tiêu chuẩn:** Tối thiểu 5 ca kiểm thử độc lập cho mỗi nhóm tính năng.
- **Phạm vi:**
  - `auth_register`: 3 risk profile (`conservative`, `balanced`, `aggressive`), full name tiếng Việt có dấu, giá trị mặc định, ẩn mật khẩu.
  - `auth_login`: Đăng nhập thành công, trả về Access Token + Refresh Token cookie, phân biệt chữ hoa/thường email.
  - `auth_refresh`: Cấp mới access token qua cookie và body, xác thực tính hợp lệ của token mới.
  - `auth_me`: Đọc thông tin người dùng hiện tại, định dạng UUID, không rò rỉ hash mật khẩu.
  - `user_watchlists`: Tạo danh mục cổ phiếu, liệt kê danh mục, xóa danh mục (`204 No Content`).
  - `user_presets`: Tạo cấu hình chiến lược với JSONB parameters, liệt kê và xóa.
  - `user_backtests`: Lưu kết quả kiểm thử định lượng kèm chuỗi `equity_curve`, liệt kê theo thứ tự thời gian.
  - `quant_endpoints`: Truy vấn `/health`, danh sách mã VN30 `/api/stocks/symbols`, nến lịch sử, chỉ báo, dự báo AI, backtest mô phỏng.

### Tier 2: Giá trị Biên & Tình huống Góc (Boundary & Corner Cases)
- **Mục tiêu:** Thử thách khả năng phòng thủ của hệ thống trước dữ liệu bất thường và tấn công cơ bản.
- **Tiêu chuẩn:** Tối thiểu 5 ca kiểm thử cho từng nhóm ngoại lệ.
- **Phạm vi:**
  - Email trùng lặp $\rightarrow$ `400 Bad Request`.
  - Định dạng email sai, mật khẩu quá ngắn $\rightarrow$ `422 Unprocessable Entity`.
  - Token JWT giả mạo, token hết hạn, thiếu Authorization header $\rightarrow$ `401 Unauthorized`.
  - Xóa ID không tồn tại hoặc ID sai định dạng $\rightarrow$ `404 Not Found` / `422`.
  - Payload JSONB rỗng, thiếu trường bắt buộc $\rightarrow$ `422`.
  - Vốn đầu tư ban đầu âm hoặc bằng 0, khoảng thời gian ngược $\rightarrow$ `422` / `400`.
  - Thử nghiệm chuỗi ký tự SQL Injection và XSS trong tên và email.

### Tier 3: Tổ hợp Tính năng & Cô lập Dữ liệu (Cross-Feature & Multi-Tenant Isolation)
- **Mục tiêu:** Xác minh tính toàn vẹn nghiệp vụ xuyên suốt và bảo mật đa người dùng.
- **Phạm vi:**
  - **Hành trình Toàn diện Nhà đầu tư (Investor Journey):**
    Đăng ký $\rightarrow$ Đăng nhập $\rightarrow$ Đọc danh sách cổ phiếu $\rightarrow$ Tạo watchlist $\rightarrow$ Tạo cấu hình chiến lược $\rightarrow$ Chạy mô phỏng định lượng $\rightarrow$ Lưu lịch sử backtest kèm đường cong tài sản $\rightarrow$ Kiểm tra nhật ký lưu trữ $\rightarrow$ Xóa dọn dẹp.
  - **Bảo mật Cô lập Đa Người dùng (Multi-Tenant Isolation & IDOR Prevention):**
    - Tạo song song Người dùng A (`user_a`) và Người dùng B (`user_b`).
    - Người dùng B gọi `GET /api/v1/user/watchlists` $\rightarrow$ Tuyệt đối không thấy watchlist của Người dùng A.
    - Người dùng B cố tình gọi `DELETE /api/v1/user/watchlists/{watchlist_a_id}` $\rightarrow$ Hệ thống trả về `404 Not Found` (ngăn chặn rò rỉ sự tồn tại của tài nguyên - IDOR Prevention).
    - Người dùng B gọi `GET /api/v1/user/presets` $\rightarrow$ Không thấy preset của Người dùng A.
    - Người dùng B cố tình thao tác preset của A $\rightarrow$ `404 Not Found`.
    - Người dùng B gọi `GET /api/v1/user/backtests` $\rightarrow$ Không thấy lịch sử kiểm thử của Người dùng A.

### Tier 4: Kịch bản Ứng dụng Thực chiến (Real-World Application Scenarios)
- **Mục tiêu:** Thẩm tra hệ thống trong điều kiện tải nghiệp vụ thực tế và tuân thủ quy chế thị trường chứng khoán.
- **Phạm vi:**
  - **Vòng đời Phiên làm việc thực tế:** Mô phỏng phiên làm việc kéo dài, access token hết hạn, client tự động dùng refresh token cookie lấy access token mới và tiếp tục thực hiện giao dịch mà không làm gián đoạn người dùng.
  - **Quản lý Danh mục phức hợp:** Người dùng sở hữu nhiều danh mục theo chủ đề (Thép, Ngân hàng, Bán lẻ), bổ sung và cập nhật mã.
  - **Thẩm định Chuỗi Equity Curve:** Kiểm tra tính liên tục của dữ liệu tài sản theo thời gian, điểm bắt đầu bằng vốn ban đầu, điểm kết thúc khớp với `total_return`.
  - **Kiểm định Vi cấu trúc Chứng khoán Việt Nam:**
    - Phí giao dịch chuẩn: trừ đúng $0.15\%$ mỗi chiều Mua và Bán.
    - Thuế bán chứng khoán: trừ đúng $0.10\%$ giá trị chuyển nhượng chiều Bán.
    - Chu kỳ thanh toán $T+2.5$ / $T+2$: tiền và cổ phiếu về tài khoản theo đúng quy định VSD.
    - Lô giao dịch tối thiểu: 100 cổ phiếu (HSX, HNX).

---

## 5. Hướng dẫn Chạy Kiểm thử & Tiêu chuẩn Nghiệm thu

### 5.1. Lệnh Thực thi Test Suite
Chạy toàn bộ bộ test E2E qua PyTest hoặc Test Runner chuyên dụng:
```bash
# 1. Chạy thông qua PyTest
uv run pytest tests/e2e -v

# 2. Chạy thông qua Test Runner độc lập
python tests/e2e/run_e2e.py

# 3. Chạy kiểm thử mục tiêu trực tiếp vào Live Server
E2E_BASE_URL=http://localhost:8000 python tests/e2e/run_e2e.py

# 4. Chạy từng tầng kiểm thử riêng biệt
python tests/e2e/run_e2e.py --tier 1
python tests/e2e/run_e2e.py --tier 2
python tests/e2e/run_e2e.py --tier 3
python tests/e2e/run_e2e.py --tier 4
```

### 5.2. Tiêu chuẩn Nghiệm thu (Exit Criteria)
- Toàn bộ các ca kiểm thử trong 4 Tầng đều đạt trạng thái `PASSED` (100% pass rate).
- Exit code của tiến trình runner trả về chính xác `0`.
- Không có lỗi rò rỉ dữ liệu chéo người dùng (Zero IDOR vulnerabilities).
- Dữ liệu vi cấu trúc tài chính (thuế, phí) được tính toán chính xác tới 4 chữ số thập phân.
