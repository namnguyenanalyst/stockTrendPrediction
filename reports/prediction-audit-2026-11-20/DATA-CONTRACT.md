# Hợp đồng dữ liệu tab Dự báo xu hướng

Đối chiếu với DashboardApp, api.ts, PredictionResponse, prediction_service và FireAntTrajectoryChart trong worktree ngày 21/11/2026. Mỗi lần chọn mã/model tải một nhóm history, indicators, summary, signal bằng Promise.allSettled. Chỉ nhận kết quả khi effect còn hiệu lực; fetchedKey phải khớp symbol:model trước khi truyền nến/dự báo cho tab.

| Trường/khối UI | Nguồn | Đơn vị, thời điểm | Ưu tiên và khi thiếu |
|---|---|---|---|
| Mã đang chọn | selectedSymbol trong DashboardApp | Symbol chuẩn hóa ở API | Dữ liệu response phải khớp lựa chọn; response cũ bị bỏ qua |
| Mô hình | modelType → signal query | lightgbm hoặc lstm | Không dùng kết quả của model trước khi đổi lựa chọn |
| Nến và OHLC header biểu đồ | GET /api/stocks/history | Giá nghìn VNĐ; volume cổ phiếu; date theo phiên | Không còn request history dự phòng trong AIPredictionTab; thiếu thì nến rỗng |
| Chỉ báo kỹ thuật đi kèm | GET /api/stocks/indicators | Chuỗi theo ngày, dùng hợp đồng endpoint hiện hữu | Endpoint lỗi không biến thành dữ liệu chỉ báo giả |
| Thông tin tổng hợp | GET /api/stocks/summary | Các tỷ lệ có quy ước riêng theo schema | Summary SMA deviation là phần trăm sẵn; không nhân thêm 100 |
| Giá đóng cửa căn cứ dự báo | GET /api/predict/signal → current_price | Nghìn VNĐ; UI nhân 1.000 thành VNĐ | Không lấy giá live/header để thay giá căn cứ |
| Ngày căn cứ | signal.data_as_of_date; fallback tương thích signal.date | Ngày dữ liệu đầu vào suy luận, không phải thời điểm request | Muốn vẽ trajectory phải khớp ngày nến cuối |
| Ba xác suất | signal.probabilities | 0–1 ở API; UI nhân 100 để hiển thị % | Hữu hạn, đúng ba lớp, tổng xấp xỉ 1; lỗi tải hiển thị — |
| Xu hướng/tín hiệu | predicted_label/class_name/signal | Lớp 0 giảm, 1 đi ngang, 2 tăng; áp quy tắc tín hiệu backend | Kiểm tra tính nhất quán nhãn và xác suất; không đổi lỗi tải thành HOLD |
| Phiên mục tiêu/trạng thái cập nhật | GET /api/v1/predict/status có Bearer token | Trạng thái thị trường và metadata huấn luyện | Không coi target date là bằng chứng nến/artifact đã mới; thiếu thì ghi chưa tải được |
| Metadata artifact | signal.training_info | artifact_generation, serving_status và mốc huấn luyện | degraded_cached_generation hiện cảnh báo; giữ trọn generation cũ khi reload hỏng |
| Nguồn giá | signal.data_quality | historical_adjustment_status và source_provenance | unverified được công khai; không tự nâng thành đã xác thực |
| T+1 → T+3 | signal.trajectory + nến gốc → buildTrajectory | Ba ngày giao dịch; đường giá minh họa bằng quy tắc FE | Yêu cầu đủ 3 bước, ngày tăng, confidence/probabilities hợp lệ, giá gốc khớp ≤0,011 nghìn VNĐ; thiếu thì nêu lý do |
| Lịch nghỉ | trajectory[].holiday_calendar_verified | Đã đối chiếu năm 2026; năm khác chưa xác nhận | Chỉ hiển thị đã xác minh khi cả 3 bước true |
| Bảng chi tiết quỹ đạo | Cùng buildTrajectory với series | VNĐ, tổng % so với T | Không tạo bộ số riêng khác với đường vẽ |
| Lịch sử | LocalStorage v2 theo user ID | Symbol/model/ngày dữ liệu và thời điểm lưu | Chỉ lưu dự báo hợp lệ, dedupe theo symbol/model/ngày; không nhập legacy vô chủ; storage lỗi dùng RAM |
| Dự báo bảng thị trường dùng chung | GET /api/predict/batch | predictions + requested_symbols + errors | Lỗi từng mã được ghi rõ, không tạo dự báo giả; không ưu tiên batch cũ hơn signal đang chọn |

## Đường đi backend

Signal → prediction_service → snapshot model/scaler/metadata cùng generation → prepare_inference_features → dữ liệu panel/raw theo ngày, raw ưu tiên trên overlap → tính đặc trưng nhân quả → transform bằng scaler huấn luyện → LightGBM hoặc tensor chuỗi LSTM → phân phối 3 lớp → nhãn/tín hiệu/trajectory → Pydantic → API client TypeScript.

Endpoint có cả prefix `/api` và `/api/v1` qua router đăng ký. Live GET/POST gây đồng bộ và yêu cầu người dùng active; retrain dùng worker secret riêng. Audit tải/huấn luyện sử dụng bản sao, không gọi live hoặc retrain sản xuất để tạo bằng chứng đọc.

## Giới hạn kiểm chứng

Artifact legacy chưa có đầy đủ provenance để khẳng định giai đoạn test độc lập. Chất lượng được đo bằng ba fold huấn luyện lịch sử riêng trong quality-early-stopping. Lịch sử giá chưa có corporate-action provenance độc lập toàn bộ mã/ngày. Hai giới hạn này không được suy diễn là đạt từ test tính toán hoặc OHLC hợp lệ.


## Luồng Live dùng snapshot theo yêu cầu

`/api/predict/live` và `/api/v1/predict/live`, GET/POST, giữ yêu cầu người dùng đăng nhập. Luồng này tải SSI stock và VNINDEX trong bộ nhớ, truyền cùng snapshot vào mô hình; không ghi cache raw/panel hoặc artifact. `is_live_synced=true` xác nhận dữ liệu mới đã được dùng cho response, không xác nhận dữ liệu đã được lưu. `data_quality.source_provenance=SSI_request_snapshot`; historical_adjustment_status vẫn unverified. `/stocks/sync` tiếp tục là thao tác ghi riêng theo quyền hiện hữu.

Stock rolling features dùng toàn bộ lịch sử SSI được trả về. Market return dùng đủ seq_length+1 đóng cửa gần nhất, chốt cùng target_date, không fallback cache khi nguồn thiếu hoặc lỗi. Các return trước cửa sổ này để NaN; tính rolling stock trước khi drop những dòng thiếu feature. Snapshot thiếu/wrong-symbol/duplicate-date không được thay ngầm bằng global panel.


### Chính sách mới: hoàn tác can thiệp theo biên độ giá

Theo yêu cầu người dùng, đã bỏ cơ chế chặn suy luận/huấn luyện/refresh dựa trên bước nhảy 20% và các 503 riêng cho lịch sử chưa xác minh. Các đoạn ghi guard/chặn trong báo cáo trước đây chỉ còn giá trị truy vết, không mô tả chính sách đang phục vụ. Không áp hệ số sửa giá dựa trên suy đoán corporate action. Dữ liệu SSI là đầu vào duy nhất; hạn chế điều chỉnh được công bố, không tự coi mọi bước nhảy là lỗi. Các kiểm tra cấu trúc, ngày/đơn vị, NaN/Infinity, lỗi mạng và tính đúng của luồng phần mềm vẫn được giữ.
