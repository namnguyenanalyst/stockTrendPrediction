# Cập nhật và kiểm tra sau triển khai

Thực hiện từ root repository. Không dùng `down -v`, `git reset --hard` hoặc tự ghi đè artifact để thử nghiệm. Worktree chứa cả thay đổi có sẵn của người dùng; baseline.json ghi nhận chúng nhưng không phải bản sao đầy đủ source ban đầu.

## Cập nhật

1. Ghi lại image hiện phục vụ và lưu tag dự phòng:

```sh
docker inspect vn_stock_api --format '{{.Image}}'
docker image tag infra-vn_stock_api:latest infra-vn_stock_api:before-update
```

2. Chạy pytest API, ML, infra bằng đúng interpreter ghi trong README; chạy Vitest, TypeScript và ESLint. Không chạy retrain để kiểm thử deploy.

3. ML nằm trong image, nên cập nhật ML phải build lại. API app và alembic đang bind-mount read-only; sửa chúng cần restart process để import lại. Read-only mount ở container không khóa file host trước thay đổi.

```sh
docker build -t infra-vn_stock_api:latest -f apps/api/Dockerfile .
docker compose up -d --no-build --no-deps vn_stock_api
docker compose ps
curl --fail http://localhost:8000/health
python scripts/audit/prediction_live.py
PYTHONPATH=apps/ml apps/ml/.venv/bin/python scripts/audit/prediction_operations.py --output reports/prediction-audit-2026-11-20/operations-current.json
```

4. Kiểm tra generation/date/price/trajectory và HTTP errors trong report, không chỉ /health. Đăng nhập giao diện, chọn VIC/HPG và hai model, đối chiếu chart và bảng T+3, kiểm tra console. Worker vắng mặt phải được báo riêng; không coi API healthy là worker đang chạy.

5. Frontend đang chạy dev cần đúng source worktree; bản sao /tmp chỉ phục vụ E2E và không phải deployment chính. Bản production cần build Next.js với API URL đúng môi trường trước recreate service web theo cấu hình của nơi triển khai.

## Quay lại image trước

Tag dự phòng đã xác minh trong đợt audit: `infra-vn_stock_api:audit-before-remaining`, image `sha256:edde1ea06e1833f04cc9067d4f0db8600b6b8521892f92eb734623a4db733124`. Đây là bản giữa đợt audit, không phải toàn bộ trạng thái trước ngày 20/11.

Các lệnh dưới là hướng dẫn phục hồi, chưa thực hiện rollback:

```sh
docker image tag infra-vn_stock_api:latest infra-vn_stock_api:before-rollback
docker image tag infra-vn_stock_api:audit-before-remaining infra-vn_stock_api:latest
docker compose up -d --no-build --no-deps vn_stock_api
```

Rollback image chỉ đổi code được đóng gói; không hoàn tác source API bind-mount, frontend hay dữ liệu. Muốn hoàn tác đầy đủ phải dùng snapshot source đã biết và chỉ đảo các thay đổi được review là thuộc audit; không restore hàng loạt file đang có thay đổi của người dùng. Không có snapshot source ban đầu đầy đủ thì không tuyên bố có thể rollback tự động toàn bộ worktree.

Sáu artifact production vẫn khớp SHA256 baseline; các fold huấn luyện thử lưu riêng trong reports. Nếu cần đổi artifact ở môi trường khác, phải phục hồi nguyên bundle model/scaler/metadata cùng generation và kiểm chứng hash; không trộn từng file.

## Sự cố đã gặp

Docker kẹt container `created`, PID 0, không chạy tới entrypoint sau recreate. Docker Desktop restart đã phục hồi; sau đó start API và kiểm chứng healthy + 60/60 dự báo. Không xóa database volume. Các lời gọi smoke thất bại lúc Docker chưa sẵn sàng được lưu, không tính là kết quả chức năng mô hình.


## Image sửa trọng tâm 22/11/2026

Image phục vụ mới: `sha256:0833dbcb249f0c4dd8c8c79edf867bea5767324573e0b4a813dc5c775a3fde83`. Giữ data/models read-only; không bật worker để thử retrain trên dữ liệu chưa xác thực. Guard có thể trả 503 cho lịch sử cần đối chiếu (hiện TCB), đây không phải lỗi cần né bằng cách hạ ngưỡng hoặc fallback dự báo.

Khi retrain trong môi trường ghi được, `artifact_publication.artifact_generation` cho biết generation đã commit. `compatibility_export_failures` không rỗng có nghĩa bundle đã công bố nhưng một số bản sao legacy chưa xuất được; xử lý cảnh báo xuất bản sao, không báo model chưa đổi hoặc tự chạy lại huấn luyện vì lỗi đó. Người đọc model/scaler phải dùng manifest cùng generation. Các loose legacy file không có tính nguyên tử theo nhóm.


### Kiểm thử riêng lỗi ngày chốt / đồng bộ

Từ root: `uv run --project apps/ml pytest apps/ml/tests/test_data_refresh_provenance.py apps/ml/tests/test_data_ingestion.py apps/ml/tests/test_modeling.py apps/ml/tests/test_price_history_quality.py -q`.

Ngày chốt của panel nay được lấy mỗi lần gọi, cùng mốc cho các constituent. Retrain từ chối khi đồng bộ trả partial/errors hoặc ném exception; không xem lỗi sync/panel publish là huấn luyện thành công. Điều này không tự khắc phục dữ liệu điều chỉnh lịch sử hoặc quyền ghi ở mount read-only.


### SSI là nguồn duy nhất (ràng buộc người dùng)

Không yêu cầu người vận hành cung cấp nhà cung cấp giá thứ hai hoặc lịch chia cổ phiếu thủ công. SSI FC-Data hiện có DailyOhlc/DailyStockPrice (ClosePriceAdjusted), nhưng tài liệu API được kiểm tra không liệt kê endpoint lịch corporate action. Không tự suy hệ số điều chỉnh từ bước nhảy giá hoặc RefPrice đã phát hiện không phản ánh sự kiện.

Strict Live refresh phải chạy kiểm tra chất lượng trước khi ghi raw cache; khi bị từ chối, giữ dữ liệu hiện tại và trả lỗi dữ liệu có mã/ngày. Không coi cache đang có là đã được chứng nhận chỉ vì được giữ lại. Nguồn cập nhật chỉ là SSI; việc vượt kiểm tra kỹ thuật không thay thế đánh giá chất lượng mô hình.


### Live với data/models chỉ đọc

Cả root và infra Compose nay truyền SSI_CONSUMER_ID, SSI_CONSUMER_SECRET và SSI_API_URL từ môi trường; secret không được đưa vào build args/image. Không xuất `docker compose config` hoặc `docker inspect` toàn bộ environment vào báo cáo. Kiểm tra cấu hình chỉ xuất boolean có/không.

Live đọc SSI vào snapshot trong bộ nhớ, không cần mount data/models writable. `is_live_synced` không bảo đảm cache đã được ghi. Nếu cần ghi thị trường/retrain, đó là tác vụ riêng cần dữ liệu phù hợp và môi trường ghi được; không đổi mount để vượt guard chất lượng dữ liệu.

Lệnh test riêng: `uv run --project apps/ml pytest apps/ml/tests/test_live_prediction_snapshot.py -q`; `apps/api/.venv/bin/python -m pytest apps/api/tests/test_prediction_audit.py -q`; `PYTHONPATH=apps/api apps/api/.venv/bin/python -m pytest infra/tests/test_docker_ssi_runtime.py -q`.


### Chính sách mới: hoàn tác can thiệp theo biên độ giá

Theo yêu cầu người dùng, đã bỏ cơ chế chặn suy luận/huấn luyện/refresh dựa trên bước nhảy 20% và các 503 riêng cho lịch sử chưa xác minh. Các đoạn ghi guard/chặn trong báo cáo trước đây chỉ còn giá trị truy vết, không mô tả chính sách đang phục vụ. Không áp hệ số sửa giá dựa trên suy đoán corporate action. Dữ liệu SSI là đầu vào duy nhất; hạn chế điều chỉnh được công bố, không tự coi mọi bước nhảy là lỗi. Các kiểm tra cấu trúc, ngày/đơn vị, NaN/Infinity, lỗi mạng và tính đúng của luồng phần mềm vẫn được giữ.
