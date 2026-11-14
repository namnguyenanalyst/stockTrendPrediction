# Phase 4 — Giao diện và cách trình bày kết quả

Thực hiện ngày 14/11/2026, theo đợt 4 trong kế hoạch sáu đợt hoàn thiện dự án.

## Các vấn đề đã sửa

### 1. Xác suất và thông tin mô hình

- Thay “độ tin cậy” bằng “xác suất lớp cao nhất”. Ghi rõ xác suất chưa được hiệu chỉnh và không phải tỷ lệ dự báo đúng đã kiểm chứng.
- Bỏ tuyên bố “Đã kiểm định OOS Thực chiến” tại phần kết quả, thay bằng trạng thái kết quả nghiên cứu chưa xác nhận hiệu quả đầu tư.
- Viết lại mô tả LightGBM/LSTM theo đầu vào và mục tiêu T+3. Bỏ các khẳng định chưa có bằng chứng rằng LightGBM phù hợp riêng với thị trường đi ngang hoặc LSTM tốt hơn khi có sóng lớn.
- Không dùng hiệu ứng nhấp nháy để ngụ ý hệ thống huấn luyện tự trị đang hoạt động khi chỉ đang đọc metadata. Hiển thị phiên chốt và thời điểm cập nhật mô hình.

### 2. Quỹ đạo và đơn vị giá

- Đường giá hiện do quy tắc giao diện quy đổi xu hướng/xác suất thành mức biến động; không phải đầu ra của mô hình hồi quy giá. Đổi nhãn thành “kịch bản minh họa”, “giá minh họa T+3”, kèm giải thích trực tiếp.
- Không tạo đường minh họa khi thiếu dự báo/trajectory, sai mã, sai mô hình hoặc ngày dữ liệu dự báo không trùng ngày nến cuối.
- Sửa đơn vị tại giá minh họa và các mốc: giá đầu vào nghìn đồng được nhân 1.000 trước khi ghi VNĐ. Trục biểu đồ tiếp tục dùng nghìn VNĐ và được chú thích.
- Bỏ cách gán mốc T+1/T+2/T+3 trên đường minh họa thành thời điểm mở vị thế/lưu ký/được bán. Những mốc minh họa này không phải lịch thanh toán của một giao dịch thực tế.
- Ghi rõ ngày tương lai chưa đối chiếu lịch nghỉ lễ. Quy tắc giá minh họa vẫn được giữ để tương thích sản phẩm; đợt này không biến nó thành dự báo giá đã kiểm định.

### 3. Tránh hiển thị dữ liệu cũ hoặc kết quả giả khi tải lỗi

- Khi đổi mã/mô hình, xóa dữ liệu chi tiết cũ trước khi tải dữ liệu mới.
- Dự báo được chọn phải khớp mã và model; kiểm tra ba xác suất hữu hạn, nằm trong 0–1 và tổng gần một.
- Xóa nến fallback cũ trước khi tải mã mới. Thiếu dự báo hiển thị trạng thái chưa có kết quả hợp lệ thay vì mặc định thành tín hiệu đi ngang; xác suất chưa có hiện dấu gạch.
- Bổ sung chú thích trên trang thị trường rằng một số chỉ số tổng quan/dòng tiền/dữ liệu cơ bản còn là ước lượng hoặc dự phòng. Chưa thay các nguồn dữ liệu đó bằng nguồn đã xác minh và chưa gắn provenance riêng cho từng ô dữ liệu.

### 4. Chiến lược lưu theo tài khoản

- Ghi đè dùng PUT giữ nguyên bản ghi, thay luồng xóa rồi tạo lại vốn có thể làm mất bản cũ và sai ID.
- Khi tạo mới, sử dụng ID server trả về cho danh sách và chiến lược đang chọn; tránh dùng ID local để sửa/xóa bản ghi CSDL.
- Active/Draft được cập nhật lên tài khoản; nếu server từ chối thì giữ trạng thái cũ và thông báo chưa lưu được.
- Xóa chờ server xác nhận trước khi bỏ bản local; không báo thành công khi server thất bại.
- Lưu thành công chỉ được thông báo sau xác nhận của server. Nếu lỗi, khôi phục cache theo danh sách cũ và cho phép thử lại.
- Tải tiếp các trang preset sau 100 bản ghi. Không dùng cache chung để khởi tạo danh sách khi đã đăng nhập; xóa danh sách cũ khi tải dữ liệu cho tài khoản hiện tại và báo lỗi nếu không tải được.
- Thông báo lỗi có biểu tượng cảnh báo và aria-live. Các thao tác lưu/toggle chưa có khóa chống nhiều lần nhấn đồng thời hoặc optimistic concurrency giữa nhiều thiết bị; cần kiểm tra thêm khi nghiệm thu tải và tích hợp.

### 5. Bố cục

Rút ngắn tiêu đề trang dự báo và chuyển hàng tiêu đề/model selector sang bố cục dọc ở khung hẹp, tránh ép tiêu đề thành nhiều dòng ngắn. Giữ nhận diện giao diện hiện có; không thay toàn bộ dashboard.

## Kiểm chứng

- 176 test web đạt, gồm tám test mới: sáu test về khớp dự báo/xác suất/đơn vị và hai test về PUT preset/phân trang.
- TypeScript noEmit, noUnusedLocals/noUnusedParameters và Next.js production build đạt. git diff --check đạt.
- Đã đăng nhập bằng tài khoản thử cục bộ và quan sát trang thị trường, trang dự báo có dữ liệu thật từ API, trang quản lý chiến lược và phòng cấu hình.
- Đã quan sát ảnh giao diện dự báo ở viewport desktop 1280 × 900 và khung trình duyệt mặc định; không tuyên bố đã kiểm thử đầy đủ mobile hoặc đạt chuẩn accessibility toàn bộ.
- Ảnh bản cuối: /Users/huongnguyen/.codex/visualizations/2026/11/14/01a1d966-10e9-77a0-af73-7a5da9b71d21/phase4-desktop.jpg
- Luồng PUT/phân trang được kiểm tra ở API client; chưa hoàn tất bài kiểm tra trình duyệt xuyên suốt tạo → ghi đè → tải lại → toggle → xóa trong đợt này. Đây là kịch bản cần nghiệm thu ở Phase 5, không gọi hai unit test client là E2E.
- Tài khoản thử và phiên thử đã được xóa; server xem thử cổng 3000 do đợt này khởi chạy đã dừng. Không dừng backend đang có của người dùng.

Chỉ chạy lại bộ web trong đợt này; không cộng các kết quả cũ để tuyên bố đã chạy lại toàn bộ hệ thống. Không huấn luyện lại, không thay model/scaler production, dữ liệu giá gốc hoặc Word. Các giới hạn về quyền cổ đông và thực nghiệm Phase 2 vẫn còn nguyên.

## Tiếp theo: Phase 5

Nghiệm thu tích hợp trình duyệt/API/PostgreSQL, thao tác chiến lược xuyên suốt, cách hiển thị lỗi mạng, chuyển tài khoản, nhiều thao tác đồng thời, Docker và đo hiệu năng thực tế. Kiểm tra thêm lịch nghỉ lễ, nguồn dữ liệu từng trường và responsive/a11y trước khi mô tả hệ thống đã hoàn thiện toàn diện trong đồ án.
