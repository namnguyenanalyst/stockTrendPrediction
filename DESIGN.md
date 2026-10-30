---
name: "VN Stock Quantitative & Prediction Dashboard"
description: "Flat Minimalist financial interface for Vietnamese stock trend prediction and quantitative backtesting"
colors:
  neutral-bg: "#020617" # Slate 950
  surface-card: "#0f172a" # Slate 900
  surface-hover: "#1e293b" # Slate 800
  border: "#334155" # Slate 700 (1px hairline border)
  border-subtle: "rgba(51, 65, 85, 0.4)"
  text-primary: "#f8fafc" # High-contrast crisp white (Slate 50)
  text-secondary: "#cbd5e1" # Slate 300
  text-muted: "#94a3b8" # Slate 400
  text-dim: "#64748b" # Slate 500
  brand-blue: "#3b82f6" # System actions & active tabs (Blue 500)
  stock-up: "#10b981" # Market UP / BUY / Profit (Emerald 500)
  stock-down: "#f43f5e" # Market DOWN / SELL / Loss (Rose 500)
  stock-ref: "#f59e0b" # Market FLAT / REFERENCE / HOLD (Amber 500)
  stock-ceil: "#a855f7" # Ceiling price (Purple 500)
  stock-floor: "#06b6d4" # Floor price (Cyan 500)
typography:
  display:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0em"
  data-mono:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0em"
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  card:
    backgroundColor: "{colors.surface-card}"
    rounded: "{rounded.md}"
    padding: "16px"
  button-primary:
    backgroundColor: "{colors.brand-blue}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  badge-success:
    backgroundColor: "rgba(16, 185, 129, 0.15)"
    textColor: "{colors.stock-up}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  badge-danger:
    backgroundColor: "rgba(244, 63, 94, 0.15)"
    textColor: "{colors.stock-down}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
---

# Design System: Flat Minimalist Financial Dashboard

## Overview
Hệ thống thiết kế theo phong cách **Flat Minimalist (Tối giản phẳng)** được xây dựng chuyên biệt cho màn hình làm việc (Operate Mode) của **Hệ thống Dự báo Xu hướng Chứng khoán & Đánh giá Chiến lược Đầu tư**.
Mục tiêu cốt lõi:
- **Tối giản thị giác:** Triệt tiêu mọi yếu tố trang trí rườm rà (gradient tím AI, bóng đổ mờ nhòe nhiều tầng, hoạt họa nảy tưng bừng).
- **Mật độ thông tin chuẩn mực:** Dữ liệu tài chính, biểu đồ nến kỹ thuật và kết quả mô hình AI là trung tâm của trải nghiệm.
- **Thân thiện với người dùng phổ thông:** Mọi chỉ số định lượng đều có chú thích bình dân, trực quan, dễ hiểu ngay tại màn hình.

## Colors
Bảng màu tuân thủ nghiêm ngặt nguyên tắc **Restrained Semantic Palette (Bảng màu ngữ nghĩa tối chế)**:
1. **Màu nền trung tính (Dark Theme cao cấp):**
   - Nền trang chính: `bg-slate-950` (`#020617`).
   - Thẻ nội dung (Cards/Panels): `bg-slate-900` (`#0f172a`).
   - Đường viền chia tách: `border-slate-800` (`#1e293b`) hoặc `border-slate-700/60`.
2. **Quy chuẩn màu bảng điện chứng khoán Việt Nam:**
   - **Xanh lục (`emerald-500` / `#10b981`):** Tín hiệu TĂNG, khuyến nghị MUA, lệnh chốt LỜI.
   - **Đỏ hồng (`rose-500` / `#f43f5e`):** Tín hiệu GIẢM, khuyến nghị BÁN, lệnh cắt LỖ.
   - **Vàng cam (`amber-500` / `#f59e0b`):** Xu hướng ĐI NGANG, giá THAM CHIẾU, trạng thái GIỮ TIỀN MẶT, cảnh báo rủi ro.
   - **Tím (`purple-500`):** Chỉ dùng duy nhất cho giá TRẦN (Ceiling Price) trên thị trường.
   - **Xanh lơ (`cyan-500`):** Chỉ dùng duy nhất cho giá SÀN (Floor Price) trên thị trường.
3. **Màu điều hướng & Tác vụ hệ thống:**
   - **Xanh dương (`blue-600` / `#2563eb`):** Nút hành động chính (Chạy mô phỏng, Chạy dự báo AI, Tab đang chọn).

## Typography
- **Phông chữ giao diện (Sans-serif):** `Inter` hoặc System Font (`font-sans`), phân cấp rõ ràng:
  - Tiêu đề màn hình: `text-xl font-bold tracking-tight text-white`.
  - Tiêu đề thẻ/khối: `text-sm font-semibold text-slate-200`.
  - Văn bản nội dung: `text-xs text-slate-300` hoặc `text-sm text-slate-300`.
  - Phụ đề & giải thích: `text-xs text-slate-400`.
- **Phông chữ số liệu tài chính (`font-mono` / `tabular-nums`):**
  - Mọi con số (Giá, %, PnL, Khối lượng, Sharpe Ratio, MDD) bắt buộc hiển thị phông đơn cách để các cột bảng thẳng hàng tuyệt đối.

## Layout
- **Cấu trúc lưới phẳng (Flat Modular Grid):**
  - Header trên cùng (TopHeader) tinh gọn: hiển thị logo, ticker đang chọn, giá hiện tại, thời gian giao dịch thực tế.
  - Khối biểu đồ nến kỹ thuật chiếm vị trí trung tâm, trực quan, hỗ trợ phóng to thu nhỏ mượt mà.
  - Các Tab chức năng (Market Overview, AI Prediction, Backtest Simulator) tổ chức theo thanh điều hướng phẳng (underline/pill phẳng tối giản).
  - Tối ưu khoảng đệm (Padding & Gap): `p-4` / `gap-4` thoáng đãng, dễ quét mắt.

## Elevation & Depth
- **Tuyệt đối không dùng bóng đổ nặng (`shadow-xl`, `shadow-2xl`, colored glow shadows):**
  - Mọi độ sâu được tạo bởi **tương phản sắc độ bề mặt** (`bg-slate-950` nền $\rightarrow$ `bg-slate-900` thẻ $\rightarrow$ `bg-slate-800` ô nhập liệu/nút bấm).
  - Viền phân cách hairline mảnh 1px (`border border-slate-800`) giữ cho các khối vuông vắn, sắc nét.

## Shapes
- Bo góc đồng nhất:
  - Khối/Thẻ: `rounded-lg` (8px).
  - Nút bấm, Ô nhập liệu, Tag: `rounded-md` (6px).
  - Badge trạng thái nhỏ: `rounded` (4px).
  - Loại bỏ các góc bo tròn quá lớn dạng hoạt hình (`rounded-3xl`).

## Components
1. **Thẻ dữ liệu phẳng (Flat Card):**
   - Nền `bg-slate-900/80`, viền `border border-slate-800/80`, padding `p-4`, không đổ bóng.
2. **Nút bấm hành động (Buttons):**
   - Nút chính (Primary): `bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs rounded-md px-3 py-2 transition-colors`.
   - Nút phụ (Secondary): `bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/60 text-xs rounded-md px-3 py-2`.
3. **Thẻ chỉ số định lượng có giải thích bình dân (Metric Card with Plain Explanation):**
   - Tiêu đề chỉ số kèm icon hỏi chấm nhỏ hoặc tooltip:
     - *Tổng lợi nhuận (Total Return)*: % lãi/lỗ tài sản so với số vốn ban đầu 100 triệu VNĐ.
     - *Chỉ số Sharpe (Sharpe Ratio)*: Đo lường mức sinh lời trên 1 đơn vị rủi ro (> 1.0 là chiến lược tốt).
     - *Sụt giảm tối đa (Max Drawdown)*: Tỷ lệ lỗ lớn nhất từ đỉnh tài sản xuống đáy (đo rủi ro chịu đựng).
     - *Tỷ lệ thắng (Win Rate)*: Tỷ lệ phần trăm các thương vụ có lãi trên tổng số lệnh.
     - *Chu kỳ T+2*: Cổ phiếu mua về tài khoản sau 2 phiên giao dịch mới được bán (theo luật chứng khoán Việt Nam).
4. **Modal / Hộp thoại điều kiện:**
   - Nền mờ tối giản `bg-slate-950/80 backdrop-blur-sm`, hộp thoại `bg-slate-900 border border-slate-700/80 rounded-lg`.

## Do's and Don'ts
### Do's:
- Sử dụng chữ trắng/sáng rõ nét (`text-white` hoặc `text-slate-100`) trên mọi nền màu hoặc nền tối.
- Gắn giải thích ngắn gọn, dễ hiểu cho toàn bộ các thuật ngữ tài chính và chỉ số máy học.
- Dùng màu xanh/đỏ/vàng chuẩn mực theo đúng quy ước giao dịch tài chính.
- Sử dụng `font-mono` cho toàn bộ số liệu tiền và phần trăm.

### Don'ts:
- **KHÔNG dùng gradient tím-hồng AI slop** (`from-purple-400 to-indigo-300`).
- **KHÔNG dùng chữ xám mờ trên nền có màu** (`text-slate-100` trên nền `bg-rose-500` $\rightarrow$ đổi thành `text-white font-semibold`).
- **KHÔNG dùng animation nảy tưng tưng** (`animate-bounce` $\rightarrow$ đổi thành icon tĩnh thanh lịch hoặc nhịp thở nhẹ `opacity-80`).
- **KHÔNG dùng bóng đổ phát sáng lòe loẹt** (`shadow-emerald-500/20`, `shadow-rose-500/20`).
- **KHÔNG viết tắt thuật ngữ mà không có chú thích** (người dùng phổ thông không thể tự hiểu Sharpe, Sortino hay Purged Horizon nếu không có tooltip/phụ đề).

