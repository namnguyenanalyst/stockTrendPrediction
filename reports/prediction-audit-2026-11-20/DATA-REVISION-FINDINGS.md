# Sai khác giá lịch sử — phát hiện 21/11/2026

**Chưa nghiệm thu dữ liệu đang phục vụ.** Có sai khác có thể làm đổi tín hiệu; bộ test xanh và smoke 60 dự báo không chứng minh lịch sử giá đã đúng với nguồn hiện tại.

## Phạm vi và kết quả

Đối chiếu toàn bộ 36.420 dòng của snapshot đánh giá (30 mã, 04/01/2022–18/11/2026) với `DailyStockPrice.ClosePriceAdjusted` của SSI. Dung sai 0,011 nghìn VNĐ. Tất cả ngày đều có tham chiếu, không có adjusted close thiếu/không dương. 32.852 dòng khớp; 3.568 dòng sai khác tập trung tại:

| Mã | Số dòng không khớp / 1.214 dòng | Trong đó local khớp raw nhưng khác adjusted |
|---|---:|---:|
| GVR | 1.164 | 243 |
| TCB | 1.199 | 269 |
| VNM | 1.205 | 92 |

27 mã còn lại khớp adjusted close ở toàn bộ ngày được kiểm tra. Kết quả này chỉ xác minh close, không chứng nhận toàn bộ corporate-action provenance hoặc OHLC/volume.

`ssi-adjustment-reconciliation.json` lưu cửa sổ đã kiểm tra từng mã và ví dụ giá; `ssi-adjustment-summary.json` tổng hợp. Lượt đầu bị từ chối vì khoảng ngày dài; lời đáp SSI xác định giới hạn tối đa 30 ngày. Lượt sau chia cửa sổ 30 ngày, lưu tiến trình và dừng khi gặp lỗi, không làm mờ lỗi thành kết quả rỗng.

Đã kiểm tra chéo DailyOhlc cho GVR/TCB đầu năm 2022: giá hiện trả về khớp mức điều chỉnh của DailyStockPrice, khác cache. Ví dụ TCB 04/01/2022: local 24,045; DailyOhlc hiện tại 33,935; DailyStockPrice adjusted 33,93503 nghìn VNĐ. Đây là sai khác dữ liệu đầu vào, không phải do định dạng VNĐ/nghìn VNĐ.

SSI mô tả trường `ClosePriceAdjusted` là giá đóng cửa điều chỉnh trong [API Specs](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs). Nguồn hiện tại là tham chiếu đối chiếu, không phải biên bản chứng minh nguồn và thời điểm tạo cache cũ.

## Nguyên nhân đã xác định và giới hạn kết luận

- Cache được chấp nhận dựa trên khoảng ngày. Nếu đủ ngày, `fetch_stock_data` trả cache; nếu thiếu phiên, nhánh incremental chỉ nối từ phiên sau ngày cuối. Hai nhánh không kiểm tra việc nhà cung cấp điều chỉnh lại giá quá khứ.
- Đã xác nhận cache khác dữ liệu SSI đang trả về. Chưa có lịch sử ingest/provenance để xác định chính xác cache sai do nguồn ban đầu, lần điều chỉnh nào, hay thời điểm nào. Không tự gán nguyên nhân cho một sự kiện chia tách/cổ tức cụ thể chưa được xác minh.
- Nhánh huấn luyện hiện gọi đồng bộ/build panel với force=False; việc retrain không tự chứng minh lịch sử cũ đã được đối chiếu lại.
- Container hiện mount data/models read-only. Có thể đọc/suy luận nhưng thao tác cần ghi dữ liệu/artifact bị giới hạn. Chưa đổi mount hoặc chạy retrain sản xuất trong audit.

## Tác động đã đo trên bản sao

Giữ nguyên model/scaler/generation và ngày 18/11/2026, chỉ thay dữ liệu GVR/TCB/VNM bằng lịch sử DailyOhlc tải riêng:

| Mã/mô hình | Lớp trước → sau | Tín hiệu trước → sau | Chênh xác suất lớn nhất |
|---|---|---|---:|
| GVR/LightGBM | Tăng → Tăng | Mua → Mua | 0,34 điểm % |
| GVR/LSTM | Tăng → Tăng | Mua → Mua | 0,55 điểm % |
| TCB/LightGBM | Tăng → Đi ngang | Mua → Nắm giữ | 15,30 điểm % |
| TCB/LSTM | Đi ngang → Đi ngang | Nắm giữ → Nắm giữ | 3,96 điểm % |
| VNM/LightGBM | Tăng → Đi ngang | Mua → Nắm giữ | 11,69 điểm % |
| VNM/LSTM | Đi ngang → Đi ngang | Nắm giữ → Nắm giữ | 0,43 điểm % |

`data-revision-inference-impact.json` chứa giá/xác suất/generation trước/sau. Không dùng thí nghiệm cùng model này để kết luận mô hình mới tốt hơn.

Trên cửa sổ nghiên cứu, mỗi mã có 903 mẫu sau warmup/horizon. GVR đổi 5 nhãn, TCB 8, VNM 5; feature thay đổi ở 903 mẫu của từng mã. 27 mã còn lại không đổi feature/nhãn theo phép đối chiếu. Bằng chứng: `data-revision-feature-label-impact.json`.

## Đánh giá độ nhạy ngoài mẫu trên dữ liệu SSI hiện trả về

Đây là thí nghiệm độ nhạy với phiên bản dữ liệu đầu vào, **không phải kết quả trên bộ giá đã được xác thực đầy đủ**. SSI hiện trả về cũng còn bước nhảy TCB chưa điều chỉnh ở 20/06/2024. Ba fold cùng cấu hình, mốc thời gian, seed và baseline như lần trước; không tuning trên test và không promote artifact.

| Mô hình | Mẫu test | Accuracy | Macro-F1 | Log loss | Brier đa lớp |
|---|---:|---:|---:|---:|---:|
| LightGBM | 1.800 | 47,11% | 0,3945 | 1,0739 | 0,6482 |
| LSTM | 1.800 | 43,11% | 0,3633 | 1,0826 | 0,6518 |
| Baseline prior train/argmax | 1.800 | 58,56% | 0,2462 | Xem summary | Xem summary |

Kết quả đầy đủ tại `quality-reconciled/summary.json`, gồm từng mã/fold, calibration, AUC và bootstrap theo ngày. Accuracy hai model thấp hơn baseline; macro-F1 cao hơn baseline. Không suy ra lợi nhuận đầu tư. Các giới hạn survivor bias, nhãn T+3 chồng lấn và dữ liệu point-in-time chưa đủ provenance vẫn áp dụng.

## Sửa đã thực hiện và phần còn mở

- Live trước đó có thể gọi fetch trả cache đủ ngày rồi báo `is_live_synced=True`. Đã thêm `require_fresh` nội bộ: buộc lấy lại toàn lịch sử và không fallback cache khi tải nguồn thất bại. Service live yêu cầu chế độ này; lỗi nguồn/ghi dữ liệu trả lỗi, không báo đồng bộ thành công.
- `strict-refresh-before.txt`, `live-refresh-before.txt` tái hiện trước sửa; sau sửa 16 test ingestion và 18 test prediction audit đạt. Full ML 151 test, full API 252 test đạt (1 auth transaction test skipped như các vòng trước).
- Dữ liệu đối chiếu và model thử nghiệm nằm riêng trong reports. Giá sản xuất và sáu artifact baseline chưa bị ghi đè. Vì vậy sai khác cache đang phục vụ còn là hạng mục mở, không được ghi “đã sửa dữ liệu sản xuất”.
- Còn phải hoàn thiện cơ chế làm mới lịch sử có điều chỉnh, triển khai dữ liệu đã đối chiếu cùng chính sách ghi/rollback phù hợp và kiểm chứng luồng live/retrain thực trong môi trường ghi được. Không chỉ dùng test giả HTTP hoặc /health để xác nhận các mục này.


## Kiểm tra tiếp nguồn SSI — cập nhật 22/11/2026

Không thể xem dữ liệu SSI tải lại là bản sửa chuẩn. Cache TCB có bước giảm 33,28% tại 29/10/2026; dữ liệu SSI hiện trả về bỏ bước đó nhưng lại còn giảm 48,66% tại 20/06/2024. Báo cáo thường niên của tổ chức phát hành xác nhận chia cổ tức cổ phiếu 1:1 tháng 6/2024; thông báo VNX xác nhận tỷ lệ 50% năm 2026. RefPrice SSI tại 29/10/2026 vẫn là 33.500 trong khi ClosePrice 22.350, nên không thể tự suy ra toàn bộ hệ số điều chỉnh chỉ từ RefPrice.

Bằng chứng API đã lưu: `tcb-action-reference-evidence.json`. Nguồn: [Techcombank 2024](https://techcombank.com/nha-dau-tu/bao-cao-thuong-nien/2024/cau-chuyen-cua-tech), [VNX thông báo TCB](https://vnx.vn/vi/thong-tin-thanh-vien/CIMS_TV/637558). Các thư mục `reconciled-data` và `quality-reconciled` giữ tên để truy vết thí nghiệm, không hàm ý dữ liệu đã được chứng nhận.

Chưa áp hệ số tự suy đoán vào giá sản xuất. Cần nguồn điều chỉnh/corporate-action có thể kiểm chứng trước khi thay dữ liệu và đánh giá lại mô hình. Đã thêm chặn suy luận khi lịch sử gần đây có Close không hợp lệ hoặc bước nhảy tuyệt đối trên 20%; đây là ngưỡng yêu cầu rà soát, không phải biên độ pháp lý và không chứng minh dữ liệu dưới ngưỡng đã đúng. Response 503 nêu mã/ngày cần đối chiếu thay vì xuất tín hiệu trên đầu vào đó. Bộ test ML 156 đạt; 57 test API liên quan đạt (`ml-price-guard-restored.txt`, `public-reason-fixed.txt`).


## CTG/HDB: đối chiếu sự kiện chính thức 22/11/2026

- CTG: báo cáo thường niên 2025 trên website VietinBank, phần lịch sử tăng vốn (trang in 126–129), ghi ngày không hưởng quyền 17/12/2025, cổ tức cổ phiếu 44,63658403%. Nguồn: https://investor.vietinbank.vn/documents/20126/32acccd3-8a3d-7828-3cd8-9b47d97eb9b4.
- HDB: HOSE thông báo 2316/TB-SGDHCM ngày 12/12/2025, ngày không hưởng quyền 18/12/2025; cùng ngày thực hiện cổ tức 25% và cổ phiếu thưởng 4,69%. Nguồn: https://staticfile.hsx.vn/Uploads/UploadDocuments/2423661/20251212%20-%20HDB%20-%20TB%20so%202316%20ve%20NDKCC%20tra%20co%20tuc%20bang%20CP%20va%20PHCP%20tang%20VCP%20tu%20NVCSH.pdf.
- Dữ liệu SSI hiện tại vẫn có bước nhảy tại hai ngày đó cả trong ClosePriceAdjusted. CTG 16→17/12: 50.224,80→34.172,56 VNĐ; HDB 17→18/12: 24.691,32→19.691,52 VNĐ. RefPrice ngày sự kiện vẫn bằng ClosePrice ngày trước (51.000 cho CTG, 32.100 cho HDB), nên RefPrice không phải nguồn tự sửa đáng tin cậy ở các trường hợp này. Response giới hạn 15–19/12 đã lưu tại `ctg-hdb-vendor-event-window.json`.
- Đây là bằng chứng chuỗi giá chưa nhất quán qua sự kiện đã được xác nhận, không phải biến động thị trường đã được xác nhận là giảm thật 32%/20%. Không tự áp thêm hệ số lên toàn bộ lịch sử đã được điều chỉnh một phần: cần xác định đầy đủ các điều chỉnh đã có để tránh điều chỉnh hai lần. Chưa đổi dữ liệu hoặc artifact sản xuất.


## Ràng buộc SSI duy nhất

Người dùng xác nhận chỉ có SSI và không có lịch corporate action riêng. Không yêu cầu người dùng tìm nguồn giá khác. Không tự tạo lịch chia hoặc hệ số điều chỉnh để làm dự báo chạy lại. Giữ các trường hợp bất thường ở trạng thái cần kiểm tra dữ liệu nguồn; khi strict live refresh gặp lịch sử bất thường gần đây, kiểm tra trước khi ghi raw cache. Việc SSI cập nhật dữ liệu có thể được tiếp nhận qua đường tải/kiểm tra hiện có; không tự coi nhãn ClosePriceAdjusted là chứng minh đầy đủ tính đúng đắn.


## Mẫu đối chiếu với SSI — kiểm tra lại 22/11/2026

Chỉ đọc ba khoảng nhỏ từ `GET /api/v2/Market/DailyStockPrice`, không ghi cache/model. Cả ba trả thành công nhưng chuỗi ClosePriceAdjusted còn các bước nhảy dưới đây. Response chọn lọc không có token/secret: `ssi-current-issue-samples.json`; phép so sánh: `ssi-current-issue-summary.json`.

| Mã | Hai ngày so sánh | Adjusted close trước → sau (VNĐ) | Thay đổi |
|---|---|---:|---:|
| TCB | 19→20/06/2024 | 32.201,61 → 16.534,16 | −48,6542% |
| CTG | 16→17/12/2025 | 50.224,80 → 34.172,56 | −31,9608% |
| HDB | 17→18/12/2025 | 24.691,32 → 19.691,52 | −20,2492% |

Thay đổi được tính trực tiếp bằng giá sau/giá trước − 1 trong cùng đơn vị nguồn, nên không phải do frontend đổi VNĐ/nghìn VNĐ. Có bằng chứng tổ chức phát hành/sở giao dịch về sự kiện cổ phiếu tương ứng trong các mục trước. Không biến bảng này thành bộ hệ số sửa toàn lịch sử.

Thông tin cần SSI làm rõ để phục hồi dữ liệu theo nguồn duy nhất hiện có:

1. DailyOhlc và ClosePriceAdjusted điều chỉnh những loại quyền nào, theo quy tắc và thời điểm nào? Có phiên bản lịch sử/điểm chốt điều chỉnh hoặc endpoint lịch sự kiện/hệ số dành cho gói đang dùng không?
2. Vì sao ClosePriceAdjusted vẫn có bước nhảy tại ba khoảng ngày trên? Có thể cung cấp phản hồi/hệ số lịch sử đã được xác nhận cho các khoảng này không?
3. Khi lịch sử được backfill, khách hàng cần tải lại toàn bộ hay có dấu mốc revision để nhận biết? Cách lấy OHLC và Volume nhất quán với cùng phiên bản điều chỉnh?

Để tái hiện, dùng access token hợp lệ trong header Authorization (không đưa vào báo cáo), PageIndex=1, PageSize=1000, Market=HOSE, cùng các tham số: TCB FromDate=18/06/2024 ToDate=21/06/2024; CTG/HDB FromDate=15/12/2025 ToDate=19/12/2025. Các khoảng này nằm trong giới hạn 30 ngày đã quan sát. Bản tổng hợp này chỉ được lưu tại repo, chưa gửi cho SSI hoặc bất kỳ bên nào.

Nguồn SSI duy nhất không ngăn việc sửa phần mềm/kiểm tra lỗi và vận hành Live trong bộ nhớ. Tuy nhiên, dữ liệu giá và tỷ lệ thay đổi riêng lẻ không đủ xác định duy nhất toàn bộ điều chỉnh còn thiếu/đã có. Không thể chứng nhận đã sửa giá lịch sử chỉ bằng việc hạ ngưỡng chặn, so với cache cùng nguồn, hoặc tự chia hệ số để đường giá trông liên tục. Phần này chờ phản hồi/điều chỉnh dữ liệu từ SSI, không yêu cầu người dùng tìm một nguồn giá khác hoặc tự lập lịch sự kiện.


## Phân loại hạn chế theo yêu cầu người dùng — 22/11/2026

Đã kiểm tra tài liệu API công khai, chỉ mục FastConnect và change log chính thức SSI. API Specs có trường ClosePriceAdjusted nhưng không mô tả đầy đủ công thức/phạm vi điều chỉnh, chính sách revision/backfill hoặc cơ chế xác minh toàn lịch sử; danh sách FCData công khai không liệt kê endpoint lịch/hệ số corporate action. Change log được đọc không bổ sung hợp đồng đó. Nguồn: https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs ; https://guide.ssi.com.vn/ssi-products/llms.txt ; https://guide.ssi.com.vn/ssi-products/change-log .

Kết luận có giới hạn: chưa tìm thấy thông tin công khai đủ rõ để chứng nhận hoặc tự sửa toàn bộ lịch sử điều chỉnh. Không khẳng định SSI không có tài liệu/gói dữ liệu hoặc giải thích riêng chưa được truy cập; chưa có phản hồi trực tiếp từ SSI. Theo phạm vi chỉ dùng SSI, tính đầy đủ/chính xác của điều chỉnh được ghi là hạn chế phụ thuộc nhà cung cấp, ngoài khả năng kiểm soát trực tiếp của ứng dụng. Phần ứng dụng vẫn phải chịu trách nhiệm tải đúng, đồng bộ đơn vị/ngày, lưu provenance và phát hiện/chặn bất thường; không được quy lỗi phần mềm của ứng dụng thành hạn chế nguồn. Các phép đo chất lượng mô hình và backtest phải công bố hạn chế này.


### Chính sách mới: hoàn tác can thiệp theo biên độ giá

Theo yêu cầu người dùng, đã bỏ cơ chế chặn suy luận/huấn luyện/refresh dựa trên bước nhảy 20% và các 503 riêng cho lịch sử chưa xác minh. Các đoạn ghi guard/chặn trong báo cáo trước đây chỉ còn giá trị truy vết, không mô tả chính sách đang phục vụ. Không áp hệ số sửa giá dựa trên suy đoán corporate action. Dữ liệu SSI là đầu vào duy nhất; hạn chế điều chỉnh được công bố, không tự coi mọi bước nhảy là lỗi. Các kiểm tra cấu trúc, ngày/đơn vị, NaN/Infinity, lỗi mạng và tính đúng của luồng phần mềm vẫn được giữ.
