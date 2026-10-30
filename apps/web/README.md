# VN Stock Web Dashboard (Next.js 16 & React 19)

Giao diện người dùng Web Dashboard theo phong cách Institutional Trading Terminal phục vụ:
- **Thị trường & Phân tích kỹ thuật**: Biểu đồ nến tương tác Canvas 60fps qua TradingView Lightweight Charts v5.2, chỉ báo động lượng RSI(14) và lưới 6 chỉ báo kỹ thuật.
- **Tín hiệu AI & Quỹ đạo $T+3$**: Trực quan hóa phân bổ xác suất Softmax 3 lớp, thẻ khuyến nghị Mua/Bán/Nắm giữ, biểu đồ Quỹ đạo 3 phiên FireAnt bám sát chu kỳ thanh toán bù trừ $T+2.5$ VSDC và Modal Retrain trực tuyến.
- **Phòng Giả lập Chiến lược DNSE EnTrade X 2 Cột**: Bộ điều khiển chiến thuật linh hoạt (ScopeSelector, DateRangePicker, 12 điều kiện mua + 12 điều kiện bán tùy biến qua DualRangeSlider, 8 chiến lược mẫu DNSE, quản lý lưu trữ chiến thuật cá nhân `strategyStorage`).
- **Thanh Header & Navbar thông minh**: Trạng thái phiên căn cứ (T hoặc T-1) theo mốc 15:00 kết thúc ATC, giờ UTC+7, nút kích hoạt đồng bộ dữ liệu SSI và Quick Stock Switcher rổ VN30.

## 🚀 Hướng dẫn khởi chạy

```bash
cd apps/web

# Cài đặt thư viện dependencies
npm install

# Khởi chạy server development
npm run dev

# Chạy toàn bộ 68 unit tests tự động với Vitest
npm test

# Build ứng dụng sản xuất
npm run build
```

Truy cập ứng dụng tại: [http://localhost:3000](http://localhost:3000)

## 🧪 Kiểm thử tự động (Vitest)
Hệ thống tích hợp bộ **68 unit tests PASSED (100%)**:
- `src/lib/api.test.ts`: 19 tests kiểm thử Web API Client, endpoints và offline fallback.
- `src/lib/strategyStorage.test.ts`: 49 tests kiểm thử logic lưu trữ, xuất/nhập, kiểm tra tính hợp lệ dữ liệu và quản lý chiến lược người dùng trong `localStorage`.
