# ANTIGRAVITY AGENT CONFIGURATION & DEVELOPMENT FRAMEWORK

Dự án: **Hệ thống Dự báo Xu hướng Thị trường Chứng khoán & Đánh giá Chiến lược Đầu tư**  
Đơn vị: Trường Đại học Mỏ - Địa chất | Khoa Công nghệ Thông tin  
Chuyên ngành: Tin học kinh tế  
Quy chuẩn báo cáo: [docs/Cấu trúc báo cáo ĐATN.md](docs/Cấu trúc báo cáo ĐATN.md)

---

## 1. BẢN ĐỒ VAI TRÒ & PHÂN CẤP CÔNG CỤ (ROLES & TOOLING ARCHITECTURE)

Hệ thống Agent vận hành theo mô hình phân tầng chặt chẽ giữa **Dự án (Project Scope)** và **Toàn cục (Global Scope)**:

### 1.1. Các vai trò chuyên trách của Dự án (Project-scoped Agents - `.agents/rules/`)
1. **Senior Quantitative Analyst (`quant-analyst`):**
   - Chịu trách nhiệm về logic tài chính, vi cấu trúc thị trường chứng khoán Việt Nam (HSX, HNX).
   - Kiểm thử chiến lược (Backtesting), mô phỏng trượt giá (Slippage), tính đúng phí giao dịch (0.15%) và thuế thu nhập chuyển nhượng (0.1%).
   - Đo lường rủi ro danh mục: Sharpe Ratio, Sortino Ratio, Maximum Drawdown (MDD), Value-at-Risk (VaR).
2. **Senior Machine Learning Engineer (`ml-engineer`):**
   - Chịu trách nhiệm về toàn bộ vòng đời ML sản xuất (End-to-end Production ML Lifecycle).
   - Tổ chức module theo chuẩn Cookiecutter Data Science v2 (CCDS v2) tại `apps/ml`.
   - Xây dựng pipeline dữ liệu tự động, trích xuất đặc trưng, huấn luyện mô hình (PyTorch LSTM/GRU, XGBoost), đánh giá và xuất artifact.
3. **Senior Frontend Developer (`frontend-developer`):**
   - Chịu trách nhiệm về tầng giao diện người dùng Web Dashboard tại `apps/web` (Next.js 15+, React 19, TypeScript).
   - Xây dựng hệ thống UI tương tác cao: biểu đồ nến kỹ thuật, tín hiệu Mua/Bán thời gian thực, đường cong tài sản (Equity Curve), bảng thống kê chỉ số định lượng.
   - Đảm bảo tính trải nghiệm (UX), thiết kế chuẩn responsive, khả năng truy cập (a11y) và tối ưu hóa hiệu năng render.
4. **Academic Researcher (`academic-researcher`):**
   - Chuyên gia tra cứu tài liệu học thuật (arXiv, Semantic Scholar, OpenAlex, Crossref), trích xuất phương pháp luận mô hình định lượng.
   - Hỗ trợ xây dựng Chương 2 (Cơ sở lý thuyết), Chương 3 và tổng quan nghiên cứu thực nghiệm.
5. **Senior Data Scientist (`data-scientist`):**
   - Chịu trách nhiệm phân tích khám phá dữ liệu (EDA), phân tích phân phối, tương quan đặc trưng và phát hiện bất thường.
   - Kiểm định giả thuyết thống kê, kiểm tra tính dừng (Stationarity), phân rã chuỗi thời gian (Trend, Seasonality) và giải thích mô hình (SHAP, Feature Importance).

### 1.2. Các vai trò kế thừa Toàn cục (Globally-inherited Agents - `~/.gemini/config/rules/` & `~/.claude/agents/`)
* **Senior Fullstack Developer (`fullstack-developer`):** Chuyên gia tích hợp toàn diện kiến trúc Monorepo (FastAPI, Next.js App Router, PostgreSQL 16, Docker Compose) phục vụ Phase 5.
* **Academic Researcher (`academic-researcher`):** Vai trò nghiên cứu học thuật cấp toàn cục dùng chung cho các dự án.

### 1.3. Kho Kỹ năng chuyên sâu theo nhu cầu (On-Demand Skills - `.agents/skills/` & Global)
Agent tự động kích hoạt kỹ năng tương ứng khi thực hiện tác vụ liên quan:
* **`clean-code` (Global - `~/.gemini/config/skills/`):** Bộ chuẩn mực viết code tinh gọn (KISS, DRY, SRP, YAGNI), hàm ngắn gọn (<20 dòng), đặt tên bộc lộ ý định, loại bỏ code thừa.
* **`generate-tests` (Global & Project):** Khung sinh bộ kiểm thử tự động toàn diện theo chuẩn AAA (Arrange, Act, Assert), bao phủ 80%+ logic nghiệp vụ cho PyTest (`apps/ml`, `apps/api`) và Vitest (`apps/web`).
* **`systematic-debugging`:** Quy trình chẩn đoán lỗi có hệ thống, tìm nguyên nhân gốc (root-cause tracing), tránh sửa code mò mẫm.
* **`python-testing-patterns`:** Chuẩn mực kiểm thử tự động với PyTest, fixtures, mocks cho các pipeline trong `apps/ml/tests/`.
* **`postgres-best-practices`:** Chuẩn tối ưu hóa CSDL PostgreSQL từ Supabase (index thời gian + ticker, pooling, batch insert dữ liệu OHLCV).
* **`fastapi-pro`:** Chuẩn phát triển REST API bất đồng bộ với FastAPI, Pydantic V2, OpenAPI docs tại `apps/api`.
* **`nextjs-best-practices`:** Chuẩn phát triển Frontend Dashboard với Next.js App Router, Server Components và trực quan hoá biểu đồ tại `apps/web`.

### 1.4. Hạ tầng MCP Servers tích hợp
* **`postgresql` (Project - `.mcp.json`):** Kết nối CSDL `postgresql://postgres:postgres@localhost:5432/vn_stock`.
* **`arxiv-mcp-server` (Global & Project):** Tra cứu paper khoa học, trích xuất abstract và metadata trực tiếp từ arXiv.
* **`github` (Global - `mcp_config.json`):** Quản lý mã nguồn, tra cứu repository tham khảo qua GitHub Personal Access Token.
* **`chrome-devtools-mcp` (Global - `mcp_config.json`):** Hỗ trợ kiểm thử trực quan giao diện frontend, chụp màn hình và đo kiểm hiệu năng rendering trên trình duyệt.
* **`postman-mcp-server` (Global - `mcp_config.json`):** Hỗ trợ kiểm thử, đồng bộ và xác thực các endpoint REST API backend.

---

## 2. NGUYÊN TẮC LIÊM CHÍNH HỌC THUẬT (ACADEMIC RIGOR & NO HALLUCINATION)

> [!CRITICAL]
> **Tuyệt đối không bịa đặt nguồn, số liệu, thuật toán hay bài báo nghiên cứu.**

* **Xác thực nguồn chính thức (Official Sources Only):**
  - Mọi định nghĩa, công thức toán và kiến trúc mô hình phải được tra cứu từ tài liệu chính thức (Official Docs của PyTorch, Scikit-learn, XGBoost, TA-Lib, FastAPI) hoặc bài báo khoa học đã xuất bản.
  - Khi tra cứu tài liệu khoa học: chỉ dẫn nguồn từ các kho uy tín: arXiv, IEEE Xplore, ScienceDirect, Springer, ACM, Google Scholar.
* **Định dạng trích dẫn chuẩn IEEE:**
  - Áp dụng chuẩn IEEE dạng đánh số `[1]`, `[2]` theo đúng quy cách của Khoa CNTT - ĐH Mỏ - Địa chất.
  - Mỗi trích dẫn phải có đủ thông tin có thật: Tác giả, Tên bài báo/sách, Tạp chí/Hội nghị, Năm công bố, DOI hoặc liên kết arXiv.
* **Nguyên tắc "Biết thì nói, không biết thì tra cứu":**
  - Nếu một giả thuyết hoặc thông số chưa được kiểm chứng, Agent phải nói rõ là *giả định cần thực nghiệm* hoặc *yêu cầu tra cứu thêm*, tuyệt đối không tự bịa số liệu.

---

## 3. KỶ LUẬT MACHINE LEARNING CHUỖI THỜI GIAN & TÀI CHÍNH

1. **Tuyệt đối chống rò rỉ dữ liệu tương lai (No Lookahead Bias / Data Leakage):**
   - Cấm sử dụng k-fold Cross-Validation ngẫu nhiên cho chuỗi thời gian. Bắt buộc dùng **Walk-forward Validation (Expanding / Rolling Window)** hoặc **TimeSeriesSplit**.
   - Feature Scaling (MinMaxScaler, StandardScaler) và Imputation chỉ được `fit` trên tập Train, sau đó áp dụng `transform` lên Validation/Test.
   - Nhãn $y_{t+1}$ hoặc $y_{t+k}$ phải được dịch chuyển thời gian đúng chuẩn (`shift(-1)`), các chỉ báo kỹ thuật tại thời điểm $t$ chỉ được tính dựa trên thông tin $t$ trở về trước.
2. **Backtesting sát với thực tế thị trường chứng khoán Việt Nam:**
   - Khớp lệnh có độ trễ chu kỳ thanh toán ($T+2.5$ / $T+2$).
   - Trừ đủ chi phí giao dịch: tối thiểu **0.15% phí giao dịch mỗi chiều** và **0.1% thuế bán chứng khoán**.
   - So sánh đối chứng bắt buộc: Mọi chiến lược AI/Quant phải được so sánh với chiến lược cơ sở chuẩn (Baseline: Buy & Hold VN-Index hoặc cổ phiếu mục tiêu).

---

## 4. BỘ KHUNG PHÁT TRIỂN 5 GIAI ĐOÀN (5-PHASE METHODOLOGICAL FRAMEWORK)

Mọi bước xây dựng hệ thống phải bám sát 5 giai đoạn liên hoàn, ánh xạ trực tiếp sang 5 chương của Đồ án Tốt nghiệp:

```mermaid
graph TD
    P1[Phase 1: Khảo sát & Dữ liệu SSI] --> P2[Phase 2: Đặc trưng & Time-Series Split]
    P2 --> P3[Phase 3: Huấn luyện Mô hình LSTM/XGBoost]
    P3 --> P4[Phase 4: Backtesting Engine & Đo lường Rủi ro]
    P4 --> P5[Phase 5: Đóng gói API, Web Dashboard & Báo cáo]
```

### Phase 1: Khảo sát bài toán & Thu thập dữ liệu (Tương ứng Chương 1 & Chương 3)
* Thu thập dữ liệu nến OHLCV từ SSI Fast Connect API (`fc-data.ssi.com.vn`).
* Tổ chức dữ liệu theo chuẩn CCDS v2: `apps/ml/data/raw/` $\rightarrow$ `interim/` $\rightarrow$ `processed/`.
* Xử lý missing values, kiểm định tính liên tục của ngày giao dịch, kiểm tra chia tách cổ tức/cổ phiếu.

### Phase 2: Kỹ thuật Đặc trưng & Kiểm định (Tương ứng Chương 2 & Chương 3)
* Trích xuất các nhóm chỉ báo kỹ thuật:
  - Xu hướng: SMA (20, 50), EMA (12, 26), MACD.
  - Động lượng: RSI (14), Stochastic.
  - Biến động: Bollinger Bands, ATR, Historical Volatility.
  - Khối lượng: Volume SMA, OBV.
* Phân tích tương quan đặc trưng, loại bỏ đa cộng tuyến.
* Thiết lập khung chia tập dữ liệu Walk-forward nghiêm ngặt.

### Phase 3: Xây dựng & Huấn luyện Mô hình (Tương ứng Chương 2 & Chương 4)
* Mô hình chính: PyTorch LSTM / GRU đa biến (Multivariate Time Series).
* Mô hình đối chứng (Baseline): XGBoost / Random Forest.
* Thiết lập Early Stopping, Loss function phù hợp (BCEWithLogitsLoss cho phân loại xu hướng Tăng/Giảm; MSE/Huber Loss cho dự báo giá).
* Lưu trữ artifact mô hình (`.pth`, `.json`), tham số scaler (`.pkl`) và log thực nghiệm.

### Phase 4: Động cơ Backtesting & Đánh giá Tài chính (Tương ứng Chương 4 & Chương 5)
* Xây dựng engine mô phỏng giao dịch trừ phí thuế.
* Đánh giá hiệu quả bằng các chỉ số định lượng:
  - Kỹ thuật: Accuracy, F1-Score, Precision, Recall, AUC-ROC (hoặc RMSE, MAE, MAPE).
  - Tài chính: Total Return (ROI), Annualized Return, Sharpe Ratio, Sortino Ratio, Maximum Drawdown (MDD), Win Rate, Profit Factor.
* So sánh chiến lược AI vs Chiến lược Mua & Nắm giữ (Buy & Hold).

### Phase 5: Đóng gói Hệ thống Full-stack & Hoàn thiện ĐATN (Tương ứng Chương 5)
* Triển khai REST API với FastAPI (`apps/api`) phục vụ suy luận trực tuyến (`/predict`, `/backtest`) (`fullstack-developer` điều phối).
* Xây dựng Dashboard Web với Next.js & TypeScript (`apps/web`) trực quan hóa biểu đồ nến, tín hiệu Mua/Bán và đường cong tài sản (Equity Curve) (`frontend-developer` phụ trách UI/UX, tích hợp biểu đồ).
* Đóng gói Docker Compose (`infra/docker-compose.yml`) điều phối PostgreSQL, API và Web.
* Viết và chuẩn hóa tài liệu Báo cáo ĐATN bám sát 5 chương, 34 mục trong [docs/Cấu trúc báo cáo ĐATN.md](docs/Cấu trúc báo cáo ĐATN.md) (kết hợp `academic-researcher` kiểm tra trích dẫn chuẩn IEEE).

---

## 5. QUY CHUẨN MÃ NGUỒN & CẤU TRÚC MONOREPO

* **Codebase structure:** Tuân thủ phân cấp `apps/ml`, `apps/api`, `apps/web`, `packages/shared`, `infra/`.
* **Kiểm thử tự động:** Mọi module trong `apps/ml/vn_stock/` phải có test tương ứng trong `apps/ml/tests/`, kiểm tra chạy đạt trước khi chuyển giai đoạn (`uv run pytest`).
* **Quản lý môi trường:** Sử dụng `uv` cho Python packages, đảm bảo `pyproject.toml` và `uv.lock` đồng bộ.
