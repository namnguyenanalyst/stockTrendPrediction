# Phase 5 — Nghiệm thu tích hợp, Docker và hiệu năng

Ngày thực hiện: 14/11/2026. Đây là đợt cải thiện thứ 5 sau các đợt rà soát ML, dữ liệu, API và frontend; không phải một lần huấn luyện mô hình mới.

## Kết quả chính

656 kiểm thử duy nhất đạt: ML 138, API 216, Web 178, hạ tầng 37, E2E chạy HTTP thật trên Docker 87. Bộ E2E tham chiếu cũng đạt 87 nhưng không cộng thêm vào tổng. TypeScript và Docker build frontend đạt. Ruff F401/F841 cho các tệp Python bổ sung/chỉnh sửa trọng tâm và git diff --check đạt. Đây không phải tuyên bố toàn bộ quy tắc lint của kho mã đều đạt.

Các log nghiệm thu cùng thư mục ghi lại ML, API, hạ tầng và E2E. Web: 12 tệp, 178 kiểm thử đạt; có thêm 2 kiểm thử chặn thao tác ghi trùng và phục hồi sau lỗi. Số 569 trong báo cáo V1 là mốc cũ; không thay bằng 656 trong Word nếu chưa cập nhật phạm vi, ngày và bảng phân loại tương ứng.

## Lỗi phát hiện và cách xử lý

1. E2E có thể âm thầm dùng mock khi đích thật không truy cập được. Khi chỉ định đích rõ ràng, runner hiện thất bại ngay; không chấp nhận đồng thời đích thật và force-mock.
2. Lần chạy thật đầu tiên có 77 đạt, 10 lỗi. Một phần do kiểm thử còn gọi endpoint dự báo không tồn tại và đọc cấu trúc kết quả tài chính cũ; phần khác do API chấp nhận vốn không hợp lệ và bỏ qua trường ngày không được hỗ trợ. Đã cập nhật kiểm thử theo API đang cung cấp và siết dữ liệu đầu vào: vốn hữu hạn, dương; tỷ lệ phí/thuế/trượt giá trong [0,1); yêu cầu backtest đơn giản không nhận trường thừa. Dải ngày dùng endpoint advanced. Không biến bài kiểm thử cấu hình phí thành bằng chứng khấu trừ phí; logic khấu trừ được kiểm tra ở engine.
3. Hộp thoại lưu trước đây đóng khi máy chủ chưa xác nhận thành công. Hiện chờ kết quả, chặn bấm ghi trùng, giữ tên và báo lỗi khi mất kết nối. Xóa dùng hộp thoại HTML, mặc định tập trung vào Hủy, Escape hủy, chỉ cập nhật danh sách sau khi máy chủ xác nhận.
4. Sửa tỷ lệ mặc định hiển thị 1500% thành 15% khi cấu hình cũ thiếu bộ lọc bán; điều chỉnh số cột/thanh công cụ để thẻ chiến lược đủ chỗ trên màn hình vừa.
5. /health chỉ thể hiện tiến trình sống. Thêm /ready kiểm tra truy cập bảng refresh_sessions với giới hạn chờ. Thử dừng PostgreSQL thật phát hiện lỗi DNS/socket trả 500; đã xử lý thành 503. Trên image cuối: /health=200, /ready=503 khi DB dừng, phục hồi khỏe sau khi DB khởi động lại. Readiness này không chứng nhận mọi bảng, chất lượng dữ liệu hay độ chính xác mô hình.
6. Docker API trước đây giải quyết dependency trôi phiên bản. Hiện cài bằng uv sync --frozen --no-dev; torch CPU dùng index explicit theo nền tảng. Web dùng Node 22, npm ci có lockfile; bỏ fallback npm install. API và Web chạy bằng người dùng không phải root. Chưa ghim digest base image, phiên bản uv bootstrap hoặc gói apt; không tuyên bố build tái lập từng byte.

## Môi trường và kiểm thử qua trình duyệt

Compose riêng infra/docker-compose.acceptance.yml: PostgreSQL riêng không mở cổng host, API 127.0.0.1:8105, Web 127.0.0.1:3105. Hostname stocktrend-acceptance.localhost tách cookie khỏi ứng dụng localhost khác. Bí mật sinh ngẫu nhiên trong tệp riêng ngoài repository; không sửa .env của người dùng. Dữ liệu và artifact mô hình chỉ gắn đọc; tắt tự đồng bộ và không chạy worker huấn luyện trong môi trường này.

Đã thao tác qua trình duyệt với tài khoản thử nghiệm trong DB riêng:

- Chạy backtest, lưu lịch sử và cấu hình Draft; khi dừng API, hộp thoại lưu giữ nguyên tên và hiển thị lỗi. Sau phục hồi có thể lưu lại.
- Ghi đè cùng tên giữ nguyên ID và chỉ có một bản ghi; chuyển Active, tải lại trang vẫn Active; chuyển Draft vẫn tồn tại sau tải lại.
- Bản ghi tồn tại sau khi khởi động lại API và DB.
- Escape hủy xóa giữ bản ghi; xác nhận xóa thành công và API xác nhận danh sách rỗng.
- Kiểm tra bố cục ở độ rộng 768 và 1280; chỉ là kiểm tra có giới hạn, không phải chứng nhận toàn bộ thiết bị hay toàn bộ accessibility.

Chi tiết ở phase5_browser_checks.json. Cấu hình “Minh chứng lưu cấu hình” trong ảnh cuối chỉ là fixture chụp giao diện, chưa có kết quả tài chính; không dùng làm chứng cứ lợi nhuận. Dữ liệu tài khoản, session và fixture thử nghiệm được xóa cùng volume riêng khi dọn môi trường.

## Hiệu năng HTTP trên image cuối

Máy khách macOS ARM; Docker 8 CPU, khoảng 12.5 GB RAM. Đo sau warm-up, không chạy đồng thời bộ E2E. 106 quan sát HTTP, không có yêu cầu lỗi; 4 yêu cầu warm-up không tính. Dữ liệu thô và thời điểm ở apps/api/reports/phase5_http_benchmark.json; kịch bản ở scripts/phase5_benchmark.py.

| Kịch bản | Số yêu cầu | Trung vị (ms) | p95 nearest-rank (ms) |
|---|---:|---:|---:|
| health_serial | 30 | 1.89 | 2.32 |
| readiness_serial | 30 | 3.17 | 4.28 |
| history_250_bars | 10 | 19.97 | 21.32 |
| prediction_serial | 5 | 27.91 | 34.28 |
| health_concurrent_with_prediction | 30 | 10.13 | 16.39 |
| prediction_during_health_burst | 1 | 62.46 | 62.46 |

Prediction serial là LightGBM cho HPG. Với N=5, p95 nearest-rank bằng giá trị lớn nhất; với N=1 không suy luận phân phối. Đây là phép đo cục bộ sau warm-up, không phải SLA, khả năng chịu tải sản xuất hoặc bằng chứng Canvas đạt 60 fps.

## Mô hình và giới hạn kết luận

Cả LightGBM và LSTM trả HTTP 200, ba xác suất hữu hạn trong [0,1], tổng bằng 1, data_as_of_date=2026-11-13. Đây là smoke test suy luận, không đo lại Accuracy/Macro F1 và không chứng minh lợi nhuận. Không huấn luyện hay ghi đè bốn artifact sản xuất.

Image API cuối dùng Python 3.11, torch 2.14.1+cpu, pandas 2.3.3, scikit-learn 1.9.1. Môi trường nghiên cứu/host có nhánh Python 3.10 và scikit-learn 1.7.2; không tuyên bố tương đương số học hoặc tương thích pickle cho mọi nền tảng. Image ID, thư viện và mount thực tế ở phase5_runtime.json.

Các hạn chế dữ liệu đã ghi ở phase 2 (corporate actions, survivorship và tính dừng từng đặc trưng) vẫn còn. Không suy diễn các thử nghiệm chẩn đoán thành kết quả cuối của đồ án. Phí, thuế và quy tắc thanh toán ở đợt này được kiểm tra theo cấu hình dự án, không thực hiện xác minh pháp lý mới.

## Tái chạy nghiệm thu

Build trực tiếp từ thư mục gốc để tránh lỗi quyền đọc đường dẫn Unicode của Compose Bake trên máy này:

docker build -t stocktrend-phase5-api:local -f apps/api/Dockerfile .

docker build -t stocktrend-phase5-web:local --build-arg NEXT_PUBLIC_API_URL=http://stocktrend-acceptance.localhost:8105 apps/web

Tạo tệp env riêng, quyền 600, có ACCEPTANCE_DB_PASSWORD và ACCEPTANCE_JWT_SECRET ngẫu nhiên, không dùng .env sản xuất. Sau đó chạy Compose với --env-file, -f infra/docker-compose.acceptance.yml và up -d --no-build --wait. Chạy tests/e2e/run_e2e.py --help để chọn đích http://127.0.0.1:8105; đích rõ ràng không được fallback sang mock. Kịch bản benchmark phải chạy khi E2E đã kết thúc. Dọn bằng down -v chỉ trên Compose nghiệm thu này.

Không dừng/rebuild hệ thống gốc ở cổng 8000/5432 và worker của người dùng. Các thay đổi hiện nằm trong working tree, chưa commit/push và chưa thay phiên bản triển khai gốc. Không sửa tệp Word. Bước tiếp theo là phase 6: đồng bộ minh chứng, số liệu và kế hoạch tinh gọn báo cáo trước khi chỉnh Word theo phạm vi đã duyệt.

## Tài liệu kỹ thuật chính thức đã đối chiếu

- Docker startup order: https://docs.docker.com/compose/how-tos/startup-order/
- uv PyTorch integration và explicit index: https://docs.astral.sh/uv/guides/integration/pytorch/
- Next.js standalone output: https://nextjs.org/docs/app/api-reference/config/next-config-js/output
