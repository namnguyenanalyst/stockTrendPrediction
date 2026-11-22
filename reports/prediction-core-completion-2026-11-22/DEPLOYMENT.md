# Triển khai runtime và worker

## Trạng thái

Image trước triển khai đã được giữ bằng tag `infra-vn_stock_api:rollback-core-20261122`:
`sha256:f613c708ec3d67a2dde23ec98fd17f7aedf947b8e2f62221badccde8d345e02e`.
Candidate `infra-vn_stock_api:core-runtime-172`:
`sha256:32701272565e7b4a4ed1972c80b35c03ac7c02e245b81c3aa5266193be33bfc2`.

Stack thực đang dùng project `stocktrendprediction` và Compose tại root. Không dùng project infra thứ hai vì container/volume đang phục vụ có sẵn.

## Điều kiện và triển khai

- Xác nhận INTERNAL_WORKER_SECRET đã cấu hình, không in giá trị trong log.
- UID/GID writer phải có quyền ghi thư mục data/models; máy hiện tại là501:20. Kiểm tra bằng entrypoint trên bản sao trước khi chạy thật. Không chown thư mục thật.
- Giữ bundle hiện đang phục vụ. Không chép model thử nghiệm trong reports/sandbox vào production.
- Sau khi kiểm chứng, chạy từ root với môi trường:

```sh
VN_STOCK_API_IMAGE=infra-vn_stock_api:core-runtime-172 ML_WRITER_UID=501 ML_WRITER_GID=20 docker compose -p stocktrendprediction --env-file .env up -d --no-build vn_stock_api vn_stock_training_api vn_stock_retrain_worker
```

- Kiểm tra health hai API, package1.7.2, worker URL trỏ training API, lịch Chủ Nhật02:00ICT, API VIC/HPG×hai model và giao diện đã đăng nhập.
- Worker khởi động ở ngoài cửa sổ lịch không huấn luyện ngay. Không ép chạy production để thay thế bằng bundle chưa đánh giá.
- Biến môi trường lựa chọn image/UID/GID phải được lưu cấu hình vận hành trước lần up tiếp theo, nếu không Compose trở về mặc định.

## Rollback

Dừng worker trước để tránh phát sinh publication mới:

```sh
docker compose -p stocktrendprediction --env-file .env stop vn_stock_retrain_worker vn_stock_training_api
VN_STOCK_API_IMAGE=infra-vn_stock_api:rollback-core-20261122 docker compose -p stocktrendprediction --env-file .env up -d --no-build --no-deps vn_stock_api
```

Image rollback không khôi phục file source bind-mount. Giữ nguyên thay đổi ứng dụng hiện hữu; nếu cần quay một sửa đổi source phải đối chiếu bản sao/diff cụ thể, không reset toàn bộ worktree. Artifact baseline được lưu ở serving-artifact-copy; không khôi phục nó đè model mới nếu chưa xác minh generation và lịch sử publication.

## Web đã triển khai

Image Web `infra-vn_stock_web:core-final-20261122` build từ worktree hiện tại với API public `http://localhost:8000`; `.env` lưu `VN_STOCK_WEB_IMAGE` để tái triển khai đúng image. Image Web cũ được giữ ở `infra-vn_stock_web:rollback-core-20261122`.

Rollback Web khi cần:

```sh
VN_STOCK_WEB_IMAGE=infra-vn_stock_web:rollback-core-20261122 docker compose -p stocktrendprediction --env-file .env up -d --no-build --no-deps vn_stock_web
```

Cập nhật cả biến lựa chọn image trong cấu hình vận hành nếu quyết định giữ rollback; lệnh override một lần không tự sửa `.env`.
