# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Nhà đầu tư cá nhân phổ thông tại thị trường chứng khoán Việt Nam (HSX, HNX), người tham gia hội đồng chấm Đồ án Tốt nghiệp (giảng viên, sinh viên). Họ cần một công cụ phân tích kỹ thuật và dự báo xu hướng chứng khoán hỗ trợ ra quyết định đầu tư an toàn, minh bạch, dễ hiểu mà không bị ngập trong các thuật ngữ chuyên sâu khó tiếp cận.

## Product Purpose

Hệ thống Dự báo Xu hướng Thị trường Chứng khoán & Đánh giá Chiến lược Đầu tư (ĐATN Khoa CNTT - Đại học Mỏ - Địa chất). Sản phẩm cung cấp khả năng quan sát biểu đồ giá nến kỹ thuật thời gian thực, đưa ra khuyến nghị Mua/Bán dựa trên mô hình học máy (LightGBM & Global LSTM) và kiểm thử chiến lược đầu tư (Backtesting) mô phỏng chính xác chu kỳ thanh toán T+2 và phí thuế thực tế tại Việt Nam. Thành công nghĩa là người dùng phổ thông hiểu được lý do tại sao mô hình đưa ra tín hiệu, tự tin thử nghiệm chiến lược và nắm rõ rủi ro.

## Positioning

Công cụ dự báo tài chính minh bạch cho thị trường Việt Nam:
- Không "hộp đen": Mô hình AI đi kèm xác suất rõ ràng và giải thích đặc trưng (XAI SHAP).
- Không mô phỏng phi thực tế: Backtesting tính đúng 0.15% phí giao dịch và 0.1% thuế chuyển nhượng, tôn trọng chu kỳ giao dịch T+2.
- Ngôn ngữ thân thiện: Toàn bộ thuật ngữ định lượng (Sharpe, MDD, Sortino, Win Rate, T+2) đều được chú thích ngắn gọn, dễ hiểu ngay tại giao diện.

## Operating Context

- Môi trường: Web Dashboard trên trình duyệt máy tính và máy tính bảng (màn hình chuẩn 1280px+ và hỗ trợ responsive).
- Tần suất: Theo dõi biến động theo phiên giao dịch hàng ngày (mốc chốt phiên ATC 15:00 UTC+7).
- Dữ liệu: Nguồn dữ liệu nến SSI Fast Connect API và dữ liệu lịch sử VN30 được chuẩn hóa Parquet.

## Capabilities and Constraints

- Chức năng cốt lõi bắt buộc giữ nguyên 100%:
  - Xem danh mục VN30 và biểu đồ nến kỹ thuật (Lightweight Charts) với các khung thời gian và chỉ báo MA/EMA/RSI/MACD.
  - Tab Dự báo Xu hướng AI: Dự báo T+3 (Tăng / Giảm / Đi ngang), xác suất phân bổ Softmax, mức giá mục tiêu và lý do đề xuất.
  - Tab Kiểm thử Chiến lược (Backtest): Tự thiết lập quy tắc Mua (theo AI hoặc RSI/MA) và quy tắc Bán (Chốt lời, Cắt lỗ, Tín hiệu AI, Nắm giữ N phiên), chạy mô phỏng hiển thị đường cong tài sản (Equity Curve), bảng lệnh giao dịch và các chỉ số tài chính.
  - Quản lý chiến lược: Lưu và tải lại chiến lược đã lưu (SavedStrategiesManager).
- Ràng buộc:
  - Giữ nguyên toàn bộ logic nghiệp vụ, API endpoint và kiểu dữ liệu hiện hữu.
  - Thay đổi tập trung vào tầng giao diện thị giác: Flat Minimalist, đơn giản hóa, giải thích rõ ràng, tăng độ tương phản và loại bỏ hoàn toàn AI-slop.

## Brand Commitments

- Phong cách chủ đạo: **Flat Minimalist** (Tối giản phẳng).
  - Không gradient tím AI (`from-purple-400`), không bóng đổ lòe loẹt, không viền dày cộm.
  - Cấu trúc thẻ phẳng, padding thoáng đãng, phân cấp thị giác bằng kích thước chữ và độ đậm nhạt văn bản.
  - Bảng màu chuẩn mực tài chính Việt Nam: Xanh lá (Tăng điểm / Mua), Đỏ (Giảm điểm / Bán), Vàng (Tham chiếu / Giữ), nền trung tính Slate/Zinc cao cấp.
- Giọng văn: Chuẩn mực, điềm đạm, minh bạch, giải thích thuật ngữ bình dân hóa để người mới cũng hiểu được.

## Evidence on Hand

- Dữ liệu lịch sử 10 năm của nhóm cổ phiếu VN30 (Parquet).
- 209 unit tests đã pass 100% tại `apps/ml`, `apps/api`, và `apps/web`.
- Bộ chỉ báo kỹ thuật tài chính chuẩn TA-Lib: SMA, EMA, RSI, MACD, Bollinger Bands, ATR.

## Product Principles

1. **Công cụ phục vụ tác vụ (Task First):** Giao diện lùi về phía sau để số liệu tài chính và biểu đồ dẫn dắt. Không sử dụng hiệu ứng chuyển động rườm rà gây mất tập trung.
2. **Minh bạch và dễ hiểu:** Mỗi chỉ số tài chính hoặc kết quả AI đều có gợi ý tooltip/chú thích bình dân, không giả định người dùng đã là chuyên gia tài chính.
3. **Màu sắc mang tính ngữ nghĩa:** Màu sắc chỉ dùng để chỉ thị trạng thái (Tăng/Giảm/Lời/Lỗ/Cảnh báo), không dùng để trang trí bề mặt.
4. **Phẳng, thoáng và sắc nét:** Sử dụng các đường kẻ mảnh (hairline 1px), typography rõ ràng, chữ số định dạng tabular mono để người dùng dễ so sánh các bảng số liệu.

## Accessibility & Inclusion

- Độ tương phản văn bản đạt chuẩn WCAG AA: chữ trắng/xám sáng trên nền tối hoặc đen trên nền sáng, tuyệt đối không dùng chữ xám mờ trên nền màu (`gray-on-color`).
- Kích thước click/chạm tối thiểu 36x36px cho các nút bấm và ô chọn.
- Phông chữ hệ thống hoặc sans-serif sạch sẽ, hiển thị chữ số bảng (`font-mono` / `tabular-nums`) cho toàn bộ giá trị tiền tệ, phần trăm và điểm số.

