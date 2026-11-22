# Chất lượng dự báo ngoài mẫu — snapshot SSI cố định

Đây là đánh giá các mô hình được huấn luyện lịch sử trong môi trường riêng, không phải test độc lập cho artifact legacy đang phục vụ. SSI là nguồn duy nhất; không tự điều chỉnh hoặc chặn giá theo biên độ. Hạn chế lịch sử giá điều chỉnh được chấp nhận và công bố.

Source HEAD lúc bắt đầu: `8127d31d102a30949db5e5fb5d95035e2d11c828` (worktree có thay đổi đã ghi tại baseline.json). Snapshot SHA256: `47eb774e563b5d4fdb9a72f28ad7f3d453bb1aede349437a7d9e7144ccd932a8`.

Ba fold tích lũy lịch sử, validation buffer 40 phiên, purge T+3, seed42, tối đa40 epoch với early stopping trên validation; không tuning trên test. Mỗi fold20 ngày ×30 mã; 1.800 mẫu cho mỗi mô hình. Các cặp mã/ngày không trùng giữa fold, nhưng nhãn T+3 vẫn chồng lấn giữa các ngày liền kề.

| Mô hình | Accuracy | Macro-F1 | Log loss | Brier đa lớp |
|---|---:|---:|---:|---:|
| LightGBM | 47.50% | 0.3995 | 1.0779 | 0.6512 |
| LSTM | 44.83% | 0.3656 | 1.0728 | 0.6454 |
| Baseline prior train / lớp phổ biến | 58.39% | 0.2458 | 0.9724 | 0.5746 |

Baseline lấy phân phối lớp từ train của từng fold và chọn lớp có xác suất lớn nhất. Dùng cùng quan sát mã/ngày với hai model. Accuracy hai model thấp hơn baseline; macro-F1 cao hơn baseline. Không suy ra mô hình tốt hơn trên mọi tiêu chí hoặc có lợi nhuận đầu tư.

Chi tiết precision/recall/F1 từng lớp, từng mã/fold, ROC-AUC, calibration và CI bootstrap theo ngày nằm tại quality/summary.json. Bootstrap theo ngày chưa xử lý đầy đủ phụ thuộc nhãn T+3. Vũ trụ là danh sách mã hiện tại, có survivor bias; chưa chứng nhận dữ liệu point-in-time hoặc đánh giá chiến lược/phí giao dịch.

## Phiên bản từng fold

- fold-1: 2026-08-19 → 2026-09-18; manifest SHA256 `34e2e88b1771b19c9cdbec121c57ef5ec4009e2b8201ffdd357cdc507a888590`. Metadata runtime và hash từng artifact trong quality-artifact-provenance.json.
- fold-2: 2026-09-21 → 2026-10-16; manifest SHA256 `980d393f469cce67314cf9ab2e81f7d15bfbf7c5b53c7fe266d66e76c59ea69d`. Metadata runtime và hash từng artifact trong quality-artifact-provenance.json.
- fold-3: 2026-10-19 → 2026-11-13; manifest SHA256 `a544fb4807088e83a64d13940c41fb10b1f261e2bc12716dd2f10d8696ca8571`. Metadata runtime và hash từng artifact trong quality-artifact-provenance.json.
