# Nguồn chính thức được đối chiếu ngày 21/11/2026

[1] HOSE, “Thông báo lịch nghỉ giao dịch năm 2026”, 29/04/2026. https://www.hsx.vn/vi/tin-tuc/hose-thong-bao-lich-nghi-giao-dich-nam-2026/2437411

Lịch gồm 01–02/01, 16–20/02, 27/04, 30/04–01/05, 31/08–02/09. Ngày làm bù thứ Bảy 10/01 và 22/08 không tổ chức giao dịch.

[2] HOSE, “Cập nhật lịch nghỉ giao dịch Tết Dương lịch 2026”, 25/12/2025. https://staticfile.hsx.vn/Uploads/UploadDocuments/2426350/20251225_Thong%20bao%20%20ve%20%20viec%20cap%20nhat%20lich%20nghi%20giao%20dich%20Tet%20Duong%20lich%202026%20toan%20thi%20truong.pdf

[3] SSI, “FC API — GetDailyStockPrice”. https://fc-data.ssi.com.vn/Help/Api/POST-api-Market-GetDailyStockPrice

Response có trường ClosePriceAdjusted. Đây là bằng chứng API có khái niệm giá điều chỉnh; không chứng minh file parquet hiện có đã được điều chỉnh.

[4] SSI, “FastConnect Data API Specs”. https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs

DailyOhlc và DailyStockPrice là hai endpoint khác nhau. Hệ thống hiện lấy OHLCV; cần lưu provenance hoặc so sánh ClosePriceAdjusted trước khi tuyên bố dữ liệu đã xử lý cổ tức/chia tách.

Giới hạn: các nguồn trên xác minh lịch năm 2026 và mô tả API. Chưa xác minh riêng sự kiện doanh nghiệp cho toàn bộ 30 mã và mọi ngày lịch sử, không suy diễn không có corporate action chỉ vì OHLC hợp lệ.
