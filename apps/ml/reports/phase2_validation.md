# Phase 2 — Kiểm tra dữ liệu, thực nghiệm theo thời gian và dọn code không dùng

Ngày thực hiện: 14/11/2026. Báo cáo này phân biệt thay đổi của Phase 2 với các bản sửa liêm chính mô hình/kiểm thử ở phase1_integrity.md.

## Kết luận về phạm vi

Đã bổ sung bộ kiểm tra dữ liệu, bộ chạy thực nghiệm riêng với bốn cửa sổ thời gian và đối chứng tài chính, sửa cách mô phỏng Monte Carlo, dọn các component/biến không dùng đã xác minh và chạy kiểm thử hồi quy. Kết quả thực nghiệm mang trạng thái diagnostic_unverified_price_adjustments. Chưa đủ điều kiện công bố hiệu quả đầu tư cuối cùng vì lịch sử quyền cổ đông và điều chỉnh giá chưa được xác minh đầy đủ.

Không thay trọng số/scaler production, không đổi bộ 13 đặc trưng, không sửa bản Word. Các artifact nghiên cứu được lưu tách khỏi thư mục model production.

## 1. Dữ liệu thực tế và giới hạn

Snapshot gồm 36.330 bản ghi OHLCV, 30 mã, 1.211 phiên từ 04/01/2022 đến 13/11/2026. Đây là dữ liệu thô gồm cả lịch sử khởi động chỉ báo; không đồng nghĩa có 36.330 mẫu Train. Phạm vi nghiên cứu hiện cấu hình bắt đầu 03/04/2023.

- Không phát hiện khóa Date/Symbol trùng, OHLCV thiếu/không hữu hạn, giá không dương, khối lượng âm, nến sai biên hoặc bản ghi cuối tuần.
- Không phát hiện thiếu ngày so với các phiên có trong dữ liệu VNINDEX. Đối chiếu này không thay lịch giao dịch chính thức của sở.
- VNINDEX_Return_1d thiếu 30 giá trị ở phiên đầu của mỗi mã; không tự điền giá trị tương lai. Các phiên này nằm trong vùng khởi động bị loại trước khi huấn luyện.
- Có 21 biến động đóng cửa vượt 15% trong toàn bộ lịch sử thô; đây là danh sách cần xác minh, không tự suy ra hệ số chia tách.
- TCB ngày 29/10/2026 giảm khoảng 33,28%. Thông báo HOSE xác nhận ngày giao dịch không hưởng quyền 29/10/2026; VSDC xác nhận ngày đăng ký cuối cùng 30/10/2026 và tỷ lệ cổ tức cổ phiếu 50%. Engine hiện chưa mô phỏng đầy đủ quyền nhận cổ phiếu/ngày cổ phiếu mới được phép bán. Không được diễn giải mức giảm giá này là khoản lỗ kinh tế tương ứng của cổ đông đang nắm giữ.
- SSI ngày 17/08/2026 giảm khoảng 19,18%; chưa có hồ sơ sự kiện đã xác minh trong lần thực hiện này.
- Đơn vị kVND được lấy theo hợp đồng nạp dữ liệu hiện có, chưa có chứng thực đơn vị độc lập cho toàn bộ cache. Backtest chuyển sang VND trước khi tính lô 100 cổ phiếu.
- Danh mục 30 mã hiện tại chưa phải danh mục thành phần lịch sử point-in-time; vẫn có rủi ro survivorship bias.
- Tám cột chỉ báo cũ trong panel được bỏ khỏi snapshot nghiên cứu; chỉ báo được tính lại từ OHLCV. Không xóa hoặc ghi đè dữ liệu gốc.

Tệp data_audit.json lưu kết quả chi tiết từng mã và các ngày cần xác minh. Bộ kiểm tra chặn huấn luyện khi gặp lỗi cấu trúc/OHLCV; rủi ro điều chỉnh giá buộc bộ chạy nghiên cứu phải được gọi bằng chế độ chẩn đoán rõ ràng.

## 2. Thực nghiệm được cố định trước khi xem kết quả

- Bốn cutoff: 31/12/2025, 31/03/2026, 30/06/2026 và 30/09/2026. Kỳ kiểm thử tương ứng kết thúc 31/03, 30/06, 30/09 và 13/11/2026.
- Mỗi kỳ chỉ huấn luyện/chọn model bằng dữ liệu đến cutoff. Validation Buffer 40 phiên, purge ba phiên ở ranh giới Train, scaler fit Train, LSTM dùng 19 phiên warm-up.
- Mỗi kỳ cấu hình 40 epoch LSTM, chọn trọng số theo loss Validation; LightGBM early stopping 30 rounds. Không chỉnh siêu tham số sau khi xem holdout.
- Optimizer thực tế là Adam có weight_decay, không phải AdamW. Giữ nguyên để tránh thay thuật toán giữa thực nghiệm; bản thảo cần mô tả đúng hiện trạng này.
- Baseline phân loại: lớp đa số chọn từ Train từng kỳ. Baseline tài chính: Buy & Hold trên cùng 30 mã, cùng vốn và chi phí.
- Vốn 300 triệu VND, chia cố định 10 triệu/mã. Lô chẵn 100 cổ phiếu có thể khiến một số mã giá cao không mua được; phần vốn đó giữ tiền. Kết quả phụ thuộc hạn mức phân bổ này.
- Tín hiệu AI: mua khi xác suất lớp tăng đạt 0,40; nếu không mua thì bán khi xác suất lớp giảm đạt 0,40. Khớp tại Open phiên kế tiếp, dùng engine thanh toán hiện tại, phí 0,15% mỗi chiều, thuế bán 0,10%, trượt giá 0,05%.
- Risk-free rate mặc định 4%/năm trong Sharpe là giả định cấu hình, không phải lãi suất thị trường đã thu thập; quy đổi 252 phiên/năm. Đặc biệt, giữ nhiều tiền có thể làm Sharpe âm dù ROI dương.
- Mỗi kỳ có 100 danh mục tín hiệu ngẫu nhiên độc lập theo mã, xác suất giảm/giữ/tăng bằng 0,25/0,50/0,25; hai mô hình dùng chung 100 đối chứng đó. Tổng cộng 400 danh mục ngẫu nhiên, không phải 400 mẫu thị trường độc lập.
- Lưu toàn bộ vector kết quả Monte Carlo và seed 42. Ước lượng đuôi dùng hiệu chỉnh cộng một, nên N=100 có mức nhỏ nhất 1/101, không trả p=0 khi không có lần vượt.
- Đối chứng ngẫu nhiên không khớp tần suất giao dịch/thời gian nắm giữ của AI. Giá trị đuôi chỉ so sánh với giả thuyết ngẫu nhiên đã chỉ định; không chứng minh alpha, không thay kiểm định hoán vị hoặc hiệu chỉnh lựa chọn nhiều chiến lược. Các so sánh nhiều kỳ/mô hình là thăm dò.
- Chỉ đánh giá ngày đã có nhãn T+3 trưởng thành. Ba phiên cuối mỗi kỳ không có nhãn bị loại; mô phỏng tài chính dùng chính các ngày được chấm điểm đó. Không cộng hoặc nhân ROI các kỳ thành một tài khoản liên tục vì mỗi kỳ khởi tạo lại vốn.

Snapshot OHLCV, cấu hình, SHA-256 mã nguồn, bản sao nguồn, phiên bản thư viện, dự báo từng mẫu, giao dịch từng mã và đường vốn nằm tại apps/ml/reports/experiments/phase2_20261114. Thư mục nặng được .gitignore; cần sao lưu riêng nếu chuyển máy. Tệp phase2_results.json giữ bản kết quả gọn để theo dõi trong Git.

Mã chạy đang phát triển có thể khác mã lúc khởi tạo thí nghiệm do sửa tài liệu, định dạng và bổ sung kiểm tra. Muốn tái lập phải dùng source_snapshot đã đối chiếu hash trong protocol.json, không mặc định dùng HEAD hiện tại.

## 3. Đặc trưng: không được khẳng định tất cả đều I(0)

Đã chạy ADF và KPSS riêng cho 13 đặc trưng × 30 mã trên phần Train hợp lệ của kỳ 1, từ 03/04/2023 đến 28/10/2025, loại Validation và các dòng purge. Không dùng kết quả này để thay schema hoặc chọn mô hình sau khi xem holdout.

Thiết lập: statsmodels 0.14.5, ADF có hằng số, chọn lag AIC tối đa 10; KPSS level với số lag tự động. Có 248/390 chuỗi cùng thỏa ADF p < 0,05 và KPSS p ≥ 0,05 ở mức chưa hiệu chỉnh. Sau BH riêng cho từng họ 390 phép thử, ADF bác bỏ unit-root ở 329 chuỗi; KPSS bác bỏ level-stationarity ở 78 chuỗi. P-value KPSS bị giới hạn bởi bảng tra; các cảnh báo được giữ trong stationarity.json. Không bác bỏ giả thuyết không không phải chứng minh giả thuyết đó đúng.

SMA_200_Dev và CV_200 chỉ có 3/30 mã mỗi đặc trưng thỏa đồng thời hai điều kiện thăm dò chưa hiệu chỉnh. Cần sửa cách viết trong đồ án từ “13 đặc trưng dừng I(0)” thành “13 đặc trưng tương đối; tính dừng được kiểm tra theo từng mã và không đồng nhất”.

Không có cặp tương quan Pearson tuyệt đối ≥ 0,95 trên lịch sử trước cutoff đầu tiên, nhưng tồn tại phụ thuộc tuyến tính chính xác: HL_Ratio bằng High_Close_Ratio trừ Low_Close_Ratio, sai số số học tối đa khoảng 1,39 × 10⁻¹⁷. Vì vậy không được kết luận “đã loại đa cộng tuyến” chỉ dựa vào tương quan từng cặp. Bộ schema hiện tại vẫn được giữ để tương thích scaler/model; thử bỏ đặc trưng cần một thí nghiệm ablation riêng.

Statsmodels chỉ được dùng trong môi trường uv tạm cho chẩn đoán, không thêm phụ thuộc vào ứng dụng production. Script và kết quả đầy đủ được lưu cùng thí nghiệm.

## 4. Code không dùng đã dọn

| Vị trí | Thay đổi | Căn cứ |
|---|---|---|
| apps/web/src/components/Navbar.tsx | Xóa component cũ, 114 dòng | Không có đường import từ entrypoint App Router hoặc nguồn dự án |
| apps/web/src/components/market/IndexChartModal.tsx | Xóa tệp alias, 5 dòng | Không có nơi gọi; modal thực tế dùng FinancialDetailModal |
| apps/web/src/components/market/FinancialDetailModal.tsx | Xóa export alias IndexChartModal | Không có import tương ứng |
| apps/web/src/components/DashboardApp.tsx | Xóa default import React | JSX runtime hiện tại không cần import này |
| apps/api/app/services/stock_service.py | Xóa hai phép gán vni_sparkline | Giá trị không được đọc/không trả về response |
| apps/ml/vn_stock/backtest.py | Xóa danh sách mc_win_rates và phép append | Kết quả không được sử dụng |

Đã kiểm tra đồ thị import TypeScript từ entrypoint App Router/proxy, tra cứu tham chiếu, kiểm tra TypeScript với noUnusedLocals/noUnusedParameters, và Ruff F401/F841/F811/F821 cho nguồn Python ML/API/infra. Việc xóa giảm mã phải bảo trì và một phần tính toán thừa; chưa có benchmark để khẳng định tăng FPS hoặc giảm bundle đáng kể.

Các hàm adapter cũ vẫn có export/test/điểm gọi, cơ chế __getattr__, package re-export và import chỉ phục vụ typing không bị coi là dead code chỉ vì ít tham chiếu tĩnh. Phạm vi đã xác minh không đồng nghĩa chứng minh tuyệt đối mọi tệp trong repository đều được dùng.

## 5. Kiểm thử hồi quy

| Nhóm | Số test đạt |
|---|---:|
| apps/ml | 138 |
| apps/api | 175 |
| apps/web | 165 |
| infra | 35 |
| E2E dùng contract reference/mô phỏng | 87 |
| Tổng | 600 |

Phase 2 thêm 12 test: kiểm tra dữ liệu 5, Monte Carlo 5 và nghiên cứu tài chính 2. Tổng tăng từ 588 ở cuối Phase 1 lên 600. Con số 569 trong bản thảo là số lịch sử, không phải số test mới nhất.

Next.js production build và TypeScript strict/noUnused đều đạt. Kiểm tra diff không có lỗi whitespace. Ruff các module mới và nhóm lỗi biến/import không dùng đạt; không tuyên bố toàn bộ quy tắc lint của mọi tệp cũ đã sạch.

Một lần chạy test tốc độ dựng đường SVG bị quá ngưỡng 50 ms khi đồng thời huấn luyện và build; test riêng và toàn bộ 165 test web chạy lại đều đạt. Không nới ngưỡng hoặc sửa test để che lỗi. Các cảnh báo hiện có gồm API TestClient/httpx, test va chạm ORM/JWT và LightGBM eval_set deprecated; chưa đổi thư viện trong đợt này.

87 E2E trên không xác nhận toàn bộ dịch vụ thật, CSDL thật hay trình duyệt thật. Cần một đợt nghiệm thu tích hợp live riêng.

## 6. Điều kiện trước khi dùng kết quả làm số liệu cuối

1. Lập sổ sự kiện doanh nghiệp có nguồn chính thức, ngày không hưởng quyền, tỷ lệ, ngày cổ phiếu mới khả dụng; xác minh SSI và các biến động còn lại. Chọn rõ giá điều chỉnh cho nghiên cứu nhãn và giá có thể khớp kèm quyền cổ đông cho mô phỏng tài sản.
2. Bổ sung lịch giao dịch và thành phần danh mục lịch sử. Ghi rõ nếu chỉ nghiên cứu tập 30 mã cố định thay vì tuyên bố đại diện toàn thị trường.
3. Chạy lại giao thức đã cố định trên dữ liệu đã xác minh; không sửa số liệu V1 theo các kết quả chẩn đoán dưới đây.
4. Nếu tối ưu mô hình, chốt ablation/siêu tham số bằng Train/Validation hoặc nested walk-forward, dành giai đoạn chưa dùng để xác nhận sau cùng. Các kỳ 2026 dưới đây đã được xem, không còn là bộ test kín cho mọi vòng tối ưu tiếp theo.
5. Nghiệm thu live trước khi mô tả hệ thống đã vượt kiểm thử end-to-end thực tế. Chỉ cập nhật Word sau khi đối soát artifact, dữ liệu, công thức và kết quả.

## Nguồn đã đối chiếu

- VSDC, TCB phát hành cổ phiếu trả cổ tức, cập nhật 22/10/2026: https://vsdc.vn/vi/ad1/201641
- HOSE, thông báo 2100/TB-SGDHCM ngày 23/10/2026, ngày không hưởng quyền TCB 29/10/2026: https://staticfile.hsx.vn/Uploads/UploadDocuments/2507504/20261023%20-%20TCB%20-%20TB%20NDKCC%20phat%20hanh%20CP%20de%20tra%20co%20tuc.pdf
- Phipson và Smyth, “Permutation p-values should never be zero”, 2010, DOI 10.2202/1544-6115.1585; bản tác giả: https://arxiv.org/abs/1603.05766
- Scikit-learn, Cross-validation: https://scikit-learn.org/stable/modules/cross_validation.html
- Statsmodels, ADF: https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html
- Statsmodels, KPSS: https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.kpss.html

## 7. Kết quả thực nghiệm đã đối soát — chỉ dùng chẩn đoán

| Kỳ | Ngày có nhãn được chấm điểm | Mẫu/mô hình | LightGBM F1 | LSTM F1 | Baseline F1 |
|---|---|---:|---:|---:|---:|
| 1 | 2026-01-05 → 2026-03-26 | 1620 | 0.3744 | 0.3238 | 0.1877 |
| 2 | 2026-04-01 → 2026-06-25 | 1770 | 0.4235 | 0.3951 | 0.2469 |
| 3 | 2026-07-01 → 2026-09-25 | 1800 | 0.3892 | 0.3895 | 0.2245 |
| 4 | 2026-10-01 → 2026-11-10 | 870 | 0.4030 | 0.3187 | 0.2467 |

Gộp dự báo không chồng lấn: 6,060 mẫu/mô hình. F1 gộp tính lại từ từng dự báo, không lấy trung bình các F1.

| Mô hình | Accuracy gộp | Macro F1 gộp |
|---|---:|---:|
| lightgbm | 43.28% | 0.4087 |
| lstm | 41.62% | 0.3898 |
| train_majority_baseline | 51.17% | 0.2257 |

| Kỳ | Mô hình | ROI % | Buy & Hold % | Sharpe | MDD % | P đuôi ROI | P đuôi Sharpe |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | lightgbm | -7.62 | -3.34 | -2.4466 | 11.27 | 0.9703 | 0.8119 |
| 1 | lstm | -5.37 | -3.34 | -1.8423 | 9.58 | 0.7723 | 0.4653 |
| 2 | lightgbm | 0.17 | -0.05 | -2.5814 | 0.36 | 0.0693 | 0.9901 |
| 2 | lstm | -0.21 | -0.05 | -1.0485 | 1.83 | 0.0990 | 0.2079 |
| 3 | lightgbm | -0.02 | -4.73 | -0.3306 | 5.77 | 0.0099 | 0.0099 |
| 3 | lstm | 1.56 | -4.73 | 0.4059 | 3.08 | 0.0099 | 0.0099 |
| 4 | lightgbm | -1.99 | -3.82 | -3.7079 | 2.70 | 0.2475 | 0.6634 |
| 4 | lstm | -0.78 | -3.82 | -7.7220 | 0.85 | 0.0099 | 1.0000 |

Các giá trị tài chính trên không được dùng chứng minh khả năng sinh lời vì chưa xử lý đủ quyền cổ đông. P-value là xác suất đuôi dưới đối chứng iid đã chỉ định, chưa hiệu chỉnh nhiều so sánh.

Đã đối chiếu hash dữ liệu và toàn bộ nguồn đóng băng, tính lại metrics từ dự báo từng mẫu; cả bốn kỳ đều hoàn thành 40 epoch và mỗi mô hình có đủ 30 mã. Chi tiết nhầm lẫn ba lớp, số mẫu Train hiệu dụng và epoch LSTM tốt nhất lưu trong phase2_results.json.
