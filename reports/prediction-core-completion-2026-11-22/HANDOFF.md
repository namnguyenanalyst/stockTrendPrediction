# Bàn giao ba mục tiêu trọng yếu — đã nghiệm thu

## Kết quả

1. **Huấn luyện tự động:** worker thật đã đi hết SSI → huấn luyện → công bố bundle → API đổi generation trong môi trường riêng, cả CORE5 mã và VN3030 mã. Sửa lỗi CORE bị mở rộng thành VN30. Thử lỗi SSI không thay artifact; thử artifact hỏng giữ generation cache hoàn chỉnh rồi phục hồi. Hiện writer API nội bộ và worker lịch Chủ Nhật02:00ICT đã hoạt động; chưa tới lần chạy lịch kế tiếp trên production và không ép retrain production.
2. **Runtime:** đã đo thực nghiệm sklearn1.7.2/1.9.1 trên cùng bản sao scaler/model.30.450 hàng scaler/LightGBM,30 cửa sổ LSTM; không đổi nhãn trong mẫu, sai khác xác suất chỉ mức số học. Khóa1.7.2 trong hai lockfile và shared package; hai API đang phục vụ đúng1.7.2. Kết quả này không chứng minh tương thích cho mọi artifact. Metadata các lượt huấn luyện mới ghi runtime_versions.
3. **Chất lượng:** ba fold ngoài mẫu, cùng1.800 quan sát/model và cùng baseline; không tuning test. Accuracy LightGBM47,50%, LSTM44,83%, baseline58,39%; macro-F1 tương ứng0,3995/0,3656/0,2458. Chưa đủ căn cứ nói model tốt hơn tổng thể hoặc tạo lợi nhuận. Xem QUALITY.md về tập dữ liệu, hash và giới hạn.

## Bảo toàn và vận hành

- 12artifact gốc không đổi hash; không promote model huấn luyện thử. Không sửa/loại giá SSI theo biên độ suy đoán.
- Inference mount data/models chỉ đọc. Writer dùng cùng image, UID501:20 của máy hiện tại, mount ghi, không publish port; secret chỉ truyền runtime.
- Image API/Web và lựa chọn UID/GID đã lưu trong `.env` địa phương (không commit). `.env.example` chỉ chứa hướng dẫn/giá trị mẫu.
- Rollback image API/Web và source snapshot đã chuẩn bị; DEPLOYMENT.md nêu lệnh và giới hạn rollback source bind mount.
- Git HEAD vẫn8127d31d102a30949db5e5fb5d95035e2d11c828; không commit/push, không reset các thay đổi có trước.

## Kiểm chứng và giới hạn

- API Docker đang phục vụ: VIC/HPG×LightGBM/LSTM, ngày dữ liệu, xác suất, generation, trajectory3 đều kiểm tra thành công; hai API healthy.
- UI đăng nhập bản sao: chọn/đổi mã và hai model, ngày/giá, lịch sử, đường minh họa nhìn thấy trên chart; lỗi ngắt API không tạo dự báo/lịch sử giả, nút thử lại phục hồi. Phiên hết hạn được báo rõ, reload khôi phục.
- Web Docker3000/API8000 đã nghiệm thu trong phiên người dùng: VIC/HPG×hai model, ngày/giá/xác suất khớp API; trajectory/toggle/khung thời gian; lịch sử4bản ghi giữ nguyên sau reload và replay đúng HPG/LSTM; console không lỗi/cảnh báo. Bằng chứng final-authenticated-ui.json. Không thay user/database hoặc tạo phiên giả.
- 27test Docker/config/runtime/writer;56test API/services/worker/writer;5test frontend trạng thái/storage/a11y đã đạt theo các lượt liên quan. Có phần chồng lặp giữa các nhóm, không cộng thành tổng test độc lập. TypeScript noEmit, ESLint hai file trạng thái, git diff --check đạt.

## Lệnh kiểm tra liên quan

Từ root:

```sh
uv run --project apps/api pytest apps/api/tests/test_prediction_audit.py apps/api/tests/test_services.py infra/tests/test_training_writer.py infra/tests/test_retrain_worker.py -q
uv run --project apps/api pytest infra/tests/test_training_writer.py infra/tests/test_ml_runtime_contract.py infra/tests/test_docker_ssi_runtime.py infra/tests/test_docker_deployment.py infra/tests/test_docker_adversarial.py -q
uv run --project apps/ml pytest apps/ml/tests/test_modeling.py -k test_train_production_model -q
```

Từ apps/web:

```sh
npx vitest run src/components/tabs/AIPredictionTab.status.test.tsx src/components/tabs/AIPredictionTab.storage.test.tsx src/components/tabs/AIPredictionTab.accessibility.test.tsx
npx tsc --noEmit
npx eslint src/components/tabs/AIPredictionTab.tsx src/components/tabs/AIPredictionTab.status.test.tsx
```

Không cần chạy lại các lượt training để đọc kết quả. QUALITY.md và các JSON lưu đủ số liệu; STATUS.md là nhật ký chi tiết. ACCEPTANCE.md theo dõi nghiệm thu; handoff-integrity-check.json kiểm hash cả18artifact của3fold,12artifact production và image/service hiện tại.
