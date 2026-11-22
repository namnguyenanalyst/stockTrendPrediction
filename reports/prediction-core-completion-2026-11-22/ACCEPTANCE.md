# Đối chiếu mục tiêu còn lại

| Yêu cầu | Bằng chứng hiện có | Trạng thái |
|---|---|---|
| Worker thật → SSI → train → publish → API dùng generation mới | worker-integration.json (CORE), worker-vn30-integration.json (VN30), trace SSI và log worker | Đạt trong sandbox; writer/worker đã vận hành, lịch tuần chưa tới lần chạy kế tiếp |
| Lỗi SSI không tạo model thành công giả | worker-source-failure.json, exit1, hash12 model không đổi | Đạt trong sandbox |
| Artifact hỏng giữ nguyên bộ cache hoàn chỉnh, phục hồi được | artifact-fault-integration.json: cả hai model cùng generation/probabilities, degraded rồi healthy | Đạt trong sandbox |
| Tương thích scaler/model giữa hai runtime | compatibility-full-comparison.json, full-output.npz/json cho ba môi trường | Đạt trên tập mẫu đã chốt; không bảo đảm artifact bất kỳ |
| Thống nhất runtime phục vụ1.7.2 | pyproject/uv.lock, image core-runtime-172, offline Docker comparison | Đạt: deployed-runtime.json, cả hai API1.7.2 healthy |
| Training metadata tái lập runtime | runtime_versions trong train.py + test fitting thư mục tạm, provenance của ba fold | Đạt |
| Chất lượng ngoài mẫu, cùng mẫu/baseline, không tuning test | QUALITY.md, quality/summary.json, quality-protocol-check.json, quality-artifact-provenance.json | Đạt; accuracy chưa vượt baseline |
| Bảo toàn model đang phục vụ | baseline.json + serving-artifact-copy, production-artifact-check.json | Đạt sau triển khai: deployed-api-smoke.json,12hash không đổi |
| Worker có writer nội bộ với quyền ghi đúng | Hai Compose + training_api_entrypoint.py + test_training_writer.py; UID501 exec trong sandbox đạt | Đạt: writer-preflight-after-restart.json, deployed-runtime.json |
| Rollback trước triển khai | Tag rollback-core-20261122, DEPLOYMENT.md | Đã chuẩn bị; chưa cần thực hiện |
| UI đăng nhập VIC/HPG×hai model, ngày/giá/xác suất/trajectory/history | Quan sát UI localhost3002 + API Docker8003; ghi chi tiết STATUS.md | Đạt trên Web3000/API8000 trong phiên người dùng: final-authenticated-ui.json |
| UI lỗi và phục hồi |401 quan sát thật → reload phiên → status ngày/timestamp đúng; status.test.tsx | Đạt: lỗi/phục hồi trên sandbox, phiên thật và console trên bản cuối đã kiểm tra |
| Không sửa giá SSI theo suy đoán | Không thay giá nguồn; hạn chế công bố trên UI/QUALITY.md; tests cho phép biến động lớn | Giữ nguyên nguyên tắc |
| Tests/TypeScript/ESLint | API/worker/writer56pass; status/storage/a11y5pass; infra Docker21pass; tsc noEmit, ESLint liên quan đạt | Đạt cho các thay đổi đã kiểm tra; chạy lại khi phát sinh sửa |
| Không commit/push | Chỉ chỉnh worktree/report/image địa phương | Tuân thủ |

Nghiệm thu cuối đã hoàn tất trong phiên người dùng ngày22/11/2026: VIC/HPG×hai model, số liệu UI khớp API, ba mốc minh họa, toggle/6M, lịch sử qua reload/replay và console. Bằng chứng final-authenticated-ui.json. Các trường hợp gây lỗi vẫn thực hiện trên bản sao như yêu cầu; không gây lỗi production.

Giới hạn được bàn giao, không đánh dấu là lỗi đã khắc phục: lịch tuần production kế tiếp chưa diễn ra; chất lượng artifact legacy chưa được chứng nhận bằng test độc lập; kết quả ngoài mẫu là các lượt huấn luyện lịch sử; lịch sử giá điều chỉnh SSI không có căn cứ để tự sửa; screenshot được quan sát inline, không có file ảnh xuất riêng.
