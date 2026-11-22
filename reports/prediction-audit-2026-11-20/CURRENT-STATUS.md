# Trạng thái nghiệm thu hiện tại — cập nhật 22/11/2026

## Thay đổi chính sách theo yêu cầu người dùng: hoàn tác can thiệp bất thường giá

**Mục này thay thế các trạng thái chặn giá/503 do heuristic trong lịch sử báo cáo bên dưới.** Đã bỏ ngưỡng nhảy giá 20%, việc quarantine lịch sử tại suy luận/huấn luyện/strict refresh, exception UnverifiedPriceHistoryError và đường public 503 riêng. Không tự sửa hệ số, giá hoặc nhãn theo lịch chia suy đoán. CTG/HDB/TCB không còn bị từ chối chỉ vì bước nhảy giá. Dữ liệu điều chỉnh SSI được ghi là hạn chế nguồn, không dùng làm lý do chặn mặc định.

Giữ các sửa độc lập: ngày chốt động; sync partial/error không báo thành công; model/scaler cùng generation; cập nhật model báo đúng trạng thái; credentials SSI trong Compose; Live dùng snapshot đúng yêu cầu trong bộ nhớ và không ghi cache; kiểm tra sai mã, thiếu/trùng ngày, giá không hữu hạn, lỗi mạng, không đủ feature. Metadata unverified chỉ thông báo hạn chế, không tự sửa hoặc chặn giá theo biên độ.

Không sửa lại file giá hay artifact trong lần hoàn tác này. Sự cố làm mới VIC từ SSI trước đây đã có báo cáo riêng, không có bản sao byte-for-byte trước sự cố nên không khôi phục bằng dữ liệu suy đoán. Các snapshot đối chiếu chỉ lưu trong reports, không promote vào dữ liệu/model sản xuất.


## Chốt phần trọng tâm sau sửa Live

**Phần mềm đã có các sửa trọng yếu và đã triển khai; mục tiêu chưa thể kết luận hoàn tất vì lịch sử giá SSI còn cần làm rõ.** Không mở rộng rà soát giao diện/lỗi nhỏ hoặc lặp lại phần công việc đã hoàn tất trước đó.

- Image phục vụ: `sha256:c014f3f658c54f46790f502954e5abb82909f208b906399f87ebccb3e53cec5d`. Docker đã nhận cấu hình SSI, không log credential. Live thực dùng snapshot trong bộ nhớ, chạy VIC/HPG × LightGBM/LSTM khoảng 9–12 giây/yêu cầu; 90 file dữ liệu/13 file model không đổi trong lượt smoke (`live-snapshot-real-ssi.json`, `live-snapshot-deployed.json`). Mount data/models vẫn read-only; Live không còn phụ thuộc ghi cache.
- Các sửa training/artifact/data-cutoff/failure-state đã nêu bên dưới. Không bật worker hoặc huấn luyện/promote model sản xuất trên dữ liệu chưa được xác thực.
- Chỉ kiểm tra lại ba cửa sổ nguồn nhỏ để xác nhận điểm nghẽn hiện tại: SSI trả 200 nhưng ClosePriceAdjusted vẫn giảm 48,65% TCB tại 20/06/2024, 31,96% CTG tại 17/12/2025 và 20,25% HDB tại 18/12/2025. `ssi-current-issue-samples.json`, `ssi-current-issue-summary.json` lưu bằng chứng. Phần DATA-REVISION-FINDINGS.md cuối cùng có tham số tái hiện và câu hỏi kỹ thuật dành cho SSI; chưa gửi ra ngoài.
- Không yêu cầu nguồn thứ hai hoặc lịch chia thủ công. Phần chưa thể làm có căn cứ là xác nhận/khôi phục đầy đủ lịch sử giá điều chỉnh để huấn luyện và đánh giá chất lượng trên dữ liệu phù hợp. Cần thông tin semantics/revision hoặc dữ liệu đã chỉnh từ SSI, không thể suy ra chắc chắn từ các bước nhảy giá hiện tại.
- Sự cố cách ly kiểm thử làm mới riêng raw/VIC.parquet đã ghi ở isolated-test-vic-refresh-incident.json. 1.214 dòng giao với snapshot 18/11 khớp OHLCV chính xác; không có hash toàn file ngay trước sự cố nên không khẳng định byte-for-byte nguyên trạng. Sáu artifact baseline vẫn không đổi.

---

## Ràng buộc dữ liệu được người dùng xác nhận

SSI là nguồn giá duy nhất của dự án; người dùng không có nhà cung cấp thay thế hoặc lịch chia cổ phiếu riêng. Không đặt việc bổ sung nguồn thứ hai hay cung cấp lịch thủ công làm điều kiện để tiếp tục sửa phần mềm. Tài liệu FastConnect hiện có DailyOhlc/DailyStockPrice với ClosePriceAdjusted nhưng không liệt kê endpoint lịch corporate action: https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs.

Trong ràng buộc này, hệ thống giữ nguyên giá do SSI cung cấp và kiểm tra chất lượng; không suy đoán hệ số chia cổ phiếu, không coi mọi bước nhảy là lỗi đã xác định. Những dự báo không vượt kiểm tra vẫn hoạt động với giới hạn dữ liệu đã công bố; những lịch sử bị chặn chỉ có thể phục hồi khi lần tải SSI đáp ứng kiểm tra phù hợp. Không khẳng định việc vượt heuristic đồng nghĩa toàn lịch sử đã chính xác hoặc mô hình đạt chất lượng ngoài mẫu.

Phần sửa mới: strict Live refresh kiểm tra lịch sử ngay sau tải/chuẩn hóa và trước atomic-save raw cache. Khi SSI trả chuỗi có bất thường gần đây, yêu cầu bị từ chối và không ghi đè cache. Mạng lỗi cũng không fallback thành công giả. `ssi-refresh-quality-before.txt` lưu test trước sửa; `ssi-refresh-quality-after.txt`: 27 test liên quan đạt. Không thay đổi chính sách đọc giá của trang thị trường hay sửa giá bằng lịch sự kiện tự tạo.

## Kết luận phần trọng tâm hiện tại

**Chưa hoàn tất; đang chờ dữ liệu đầu vào có thể xác minh.** Các sửa trọng yếu đã triển khai: tránh công bố sai trạng thái sau commit model; chặn đầu vào giá bất thường trước suy luận/huấn luyện; ngày chốt panel được lấy mỗi lần build; lỗi/partial khi đồng bộ ngăn training; lỗi xuất panel không được báo success. Không rà lại các phần đã hoàn tất ở đợt trước hoặc mở thêm việc chỉnh giao diện nhỏ.

- Image đang chạy: `sha256:1bb94a1d8b86d1b04b12561eb9ae9a60f80eff053d6a237316e8006382a20aa4`, API healthy. Bằng chứng mới nhất: `core-remaining-blocker.json`, `data-freshness-deployed.json`.
- Kiểm thử cho các thay đổi mới: `core-training-after.txt` (23), `core-api-after.txt` (43), `data-training-freshness-after.txt` (35); các nhóm có phần trùng nhau, không cộng thành số test duy nhất. Fault injection trong container dùng thư mục tạm và nguồn giả, không viết artifact sản xuất.
- Sáu artifact baseline được giữ nguyên. Một bài kiểm thử Live mới thiếu mock đã làm mới raw/VIC.parquet từ SSI; xem isolated-test-vic-refresh-incident.json. Toàn bộ 1.214 dòng OHLCV giao nhau với snapshot 18/11 khớp chính xác; chưa có bản sao đầy đủ ngay trước bài test để khẳng định byte-for-byte toàn file. Không rollback bằng dữ liệu suy đoán. CTG/HDB/TCB bị chặn ở suy luận; GVR/TCB/VNM có sai khác phiên bản dữ liệu. SSI hiện tại cũng còn bước nhảy chưa điều chỉnh tại sự kiện đã có thông báo chính thức. Khớp SSI hoặc không vượt ngưỡng 20% không chứng minh dữ liệu đã đúng.
- Vẫn thiếu một chuỗi giá điều chỉnh hoặc lịch corporate action đầy đủ, có provenance để xác định các điều chỉnh đã có/chưa có; không tự chia thêm hệ số lên dữ liệu điều chỉnh một phần. Không dùng kết quả quality-reconciled làm chứng nhận chất lượng dữ liệu.
- Data/models đang mount read-only và worker không chạy. Luồng đọc/suy luận không đồng nghĩa luồng live/retrain đã hoạt động. Chưa mở ghi hoặc chạy huấn luyện trên dữ liệu chưa xác thực.
- Bước tiếp theo khi có nguồn phù hợp: đối chiếu trên bản sao → tạo snapshot có hash/provenance → kiểm chứng lại feature/nhãn và đánh giá ngoài mẫu → kiểm tra live/retrain trong môi trường ghi riêng → cập nhật sản xuất có rollback. Không lặp lại các mục giao diện/test cũ không liên quan.

---

**Ưu tiên hiện tại theo yêu cầu mới:** chỉ xử lý các lỗi trọng yếu còn mở; không lặp lại rà soát và chỉnh sửa nhỏ đã hoàn tất.

Mục tiêu còn đang thực hiện. **Phát hiện mới quan trọng: cache GVR/TCB/VNM khác lịch sử giá điều chỉnh SSI và có thể làm đổi tín hiệu. Đọc DATA-REVISION-FINDINGS.md.** Không coi bộ test xanh là bằng chứng toàn bộ kế hoạch đã đạt.

| Phạm vi | Bằng chứng đã có | Hạng mục cần xác minh tiếp |
|---|---|---|
| A. Luồng và hợp đồng | DATA-CONTRACT.md: từng trường UI, nguồn ưu tiên, đơn vị/ngày/fallback; live-api.json đối chiếu single/batch và GET/POST; deployment-final-current.json ghi OpenAPI cả hai prefix từ image cuối; served-log-context.json đối chiếu response với log generation | Log liên kết bằng symbol/model/date/generation đã kiểm chứng bằng response phục vụ thực |
| B. Frontend | DashboardApp.audit.test.tsx: response sai thứ tự, retry, không giữ nến cũ, không tải history trùng. predictionAudit.test.ts: dữ liệu sai. storage/accessibility tests: quota, blocked storage, trap/restore focus. e2e-remaining.json: hai tài khoản, lỗi 503 và retry | Chrome native đã xác nhận 200% và reset 100%; còn tương tác đầy đủ ở từng breakpoint, ảnh bằng chứng lưu thành file và rà soát độ tương phản |
| C. Biểu đồ | Trajectory helper từ chối thiếu/sai ngày/giá; E2E thấy T và ba bước khớp bảng; toggle và 6M. Canvas [7,7,7]. chart-lifecycle.txt: 4 chart instances được remove đúng một lần, 4 resize handler đều gỡ, recreated chart nhận lại đủ dữ liệu; toggle không fitContent lại | Pan/zoom trực tiếp đã kiểm tra và sửa nhãn T+3; heap thư viện chưa đo được (raw CDP Memory.getDOMCounters không hỗ trợ). Mock lifecycle chứng minh cleanup của component, không đo bộ nhớ trong thư viện/browser |
| D. API/quyền | api-calendar-final.txt: 250 passed, 1 skipped. permissions-readiness.txt: anonymous/user/admin/inactive/worker. live-api.json trên image cuối: 60 dự báo/0 lỗi; GET/POST và single/batch khớp | Test skipped là concurrent password reset cần PostgreSQL độc lập (ngoài tab dự báo), không phải test dự báo bỏ qua; chưa dùng SQLite để xác nhận cạnh tranh transaction PostgreSQL |
| E. Dữ liệu | data-model-audit.json: 30 mã, OHLCV, causal feature; raw-panel-reconciliation.json: Close khớp trên overlap; calendar-data-reconciliation.json: không có nến ngày nghỉ 2026 | Đã đối chiếu 36.420 ngày/mã với SSI adjusted close: 27 mã khớp, GVR/TCB/VNM có 3.568 sai khác. Bản sao đã đối chiếu riêng; cache đang phục vụ chưa thay. Xem DATA-REVISION-FINDINGS.md |
| F. Mô hình/artifact | Test scaler/tensor/class mapping, atomic bundle 75 reads/5 publishes; cached fallback có generation/degraded; early stopping thực. Sparse purge theo từng mã: 26 test liên quan đạt; full ML mới nhất 149 passed | Artifact legacy thiếu provenance train/validation đầy đủ; không được dùng metric metadata làm test độc lập. Không retrain/promote model sản xuất |
| G. Chất lượng | quality-early-stopping/summary.json: 3 fold/1.800 mẫu, baseline, macro-F1, từng lớp/mã/fold, calibration/log loss/Brier/AUC. sparse-purge-evaluation-compatibility.json: mask không đổi cả 3 fold | quality-reconciled/summary.json là đánh giá mới sau đối chiếu: accuracy LGB 47,11%, LSTM 43,11%, baseline 58,56%; không tuyên bố ưu thế đầu tư. Snapshot cũ chỉ giữ để truy vết |
| H. Vận hành | http-load.json: 1/5/10 đồng thời trên API riêng, 0 lỗi. worker-container-smoke.json: worker thực trong container riêng với fixture 200/503. operations-current.json báo worker_not_running dù HTTP healthy. Kiểm tra stale date, stale/degraded/missing metadata bằng test. served-log-context.json xác nhận log production có mã/model/ngày/generation/thời gian | http-load-resources.json đã đo CPU/RSS theo mức tải. Worker sản xuất hiện không chạy, chưa xác nhận lần chạy lịch tiếp theo. Benchmark hữu hạn, không khẳng định SLA hoặc tải liên tục; không tự tạo lịch giám sát mới |

## Kết quả chạy lại sau khi tiếp tục

- `ml-final-current.txt`: 149 passed, 2 warnings; có sparse-symbol purge regression.
- `web-final-current.txt`: 206 passed, 1 timing failure (53 ms so với ngưỡng 50 ms ở bài backtest ngoài tab dự báo) khi build/test cùng chạy. Giữ nguyên log thất bại để truy vết.
- `web-final-rerun.txt`: 207 passed khi chạy lại. Chưa sửa ngưỡng test để che lỗi; phép đo nhạy tải máy vẫn là hạn chế.
- `typescript-final-current.txt` và `eslint-final-current.txt`: lệnh hoàn tất với exit code 0, log rỗng.
- `docker-build-final.txt`: image sha256:29271c814668609d3ff44bb9f2ab6f1ad900559ec5570c68eb8a93fbd145ed16. Docker kẹt lúc start (container created/PID 0); Docker Desktop restart phục hồi, không xóa volume. `deployment-final-current.json`: /health healthy, đúng image/generation, lịch 2026 true, data_quality unverified. `live-final-current.txt`: 60 predictions, 0 failures. Snapshot docker stats lúc smoke: API 155,53% CPU / 447,6 MiB; đây chỉ là một mẫu, không phải profile tải.
- `production-artifact-preservation.json` đã kiểm tra lại: 6 file so với baseline, changed=[], không promote các fold đánh giá.
- Browser môi trường riêng: token cũ hết hạn có warn 401; sau phục hồi vào đúng tài khoản Audit Two. Request VIC ban đầu bị timeout 30s; Thử lại khôi phục tín hiệu, nến và T+1/2/3 với lịch nghỉ 2026. Không đồng nhất lỗi timeout với xác suất 0%.

## Kiểm chứng vận hành bổ sung

- `log-context-before.txt`: test thể hiện thiếu log liên kết thất bại trước sửa. `log-context-after.txt`: 17 test API đạt sau thêm log thành công gồm symbol, model_type, data_as_of_date, artifact_generation, serving_status, elapsed_ms; lỗi suy luận có cả mã và model. Chỉ log các trường cho phép, không log token/header/payload người dùng.
- Sau restart API, request HPG/LSTM thực khớp log với response: generation 71d398842a1f2650, ngày 20/11, status healthy. API/DB healthy. Thay đổi service nằm trong bind mount; image hash không chứng minh nội dung service mới, vì vậy dùng log request phục vụ thực làm bằng chứng.
- `infra-operations-final.txt`: 41 passed. `prediction_operations.py` chỉ đọc /health, signal của VIC/HPG × hai model và danh sách tên container. Báo stale data, degraded artifact, timestamp thiếu/sai/tương lai/quá ngưỡng 8 ngày và worker vắng mặt. Ngưỡng 8 ngày là chính sách kiểm tra vận hành công khai, không phải kết luận chất lượng mô hình.
- `worker-container-smoke.json`: hai container dùng worker script thật, test secret riêng, API fixture cục bộ. HTTP 200 → exit 0; HTTP 503 → exit 1. Đúng endpoint/payload/auth header; không gửi retrain vào API sản xuất.
- `chart-lifecycle.txt`: 2 test đạt; `typescript-lifecycle.txt` và `eslint-lifecycle.txt`: exit 0. Đây là bổ sung sau mốc toàn bộ frontend 207 test, chưa chạy lại cả suite với hai test mới.

Lệnh kiểm tra vận hành từ root:

```sh
PYTHONPATH=apps/ml apps/ml/.venv/bin/python scripts/audit/prediction_operations.py --output reports/prediction-audit-2026-11-20/operations-current.json
python scripts/audit/prediction_worker_smoke.py
PYTHONPATH=apps/api apps/api/.venv/bin/python -m pytest infra/tests -q
```

## Sparse purge

Nhãn dùng ba quan sát tiếp theo của từng mã. Purge theo ba ngày cuối toàn thị trường có thể bỏ sót mã thiếu phiên. Bản sửa gán sentinel cho ba quan sát cuối từng mã, giữ hàng feature để warmup LSTM. Fixture sparse tái hiện lỗi cũ; regression đã đạt. Trên snapshot đánh giá hiện tại, cả ba fold có cùng purge mask trước/sau sửa, nên không cần suy diễn metric mới từ một tập dữ liệu khác.

## Zoom, pan và độ chính xác nhãn — vòng tiếp theo

- Chrome native tài khoản Audit Test, localhost:3001: điều khiển browser hiển thị “Thu phóng: 200%”; xem được controls xuống dòng và nến/đường minh họa. Reset qua nút Đặt lại, xác nhận 100%. Không dùng IAB viewport hẹp làm bằng chứng zoom thật.
- Phát hiện nhãn T+3 232,05 trong khi bảng là 232.070 VNĐ: formatter chung lấy minMove=0,05 của nến. Đổi sang độ chính xác 0,01, quan sát sau sửa nhãn 232,07 khớp bảng. Không thay công thức giá minh họa hoặc kết quả suy luận.
- Pan/zoom trực tiếp trong IAB bằng mouse wheel và drag: thu/phóng thay vùng ngày; kéo sang lịch sử đẩy T+3 khỏi màn hình. Phát hiện last-value label của thư viện bám điểm cuối đang nhìn thấy nhưng còn title T+3. Đổi thành custom price line gắn đúng giá T+3; tắt last-value label của hai series minh họa. Sau sửa, kéo T+3 ra khỏi màn hình vẫn giữ nhãn 232,07, không nhảy sang giá T+1 238,58. Toggle ẩn cả đường và marker, giữ vùng ngày; 1M phục hồi điểm tương lai.
- chart-target-marker.txt: 3 test đạt gồm marker thay thế khi đổi dự báo, chart/resize cleanup và toggle không fitContent. typescript-target-marker.txt đạt. Bộ web cuối web-marker-final.txt đạt 210/210; TypeScript và ESLint đạt.
- API full trước sửa logging migration: 250 passed, 1 failed, 1 skipped. Test đơn lẻ đạt nhưng full suite lộ Alembic fileConfig vô hiệu hóa logger đã tồn tại. Đổi disable_existing_loggers=False; regression migration → log-context liên tiếp đạt (migration-log-isolation.txt). Không đổi production model.
- http-load-resources.json: từng model 1/5/10 đồng thời, 0 lỗi. Mức 10: LightGBM p95 0,830s, RSS mẫu đỉnh 284,1 MiB, CPU bình quân 3,37 lõi; LSTM p95 0,500s, RSS 422,9 MiB, CPU 1,55 lõi. CPU là delta user+system chia wall-time; RSS lấy mẫu 50ms. Mức 1 chỉ có hai mẫu RSS nên không coi là profile ổn định.
- Xuất screenshot thành file chưa thành công: clipboard của IAB không trở thành ảnh clipboard native của Preview. Đã khôi phục clipboard kiểm thử rỗng; chưa có ảnh file để gắn vào báo cáo. Ảnh quan sát hiện nằm trong tool output, không đánh dấu đạt deliverable ảnh lưu trữ.
- DEPLOYMENT-RUNBOOK.md ghi rõ image rollback không hoàn tác source bind-mount và không có snapshot source ban đầu đầy đủ để tự động rollback toàn bộ worktree. current-tracked.patch lưu diff tracked hiện tại, không phải bản sao ban đầu và không chứa file untracked.

- api-log-migration-final.txt: 251 passed, 1 skipped, 7 warnings sau sửa logger của migration. Test skipped vẫn là concurrent password reset cần PostgreSQL, không phải test dự báo.
- Đã dừng API/frontend riêng 8001/3001 sau kiểm tra; API Docker 8000 và database tiếp tục healthy. Sáu hash artifact production tiếp tục không đổi.

## Khả năng truy cập và dữ liệu nguồn — cập nhật mới

- probability-help-before.txt tái hiện nút trợ giúp không có tên truy cập; nội dung còn ghi cứng 1,5% trong khi artifact có threshold=0,02. Đã đọc ngưỡng metadata, ghi rõ lớp ≥ +ngưỡng / ≤ −ngưỡng; khi thiếu thì không tạo ngưỡng giả. Nút có tên, aria-expanded, aria-controls, vùng bấm/focus rõ. Giải thích phân biệt xác suất với accuracy.
- contrast-measurements.json: 117 text nodes ở trạng thái dự báo có dữ liệu, 4 lỗi trước sửa; sau sửa không còn lỗi trong scan. LightGBM 3,665→5,367; sàn/volume 3,857→6,996; SMA50 tắt 2,189→7,675. Không coi scan này là chứng nhận WCAG toàn hệ thống.
- responsive-keyboard.json: 390/768/1280/1920px đều thao tác Enter chọn SMA50/1M, mở trợ giúp, mở/đóng model dialog bằng Escape, đổi hai model và nhận trajectory hợp lệ. Không tràn ngang document; focus nằm trong dialog; canvas count 7. Đã reset viewport.
- web-a11y-threshold-final.txt: 211 passed; TypeScript/ESLint đạt. ml-strict-refresh-full.txt: 151 passed. api-strict-refresh-full.txt: 252 passed, 1 skipped.
- Image strict refresh sha256:755d293c777c12ef9a830a9a48da81d23e9c641b00d5427aaf902ae7586a26d0 đã chạy healthy; live-strict-refresh-smoke.txt: 60 dự báo, 0 lỗi đối chiếu hợp đồng. Điều này không chứng minh cache lịch sử đúng, xem phát hiện dữ liệu mới.
- DATA-REVISION-FINDINGS.md và quality-reconciled/ ghi rõ giới hạn và phần còn mở; không promote model thử hoặc ghi đè dữ liệu giá sản xuất.


## Cập nhật nguồn dữ liệu và giới hạn nghiệm thu 22/11

- Dữ liệu SSI mới không phải bản sửa chuẩn: TCB hiện còn bước nhảy chưa điều chỉnh tháng 6/2024, còn cache có bước nhảy tháng 10/2026. Không promote bản tải lại; xem DATA-REVISION-FINDINGS.md và tcb-action-reference-evidence.json.
- Các metric trong quality-reconciled chỉ là thí nghiệm độ nhạy với phiên bản dữ liệu, không chứng nhận chất lượng trên dữ liệu đã xác thực.
- Guard suy luận chặn Close không hợp lệ/bước nhảy >20% trong ngữ cảnh gần đây, trả lý do 503 an toàn. Ngưỡng này là heuristic cần kiểm tra, không tự sửa giá hoặc chứng nhận các mã không bị chặn. 156 test ML và 57 test API liên quan đạt.
- Các smoke 60/60 cũ thuộc image trước guard; không dùng làm bằng chứng rằng mọi mã hiện đều được phép dự báo. TCB phải bị từ chối minh bạch cho đến khi có dữ liệu đáng tin cậy.


## Sửa trọng tâm về công bố model — 22/11

- Trước sửa, training commit manifest rồi ghi nhiều bản sao legacy; lỗi ghi sau commit khiến API báo thất bại dù model mới đã phục vụ. Nay commit bundle là kết quả công bố; lỗi xuất bản sao được ghi log và trả `artifact_publication.compatibility_export_failures`, không giả vờ rollback. Generation trả về là generation của chính lần publish, không đọc lại manifest có thể đã bị publisher khác thay.
- Feature importance được ghi cùng generation. Wrapper LSTM ưu tiên artifact trong bundle, không đọc bản sao legacy cũ nếu xuất bản sao thất bại. Legacy loose files vẫn là bản xuất tương thích, không có cam kết atomic nhiều file; pipeline/API chính phải dùng manifest.
- Trước fitting, production trainer kiểm tra toàn bộ khoảng nghiên cứu cho từng mã và từ chối lịch sử Close không hợp lệ/bước nhảy trên ngưỡng rà soát. Đây là chặn đầu vào đáng ngờ, chưa thay thế việc xác thực điều chỉnh corporate action.
- `artifact-export-before.txt` và `training-price-guard-before.txt` lưu tái hiện trước sửa; `core-training-after.txt`: 23 passed. Không huấn luyện lại hoặc thay sáu artifact sản xuất; kiểm tra hash vẫn changed=[].
- Guard suy luận đã kiểm chứng trên Docker image 7880e271: VIC/HPG × hai model trả 200; TCB × hai model trả 503 đúng lý do/ngày. `price-guard-deployed.json` lưu response tóm tắt. Image chứa thêm sửa publication đang được cập nhật, không đồng nhất bằng chứng image cũ với image sau.


## Xác minh image phục vụ sau sửa trọng tâm

- `core-training-deployed.json`: image `sha256:0833dbcb249f0c4dd8c8c79edf867bea5767324573e0b4a813dc5c775a3fde83`, container healthy. Batch VIC/HPG/TCB có hai kết quả hợp lệ và lỗi 503 riêng cho TCB, không sinh dự báo thay thế.
- `core-api-after.txt`: 43 test API service/audit đạt, gồm từ chối retrain với lý do dữ liệu an toàn.
- `core-container-smoke.txt`: trong container đang phục vụ, thử lỗi xuất alias trên thư mục tạm vẫn resolve được bundle đã commit; từ chối retrain khi đầu vào bị chặn. Không gọi training thật trên dữ liệu/artifact sản xuất.
- Docker từng kẹt ở trạng thái created/PID 0 khi recreate; restart Docker Desktop rồi start lại phục hồi. Không xóa volume. API/DB hiện chạy lại; không khởi động worker sản xuất hoặc đổi mount read-only.
- Phần chưa giải quyết trọng yếu: nguồn điều chỉnh/corporate-action đáng tin cậy cho các lịch sử đang có sai khác; sau đó mới có cơ sở phục hồi dữ liệu, đánh giá lại và mở lại luồng ghi/live/retrain sản xuất. Guard không thay thế bản sửa dữ liệu này.


## Phạm vi guard thực tế trên 30 mã

`core-batch-coverage.json`: mỗi mô hình có 27 kết quả, 3 lỗi 503 riêng theo mã; tổng kết quả + lỗi khớp đủ 30 mã yêu cầu, xác suất hợp lệ và trajectory đủ ba bước ở các kết quả trả về. Những lịch sử bị chặn: CTG tại 17/12/2025, HDB tại 18/12/2025, TCB tại 29/10/2026. `price-history-review-required.json` lưu lý do cùng các nến trước/tại/sau sự kiện và mức thay đổi Close. Chưa gán nguyên nhân corporate action cho CTG/HDB khi chưa có chứng từ đối chiếu. Việc 27 mã khớp ClosePriceAdjusted hiện tại không chứng minh SSI đã điều chỉnh đầy đủ các sự kiện.


## Lỗi dùng ngày chốt cũ và tiếp tục train sau đồng bộ lỗi — 22/11

- `build_panel_dataset` trước sửa bind DEFAULT_END_DATE lúc import. Tiến trình sống qua nhiều ngày vẫn có thể tải/lọc panel về mốc cũ dù đã đồng bộ phiên mới. Nay end_date mặc định None và được chốt đúng một lần mỗi lần build; stock, index và coverage cùng dùng mốc đó. Ngày được truyền tường minh vẫn giữ nguyên.
- Production trainer trước sửa nuốt exception đồng bộ, bỏ qua status partial rồi vẫn tải panel để huấn luyện. Nay exception hoặc partial/errors dừng trước fitting và công bố artifact. Trường hợp cung cấp raw_panel trong môi trường đánh giá riêng vẫn không gọi mạng.
- Đồng bộ trước sửa có thể trả success khi xuất panel thất bại. Nay ghi lỗi panel vào errors và trả partial; trainer không nhận trạng thái đó làm đầu vào thành công.
- Tái hiện: dynamic-cutoff-before.txt, training-sync-before.txt, panel-sync-status-before.txt. Sau sửa: data-training-freshness-after.txt, 35 passed. Các kiểm thử đều dùng dữ liệu/mạng giả trong môi trường riêng, không sửa dữ liệu sản xuất.
- CTG/HDB đã có nguồn chính thức xác nhận sự kiện đúng ngày bị chặn; nguồn và giới hạn kết luận được ghi tại DATA-REVISION-FINDINGS.md. SSI vẫn có bước nhảy trong ClosePriceAdjusted và RefPrice không phản ánh điều chỉnh ở hai ngày đó. Chưa tự sửa chuỗi điều chỉnh một phần hoặc mở lại các dự báo đang bị chặn.


Xác minh triển khai phần ngày chốt/sync: image `sha256:1bb94a1d8b86d1b04b12561eb9ae9a60f80eff053d6a237316e8006382a20aa4`, API healthy (`data-freshness-deployed.json`). Thử trong container với nguồn và thư mục tạm: cutoff thay đổi theo từng call; panel publish lỗi trả partial; sync exception/partial dừng training trước build/fitting (`data-freshness-container-smoke.txt`). Không tạo artifact sản xuất; sáu hash baseline không đổi. Không lặp lại kiểm tra giao diện hoặc các mục trước đã hoàn tất.


## Bổ sung sau ràng buộc SSI duy nhất

Strict refresh nay chặn lịch sử SSI đáng ngờ trước raw-cache write, và service Live giữ lý do chất lượng riêng thay vì biến thành lỗi kết nối chung. `ssi-refresh-quality-after.txt`: 27 test ML liên quan đạt; `ssi-live-quality-reason-after.txt`: 22 test API audit đạt. `ssi-refresh-quality-container.txt` kiểm tra fault injection trên đúng container, không gọi vendor hoặc viết artifact sản xuất. Image triển khai `sha256:2227adf14cb719bf70b82d64129c00886d89520216b84a85eaedb3e896c1453d`, API health đạt, sáu artifact baseline không đổi (`ssi-refresh-quality-deployed.json`). Không tuyên bố đã sửa được các giá lịch sử chưa đủ căn cứ, không yêu cầu người dùng bổ sung nguồn giá khác.


## Luồng Live không cần ghi cache

Lỗi trọng yếu: trước đây service tải SSI rồi dự báo lại từ global panel/cache; Docker mount read-only khiến Live thất bại khi ghi hoặc có nguy cơ dự báo từ lịch sử khác phiên bản vừa tải. Nay Live fetch cả stock và VNINDEX với save_to_raw=False, đóng gói request-local panel và truyền trực tiếp vào predict_trend/prepare_inference_features qua raw_snapshot tùy chọn. Có snapshot thì không đọc panel cũ hoặc fallback/tải lại. Luồng dự báo thường giữ cách đọc cũ.

Price rolling features vẫn dùng toàn lịch sử stock. VNINDEX chỉ cần đóng cửa cho seq_length+1 phiên gần nhất để tính đủ seq_length lợi suất; không tải lại nhiều năm index cho mỗi request. Các dòng cũ chưa có market return để NaN, tính rolling price trước rồi loại dòng thiếu feature; test so sánh cửa sổ 20 feature cuối khớp chính xác với cách dùng toàn bộ lịch sử index. Không điền thiếu thành 0.

Từ chối snapshot sai mã, trùng ngày, index thiếu phiên/giá không hữu hạn hoặc không đủ ngày chốt. `source_provenance=SSI_request_snapshot`, historical_adjustment_status vẫn unverified. is_live_synced xác nhận dữ liệu mới đã được dùng cho yêu cầu, không hàm ý cache đã được ghi.

Test: live-snapshot-before.txt (7 lỗi thể hiện thiếu luồng snapshot); live-snapshot-after.txt (8 đạt, gồm parity feature); live-snapshot-ml-after.txt (29 đạt trước khi bổ sung test bounded-market); live-snapshot-api-focused.txt (29 đạt). Lượt API rộng bị dừng sau 49 test đạt vì nhánh fixture cũ chỉ có Date đã đi vào tải VNINDEX toàn lịch sử trước khi kiểm tra độ dài được bổ sung; log live-snapshot-api-after.txt giữ trạng thái interrupted, không tính là lượt kiểm thử hoàn tất. Chỉ chạy nhóm liên quan sau sửa; không rà lại UI hoặc các hạng mục cũ.

Sự cố cách ly test: lượt test service ban đầu chưa mock fetch_stock_data đã ghi lại VIC từ SSI trước khi bị dừng; đã khóa nhánh đó bằng mock raise, bổ sung test live consumes request snapshot. Không chạy training; không tuyên bố toàn bộ file giá giữ nguyên. Bằng chứng đối chiếu OHLCV và giới hạn tại isolated-test-vic-refresh-incident.json.


## Kết quả Live trong Docker với SSI thật

- Hai file Compose trước sửa không đưa SSI_CONSUMER_ID/SSI_CONSUMER_SECRET vào container; cả hai biến chưa cấu hình trong runtime dù host có credentials. Nay khai báo qua environment, không build args hoặc copy .env vào image. `docker-ssi-config-before.txt`: 2 lỗi tái hiện; `docker-ssi-config-after.txt`: 2 test đạt; kiểm tra chỉ xuất boolean xác nhận credentials được cấp, không log giá trị.
- `live-snapshot-real-ssi.json`: VIC × LightGBM/LSTM và HPG × LightGBM/LSTM đều trả được Live bằng snapshot thật; cùng ngày 20/11/2026, đúng giá mới nhận, trajectory ba bước, xác suất hợp lệ. Thời gian từng request 11,104 / 12,059 / 10,029 / 9,290 giây. Đây là 4 lần đo, không cam kết SLA.
- Hash toàn bộ 90 file data và 13 file model trước/sau **lượt smoke này** khớp; data/models vẫn read-only. Điều này không xóa sự cố refresh VIC ở bài test trước (đã ghi riêng).
- Service được gọi trong container đang phục vụ; không tuyên bố đã dùng phiên đăng nhập HTTP sản xuất cho lượt này. `live-snapshot-api-http.txt`: 28 test API audit đạt, gồm GET/POST cả hai prefix với dependency tài khoản được cô lập và cùng snapshot được truyền vào suy luận. Quyền truy cập HTTP đã kiểm tra ở các vòng trước, không thay đổi/chạy lại toàn bộ UI.
- stderr của smoke ghi warning scaler được lưu bằng sklearn 1.7.2, runtime 1.9.1; lượt suy luận thành công không phải chứng nhận tương thích mọi artifact hoặc chất lượng mô hình. Không tự nâng/retrain artifact để xóa warning.
- Còn hạn chế nguồn SSI giá điều chỉnh đã mô tả; không yêu cầu người dùng tìm nguồn giá khác. Worker/retrain sản xuất chưa bật hoặc mở quyền ghi trên dữ liệu chưa được xác thực. Không dùng Live thành công để tuyên bố lịch sử đã hết lỗi.


Theo yêu cầu mới, tính đầy đủ/chính xác của điều chỉnh lịch sử từ SSI được phân loại là hạn chế phụ thuộc nhà cung cấp trong phạm vi nguồn SSI duy nhất. Đã rà tài liệu công khai; chưa có hợp đồng điều chỉnh/revision đủ rõ để tự xác thực toàn lịch sử. Không khẳng định SSI không cung cấp qua kênh riêng, chưa có phản hồi trực tiếp. Xem mục cuối DATA-REVISION-FINDINGS.md. Các lỗi tải/ghép/đổi đơn vị của ứng dụng vẫn thuộc trách nhiệm phần mềm, không gộp vào hạn chế này.


Xác minh hoàn tác: ssi-limitation-rollback-ml.txt 25 test đạt; ssi-limitation-rollback-policy.txt 3 regression đạt (chấp nhận bước nhảy nguồn mà không tự sửa/chặn ở inference, refresh, training); ssi-limitation-rollback-api.txt 46 test đạt. Container cập nhật; CTG/HDB/TCB × LightGBM/LSTM đều trả 200 (ssi-limitation-rollback-deployed.json). Sáu artifact baseline không đổi; không chạy retrain hoặc tự điều chỉnh giá.
