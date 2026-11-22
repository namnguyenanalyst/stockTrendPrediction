# Kiểm tra tab Dự báo xu hướng — bắt đầu 20/11, tiếp tục 21/11/2026

Trạng thái: đã hoàn thành vòng sửa lỗi, smoke Docker, E2E đăng nhập cơ bản và ba fold walk-forward. Chưa nghiệm thu toàn diện các hạng mục mở được liệt kê ở cuối báo cáo.

**Đọc trạng thái hiện tại tại [CURRENT-STATUS.md](CURRENT-STATUS.md).** Các mục phía dưới là nhật ký theo thời điểm; các câu “chưa kiểm tra” trong nhật ký có thể đã được xử lý ở vòng sau. Chỉ ma trận hiện tại được dùng để xác định hạng mục còn mở.

## Luồng dữ liệu và hợp đồng

`DashboardApp → api.ts → /api/stocks/history, /indicators, /summary + /api/predict/signal → prediction_service → load_prediction_snapshot + prepare_inference_features → scaler → LightGBM/LSTM → PredictionResponse → AIPredictionTab → FireAntTrajectoryChart`.

- OHLC và current_price: nghìn VNĐ; frontend nhân 1.000 để trình bày VNĐ.
- probabilities: [0,1], lớp 0 GIẢM / 1 ĐI NGANG / 2 TĂNG; tổng xấp xỉ 1.
- date/data_as_of_date: ngày chốt dữ liệu, khác ngày chạy và ngày huấn luyện.
- summary SMA deviation: phần trăm sẵn; indicator SMA deviation: tỷ lệ. Không dùng chung phép nhân 100.
- status: `/api/v1/predict/status`, có xác thực. Phiên mục tiêu theo đồng hồ không chứng minh nến hoặc model đã cập nhật.
- trajectory: ba mốc minh hoạ từ đầu ra phân loại T+3; đường giá theo quy tắc frontend, không phải ba dự báo giá độc lập.
- lịch sử: lưu cục bộ theo user ID, không dùng khóa legacy chung tài khoản.

## Phát hiện và sửa

| ID | Mức | Tái hiện/nguyên nhân | Thay đổi | Bằng chứng |
|---|---|---|---|---|
| A01 | Cao | probabilities/model_type null làm matchesPrediction crash | Kiểm tra cấu trúc, giá hữu hạn, nhãn/xác suất | predictionAudit.test.ts |
| A02 | Cao | Khóa history chung mọi tài khoản, JSON có thể không là mảng | Khóa v2 theo user ID, lọc bản ghi, không nhập legacy không có chủ sở hữu | predictionHistory.ts; cần E2E hai tài khoản |
| A03 | Cao | raw thay panel tạo cột phụ NaN và VNINDEX_Return_1d NaN, API chỉ báo trả 0 dòng | Chỉ trả OHLCV cần thiết; tính market return theo ngày từ raw index | baseline API test thất bại; test_api sau sửa |
| A04 | Vừa | Batch bỏ qua mã lỗi | Bổ sung requested_symbols và errors, giữ total_symbols là số thành công | test_prediction_audit.py |
| A05 | Cao | Đổi lựa chọn có thể còn nến/response trước; child gọi history trùng | Gắn kết dữ liệu với selection key, remount theo account/mã/model; bỏ request dự phòng trùng | cần E2E response chậm và network count |
| A06 | Vừa | Thiếu trajectory bị tự điền ngày/xu hướng/xác suất | Chỉ vẽ đủ ba bước hợp lệ, đúng ngày và giá gốc; giải thích lý do ẩn | predictionAudit.test.ts |
| A07 | Vừa | API lỗi không có nút retry; bar xác suất tối thiểu 2% dù không có dự báo | Retry và thông báo lỗi; bar đúng giá trị, 0 khi không có dữ liệu | TypeScript/Vitest; cần E2E lỗi mạng |
| A08 | Vừa | Resize đổi height tạo chart mới nhưng effect dữ liệu không chạy | Thêm height vào phụ thuộc dữ liệu/toggle | cần xác minh hình ảnh |
| A09 | Thấp | Hover timer còn sống sau unmount; mô tả model chỉ hover | Cleanup timer; hỗ trợ focus bàn phím | ESLint; cần kiểm tra bàn phím thực |
| A10 | Vừa | Lịch sử chèn trùng khi quay lại mã đã xem, giá cũ gán vào modal nến mới | Dedupe theo mã/model/phiên trong toàn bộ history; modal dùng dữ liệu mới tự tải | cần E2E lịch sử |

## Bằng chứng và lệnh tái lập

- `baseline.json`: git/container/hash artifact ban đầu. Không ghi secret.
- `web-baseline.txt`, `api-baseline.txt`, `ml-baseline.txt`: trạng thái trước sửa. API ban đầu có test_stocks_indicators thất bại.
- `live-api.json`: API Docker thực, ngày/giá nến-dự báo, GET/POST, single/batch, kiểm tra quyền không có credential. Chỉ có khi script chạy hoàn tất.
- `data-model-audit.json`: 30 mã, OHLCV, trùng ngày, kiểm tra đặc trưng quá khứ không đổi khi nối dữ liệu tương lai, metadata artifact.
- `quality/`: snapshot dữ liệu, hash, ba fold huấn luyện lịch sử tích luỹ, mô hình riêng từng fold, dự báo và chỉ số ngoài mẫu. Không promote vào models sản xuất.

```sh
cd apps/web
npx vitest run
npx tsc --noEmit
npx eslint src/components/DashboardApp.tsx src/components/tabs/AIPredictionTab.tsx src/components/charts/FireAntTrajectoryChart.tsx src/lib/prediction*.ts
```

```sh
cd apps/api
.venv/bin/python -m pytest tests -q
```

Từ root:
```sh
uv run pytest apps/ml/tests -q
PYTHONPATH=apps/ml apps/ml/.venv/bin/python scripts/audit/prediction_data.py
PYTHONPATH=apps/ml apps/ml/.venv/bin/python scripts/audit/prediction_quality.py
python scripts/audit/prediction_live.py
```

## Chưa được phép đánh dấu đạt

- E2E đăng nhập: browser kiểm thử bị chuyển về login. Chưa có session được cung cấp; không bypass xác thực.
- 390/768/1280/1920 px, zoom 200%, console/network, pan/zoom/toggle và ảnh chụp sau đăng nhập.
- Cold start và tải 1/5/10 request đồng thời trong môi trường kiểm thử riêng; không dùng latency smoke trên production làm kết luận chịu tải.
- Nhận diện điều chỉnh cổ tức/chia tách: chưa có nguồn provenance đã xác thực. OHLC hợp lệ không chứng minh dữ liệu adjusted nhất quán.
- Lịch nghỉ lễ: backend chỉ bỏ cuối tuần; chưa có lịch nghỉ chính thức. Giao diện phải giữ giới hạn này.
- Artifact legacy thiếu provenance: không khẳng định kết quả validation lưu trong production metadata là test độc lập.
- LSTM có chọn best validation epoch nhưng vòng huấn luyện hiện chạy hết epochs; chưa có dừng sớm theo patience.
- Endpoint live/sync có ghi dữ liệu; cần đối chiếu chính sách quyền trước khi đổi hành vi API hiện hữu.
- Khả năng bundle/cache giữ model cũ có log nhưng UI chưa có trạng thái degraded/generation đầy đủ.

## Cập nhật và phục hồi

Backend bind-mount app nhưng code ML nằm trong image: thay module ML cần rebuild image, không chỉ restart. Dùng `docker build -t infra-vn_stock_api:latest -f apps/api/Dockerfile .` rồi recreate đúng service với `--no-build`. Không chạy retrain sản xuất cho thử nghiệm. Giữ hash/model artifact ban đầu; rollback bằng image cũ và snapshot mã trước thay đổi, không xóa volume database.

## Kết quả đã xác minh khi tiếp tục 21/11

- Frontend: 200 test đạt, TypeScript đạt, ESLint các file dự báo đạt.
- ML baseline: 140 test đạt. Kiểm tra causal feature trên snapshot 30 mã đạt.
- API mục tiêu: 32 test đạt, gồm lỗi chỉ báo rỗng và batch error. Bộ API đầy đủ lưu tại api-final.txt.
- Docker smoke: 60/60 dự báo của 30 mã × hai model khớp ngày/giá; GET/POST và single/batch VIC khớp cả hai model.
- Quyền: status không token → 401; retrain không worker secret → 403; market sync không token → 401. Đây chưa thay thế ma trận user/admin đầy đủ.
- Latency smoke trên cache ấm: p50 khoảng 0,117 giây, p95 khoảng 0,278 giây; không phải benchmark chịu tải.
- Fold 1 (600 mẫu, 19/08–18/09/2026): LightGBM accuracy 0,4800 / macro-F1 0,4076; LSTM 0,4550 / 0,3603; baseline lớp phổ biến 0,5883 / 0,2469. Chưa kết luận ba fold khi chưa có quality/summary.json.
- Browser 21/11: dashboard chuyển về login. E2E sau đăng nhập và responsive chưa xác minh.

## Bổ sung kiểm chứng E2E và tải đồng thời

- Đã tạo môi trường kiểm thử riêng trong /tmp/stock-prediction-e2e: SQLite riêng, tài khoản audit@example.test riêng, API 8001 và bản sao frontend 3001; đăng nhập qua endpoint thật, không bỏ qua xác thực. Không tạo tài khoản trên database chính, không gửi thư xác minh.
- Đã xem trực tiếp tab dự báo sau đăng nhập: LightGBM VIC 41,6% lớp giảm; đổi LSTM thành 41,4%; ngày chốt 20/11; giá 241.900 VNĐ; hai bản ghi lịch sử riêng theo model.
- Đã quan sát chart LSTM thực: đường giảm từ phiên T tới ba điểm tương lai 23/24/25-11; nhãn 232.110 VNĐ T+3 khớp bảng chi tiết. Loading khi đổi model không giữ phần xác suất cũ.
- Phát hiện mô tả footer còn khẳng định LightGBM hợp sideway/LSTM hợp trend dù chưa có bằng chứng; đã thay bằng hướng dẫn so sánh ngoài mẫu.
- offline-load.json: cả hai model suy luận với 1/5/10 luồng đều không lỗi, dữ liệu cố định, không ghi production. Phép thử này không bao gồm network/DB/SSI.
- API đầy đủ sau sửa: 235 passed, 1 skipped, 7 warnings (api-final.txt).
- Chưa kiểm tra đủ: toàn bộ ma trận responsive/zoom, E2E lỗi mạng/race và hai tài khoản, live sync lỗi upstream, benchmark HTTP đồng thời, worker mất kết nối. Không đồng nhất E2E môi trường riêng với nghiệm thu tất cả tình huống trên hệ thống chính.

## Kết quả walk-forward cuối cùng

- lightgbm: 1800 mẫu, accuracy 0.4750, macro-F1 0.3995, log loss 1.0779, Brier 0.6512.
- lstm: 1800 mẫu, accuracy 0.4483, macro-F1 0.3656, log loss 1.0728, Brier 0.6454.
- Baseline theo prior train (argmax tương đương lớp phổ biến): accuracy 0.5839, macro-F1 0.2458.
- Đủ ba fold, tổng hợp calibration, ROC-AUC, từng mã và từng fold tại quality/summary.json. Accuracy mô hình thấp hơn baseline; không kết luận mô hình có ưu thế đầu tư.
- Kiểm tra breakpoint phát hiện sidebar mở chiếm 256/390px: đã thêm tự thu gọn khi vào màn hình dưới 768px. Cần kiểm tra lại bản sửa trên thiết bị thực.
- Đã kiểm tra lại responsive sau sửa trong bản sao E2E: viewport 390px, sidebar 80px và main 304px (trước đó sidebar 256px, main 128px). Tab vẫn có tín hiệu, đủ trajectory, hai bản ghi lịch sử và dedupe giữ nguyên khi tải lại. Đây chưa thay thế kiểm tra hình ảnh đầy đủ mọi viewport/zoom.

## Tiếp tục mục còn thiếu — 21/11

- Đã bổ sung LSTM early stopping theo validation loss, patience mặc định 10. Metadata tách epochs_requested / epochs_completed và lưu patience. Test tích hợp loss validation cố định chứng minh yêu cầu 10 epoch thực dừng ở epoch 3 khi patience=2, giữ best epoch 1; không xuất production artifact.
- Snapshot metadata bổ sung artifact_generation và serving_status. Reload thất bại giữ nguyên model/scaler/metadata thế hệ đã xác minh, trả degraded_cached_generation dưới dạng bản sao, không làm hỏng metadata healthy trong cache. FE có thông báo đang phục vụ bản cũ.
- Test đọc đồng thời: 75 snapshot trong khi xuất 5 thế hệ mới; tất cả model/scaler/version thống nhất, thế hệ cuối đúng. Test artifact hỏng xác nhận đúng generation và degraded status.
- Test SSI lỗi và dữ liệu stale: trả 503, không lộ chi tiết nội bộ và không gọi suy luận khi nguồn chưa đủ mới.
- Dashboard component integration (mô phỏng response thật qua API client mock): đổi VIC → HPG trước response VIC, trả VIC muộn không ghi đè HPG; không giữ nến cũ; đúng 2 lượt history cho 2 mã. Lỗi prediction hiện lỗi và retry gọi lại thành công. Hai test đạt.
- Những test FE này không thay thế E2E trình duyệt lỗi mạng. Các thay đổi module ML mới chưa được đưa vào image sản xuất ở thời điểm ghi mục này; không retrain hoặc promote production.

## Kiểm tra tiếp E2E và tải HTTP

- e2e-remaining.json ghi các quan sát trực tiếp: signal 503 hiển thị lỗi đúng, xác suất rỗng, nến còn; clear fault + Thử lại khôi phục đầy đủ. Toggle trajectory ẩn/hiện đúng; chuyển 6M vẫn giữ điểm tương lai.
- E2E hai tài khoản đã thực hiện trên SQLite riêng: Audit Test có hai bản ghi; logout; Audit Two đăng nhập có đúng một bản ghi mới, không có LSTM của tài khoản trước.
- Đã đo 390/768/1280/1920px và quan sát screenshot desktop/mobile. Không có tràn ngang toàn trang; main 304px sau sidebar gọn ở 390. Zoom 200%, kiểm tra focus và tương tác toàn bộ viewport vẫn chưa hoàn thành.
- HTTP-load.json: API riêng, restart trước đo, 2/10/20 request tại mức 1/5/10 cho từng model, không lỗi. p95 mức 10: LightGBM 0,994 giây; LSTM 0,783 giây. First request: LightGBM 2,205 giây; LSTM 1,856 giây (đã có shared import/OS cache). Đây không phải sustained-load SLA.
- Harness tái lập: scripts/audit/isolated_e2e_server.py; cấu hình fault nằm riêng /tmp, không thêm endpoint gây lỗi vào sản phẩm. scripts/audit/prediction_http_load.py chỉ gọi cổng 8001.
- Đã khởi chạy quality-early-stopping trên đúng snapshot cũ để kiểm tra lại chất lượng pipeline sau sửa patience. Kết quả quality/ trước đó vẫn được giữ như bằng chứng phiên bản trước sửa; chưa dùng nó để tuyên bố chất lượng phiên bản mới.

## Ma trận quyền, phiên và vận hành — cập nhật tiếp

- Phát hiện và sửa: GET/POST /predict/live trước đó cho phép anonymous gây đồng bộ ghi dữ liệu. Cả /api và /api/v1 nay yêu cầu get_current_active_user, giống thao tác /stocks/sync. Đây là thay đổi quyền có chủ đích: caller live cần Bearer token; endpoint signal/batch chỉ đọc giữ hợp đồng hiện tại.
- permissions-readiness.txt: 31 test đạt. Gồm anonymous live bị 401 ở hai prefix/hai method; user/admin active được tới service; tài khoản inactive bị 400; worker secret không thể giả làm user; retrain vẫn cần secret riêng; readiness báo 503 khi DB lỗi và không lộ chi tiết.
- live-contract-after-auth.txt: test GET/POST live với auth dependency phù hợp đạt. Không dùng dependency override của test này làm bằng chứng cho ma trận token thật; ma trận trên tạo user DB và token thật riêng.
- worker-market-session.txt: 14 test đạt. Worker mất kết nối báo lỗi, thử lại lần sau và không chạy lặp trong ngày sau thành công. Database outage/timeout đã có test readiness riêng.
- Phát hiện và sửa timezone: input aware UTC cần đổi sang Asia/Ho_Chi_Minh trước so sánh ATC. Test trước sửa thất bại tại 08:00 UTC; sau sửa đúng 15:00 VN và thông tin phiên khớp. Naive input vẫn được hiểu là giờ Việt Nam theo quy ước hiện có.
- Đã lưu image cũ dưới infra-vn_stock_api:audit-before-remaining và ID tại image-before-remaining.txt trước khi build lại module ML/API mới; chưa promote artifact huấn luyện.

## Hồi quy và giới hạn dữ liệu đã đối chiếu

- api-post-permissions.txt: 250 passed, 1 skipped; ml-post-session.txt: 145 passed; infra-post-session.txt: 39 passed.
- Lệnh gộp ML+infra ban đầu lỗi collection vì môi trường ML không có SQLAlchemy. Đã chạy ML bằng uv/ML và infra bằng interpreter API có dependency phù hợp; không báo lỗi môi trường là lỗi sản phẩm.
- Hai test Compose cũ đòi config chạy với zero env trái yêu cầu FRONTEND_PUBLIC_URL bắt buộc. Đã sửa test để xác nhận thiếu URL phải bị từ chối và explicit test URL render thành công, không nới cấu hình sản phẩm.
- predictionTimeout.test.ts: request signal/history không phản hồi bị abort sau 30 giây. API client áp timeout cho các request read-only history/indicators/summary/signal/batch; không áp timeout này vào retrain/backtest. Không còn chờ vô hạn do các dependency này.
- AIPredictionTab.storage.test.tsx: đọc storage bị chặn và ghi storage hết quota đều không crash; dự báo và lịch sử trong RAM vẫn hoạt động. Cần phân biệt kiểm thử component với quan sát browser quota thực.
- quality-early-stopping/summary.json: hoàn tất ba fold, 1.800 mẫu; accuracy/macro-F1 giống bản trước sửa. Epoch thực chạy fold 1/2/3 là 16/12/13, best epoch 6/2/3. Production artifacts không được promote từ các fold.
- calendar-and-adjustment-sources.md: nguồn HOSE 2026, tài liệu SSI DailyOhlc/DailyStockPrice và trường ClosePriceAdjusted. Hiện code calendar mới sửa timezone, vẫn chưa áp danh sách ngày lễ; giới hạn này còn hiển thị ở biểu đồ. Chưa có corporate-action provenance cho mọi file/mã/ngày.

## Lịch giao dịch và nguồn giá — kiểm tra tiếp

- Đã bổ sung ngày nghỉ giao dịch năm 2026 theo nguồn HOSE [calendar-and-adjustment-sources.md], gồm cập nhật nghỉ 02/01. target date lùi qua ngày nghỉ; future trading days bỏ cả cuối tuần và ngày nghỉ. Test qua 01/01, Tết Âm lịch, Quốc khánh và năm chưa xác minh đạt.
- Metadata holiday_calendar_verified theo từng ngày tương lai, không khẳng định lịch năm 2027 đã xác minh. FE chỉ ghi đã đối chiếu 2026 khi cả ba bước có xác nhận; trường hợp thiếu metadata vẫn giữ thông báo giới hạn.
- raw-panel-reconciliation.json: 30 mã, các ngày giao nhau đều khớp Close (0 sai khác vượt 0,011 nghìn VNĐ). calendar-data-reconciliation.json: snapshot không chứa hàng trên các ngày nghỉ 2026 đã xác minh.
- Không suy diễn giá đã điều chỉnh từ sự khớp raw/panel. PredictionResponse bổ sung data_quality và UI ghi rõ trạng thái chưa xác minh đầy đủ điều chỉnh cổ tức/chia tách. Cần nguồn dữ liệu điều chỉnh hoặc lịch corporate-action độc lập để nâng trạng thái này.
- production-artifact-preservation.json đối chiếu SHA256 với baseline để kiểm tra các thử nghiệm không promote/ghi đè artifact sản xuất.
- Các thay đổi calendar/data_quality mới còn cần rebuild và smoke container trước nghiệm thu. Không coi các lần smoke trước thay đổi là bằng chứng triển khai của bản này.
