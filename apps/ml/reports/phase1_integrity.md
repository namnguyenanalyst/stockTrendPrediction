# Đợt 1 sửa tính đúng của pipeline ML và backtest

Ngày thực hiện: 14/11/2026. Nhánh: codex/phase1-ml-quant-integrity. Mốc bắt đầu: 3c26f93. Tệp Word không thuộc phạm vi chỉnh sửa của đợt này.

## Thay đổi đã thực hiện

| Vấn đề tái hiện được | Sửa tại | Kết quả kiểm tra |
|---|---|---|
| Cache inference có nến muộn hơn ngày căn cứ | modeling/predict.py | Cắt dữ liệu theo ngày mục tiêu trước tính đặc trưng; test thay đổi giá tương lai không làm đổi đầu vào quá khứ |
| SHAP dùng đặc trưng chưa scale | features.py, modeling/explain_shap.py | Dùng chung transform_model_features với inference/backtest; kiểm tra tổng SHAP cộng base khớp raw score |
| Model/scaler/metadata có thể bị đọc ở hai lần export khác nhau | modeling/artifacts.py, modeling/predict.py, modeling/train.py | Ghi thư mục phiên bản riêng, SHA-256 và schema; commit bằng một manifest; reload thất bại giữ nguyên cả snapshot cũ |
| Backtest validation tự fit lại scaler, LSTM có nguy cơ chọn sai mã do thứ tự chuỗi theo symbol | backtest.py | Dùng scaler đã lưu; tạo chuỗi riêng từng mã; giữ tên hàm cũ nhưng tên chiến lược là VALIDATION |
| Validation lựa chọn model bị gọi là OOS độc lập | modeling/train.py, modeling/evaluation.py | Metadata ghi rõ vai trò validation; thêm runner temporal holdout tách ngày cutoff và artifact thử nghiệm |
| Cộng weighted validation loss theo số mẫu làm sai mẫu số | modeling/train.py | Tổng weighted cross-entropy chia tổng trọng số nhãn trên tất cả batch |
| Confusion matrix thiếu lớp nếu giai đoạn test không có đủ ba nhãn | modeling/train.py | Luôn dùng thứ tự lớp 0, 1, 2; Macro F1 tính trên ba lớp cố định |
| RS dùng rank trên toàn chuỗi, thay đổi quá khứ khi thêm tương lai | backtest.py | Rank theo expanding history; test tính bất biến khi nối dữ liệu tương lai |
| Backfill và padding giả trong preprocessing backtest AI | backtest.py | Bỏ điền bằng tương lai; không lặp dòng giả để tạo warm-up; lỗi preprocessing không bị đổi âm thầm thành kết quả AI |
| Giá đầu vào kVND nhưng tiền mặt VND | backtest.py | Quy đổi đầu vào từ ingestion sang VND trước khớp lô; giữ nguyên giá trong pipeline features/ML |
| Cho bán Open ngày thanh toán T+2 | backtest.py | Chính sách nến ngày bảo thủ: Open phải sang phiên tiếp theo; Close có thể dùng lô đã về trong ngày |
| Thanh lý cuối kỳ bán cả lô chưa về và bỏ trượt giá | backtest.py | Chỉ bán lô đủ điều kiện; lô chưa về tiếp tục định giá; áp dụng trượt giá và cùng chính sách cho Buy & Hold |
| CAGR dùng sai số khoảng; Sortino khác nhau giữa đơn mã và danh mục | backtest.py | CAGR dùng số khoảng sinh lời; downside deviation lấy toàn bộ kỳ; danh mục gọi cùng calculate_financial_metrics |
| Danh mục gán CAGR bằng ROI, chia phí/thuế theo tỷ lệ giả định, holding cố định | backtest.py | Tổng hợp từ equity chưa làm tròn và trade log thật; đếm thắng/thua, phí, thuế, holding và profit factor từ giao dịch |
| Mã thiếu dữ liệu hoặc khoảng đầu bị backfill làm sai vốn danh mục | backtest.py | Giữ phần vốn chưa dùng dưới dạng tiền mặt, không lấy tài sản tương lai lấp về đầu; khử trùng danh sách mã |

## Quy ước cần biết khi chạy

- simulate_vietnam_trading và run_backtest nhận giá và vốn cùng đơn vị VND. Giá trong fixture đơn vị tự chọn chỉ hợp lệ khi vốn dùng cùng đơn vị đó.
- backtest_symbol_oos và run_portfolio_backtest đọc dữ liệu ingestion theo mặc định price_unit là kVND; chúng quy đổi giá giao dịch sang VND. Nếu gọi bằng dữ liệu tự tạo đã là VND, truyền price_unit="VND" ở hai hàm cấp cao này. Không đoán đơn vị bằng độ lớn giá.
- Kho dữ liệu cũ chưa có metadata đơn vị cho từng tệp. Mặc định kVND bám hợp đồng hiện tại của fetch_stock_data và SSI client; các cache nhập ngoài cần kiểm tra đơn vị trước khi dùng.
- T+2 tính từ ngày mua. Với nến ngày và execution_price="open", chỉ bán từ sáng phiên thứ ba sau ngày mua. Thanh lý Close cuối kỳ là quy ước kết thúc mô phỏng đã định trước, không phải một tín hiệu AI sinh và khớp cùng Close.
- Lệnh bán chưa đủ điều kiện không được tự lưu vô thời hạn; tín hiệu phải còn tồn tại ở phiên được thực thi.
- Tiền bán vẫn được tái sử dụng ngay theo cơ chế hiện có; chưa mô phỏng riêng lịch tiền về, phí ứng trước, bước giá, giới hạn thanh khoản, giá trần/sàn và lệnh không khớp. Không gọi engine là mô phỏng hoàn chỉnh mọi vi cấu trúc.
- Backtest dùng model production chạy ngược lịch sử vẫn là mô phỏng hồi cứu. Chức năng đó không tự có model vintage đúng cho mọi ngày. Runner mới dùng cutoff và artifact riêng để kiểm tra theo thời gian.

## Phiên bản artifact

Mỗi lần train mới tạo một thư mục runs/ với model LightGBM, LSTM, scaler và training metadata. production_bundle_t3.json chỉ được thay sau khi toàn bộ tệp đã ghi xong. Manifest có SHA-256, thứ tự đặc trưng và ánh xạ Symbol_Code. Loader không trộn tệp từ manifest với các tệp loose khi manifest lỗi; nếu đã có cache thì giữ snapshot trước đó.

Các tên tệp production cũ vẫn được xuất để tương thích. Loader ưu tiên manifest; các công cụ ngoài đọc trực tiếp tên loose cần chuyển sang load_prediction_snapshot hoặc load_prediction_artifacts. Bộ production hiện có chưa được huấn luyện lại hoặc thay trọng số trong đợt này. Chế độ đọc legacy vẫn tồn tại khi chưa có manifest; không có bằng chứng hash lịch sử để xác nhận quan hệ giữa các tệp legacy. Cơ chế phiên bản đầy đủ bắt đầu từ lần xuất artifact mới.

Không tự dọn các thư mục runs đang được tham chiếu hoặc còn dùng để tái lập thí nghiệm. Cơ chế này kiểm soát việc công bố nhất quán; không tuyên bố chống mọi tình huống mất điện hoặc thay thế cơ chế backup.

## Kiểm chứng

| Suite | Trước đợt sửa | Sau đợt sửa |
|---|---:|---:|
| apps/ml | 107 | 126 passed |
| apps/api | 175 | 175 passed |
| apps/web | 165 | 165 passed |
| infra/tests | 35 | 35 passed |
| tests/e2e | 87 | 87 passed |
| Tổng | 569 | 588 passed |

87 tests trong tests/e2e được chạy với E2E_FORCE_MOCK=1. Đây là kiểm tra hợp đồng bằng reference mock, chưa phải nghiệm thu trình duyệt và PostgreSQL live. Các cảnh báo LightGBM, Starlette và một số ca kiểm thử adversarial vẫn tồn tại.

Đã kiểm tra Ruff F/I trên các module hiện hữu được sửa và toàn bộ rule áp dụng cho hai module mới artifacts.py/evaluation.py: đạt. Kiểm tra Ruff đầy đủ trên năm module hiện hữu giảm từ 38 xuống 19 chẩn đoán; không tăng số chẩn đoán theo rule. 19 chẩn đoán còn lại thuộc mã cũ, gồm closure trong vòng lặp, catch Exception rộng, datetime không timezone và style/performance. Không tuyên bố toàn repository sạch lint.

Các test mới đã bắt lỗi trước khi sửa đối với bán Open ngày thanh toán, thanh lý lô chưa về, thiếu trượt giá, downside deviation, trật thứ tự tín hiệu, RS nhìn tương lai, số liệu danh mục, đơn vị kVND/VND và cache inference vượt ngày căn cứ. Các test artifact kiểm tra publish thất bại, reload đồng bộ, corruption và đường dẫn manifest.

## Chạy lại kiểm thử

Từ apps/ml:

    uv run pytest -q

Từ apps/api:

    uv run pytest tests -q

Từ gốc repository:

    uv run --project apps/api pytest infra/tests -q
    E2E_FORCE_MOCK=1 uv run --project apps/api pytest tests/e2e -q

Từ apps/web:

    npm test -- --run

## Kiểm tra tích hợp trên dữ liệu hiện có

Đã chạy offline temporal holdout với cutoff 15/09/2026, dữ liệu giá kết thúc 13/11/2026; test có 1.200 nhãn từ 16/09 đến 10/11/2026. Validation 40 phiên nằm hoàn toàn trước cutoff và chỉ dùng chọn model. Train fit thực tế có 24.420 mẫu LightGBM, 23.850 chuỗi LSTM.

Lần chạy chỉ dùng một epoch LSTM để kiểm tra luồng. Đây không phải thực nghiệm hoàn chỉnh dùng thay số liệu đồ án, không phải bộ dữ liệu chưa từng được người nghiên cứu xem, và không phải bằng chứng sinh lời.

| Model trong lần kiểm tra một epoch | Accuracy holdout | Macro F1 holdout |
|---|---:|---:|
| LightGBM | 46,92% | 0,3910 |
| LSTM | 47,00% | 0,3868 |
| Lớp đa số chọn từ Train | 59,42% | 0,2485 |

Đầu ra cục bộ của lần kiểm tra: /tmp/stocktrend-phase1-holdout-verified-20261114. Trong đó evaluation.json lưu cấu hình, metric và fingerprint dữ liệu; predictions.json lưu dự báo từng mẫu; artifacts lưu bộ model thử nghiệm. Fingerprint đầu vào: 23c414418ce5333bd41b777fd59467e31173de48e808e0ee0a1a8c2b315dd57f. Thư mục /tmp không phải kho lưu trữ dài hạn cho kết quả cuối.

SHAP đã được chạy trên 30 mẫu bằng model/scaler của lần kiểm tra này và vượt kiểm tra tính cộng raw score. Kết quả tại /tmp/stocktrend-phase1-shap-verified-20261114, gồm ba hình và shap_analysis.json. Đây là kiểm tra tích hợp, không thay hình trong bản thảo.

Đã chạy thêm backtest VIC trên 40 phiên holdout với artifact cutoff đúng thời gian, chặn mọi yêu cầu mạng trong lần kiểm tra. Luồng hoàn tất với bảy giao dịch đóng; bản đối soát nằm trong backtest_acceptance.json. Không dùng một mã này để kết luận hiệu quả đầu tư toàn hệ thống.

Ví dụ chạy một thực nghiệm riêng, từ apps/ml; chọn thư mục output mới chưa tồn tại:

    uv run python -m vn_stock.modeling.evaluation --cutoff 2026-09-15 --end 2026-11-13 --epochs 40 --output /absolute/path/new-evaluation

Runner chỉ đọc panel cục bộ, không gọi đồng bộ SSI và không công bố artifact sang models production. Mỗi run cần thư mục riêng. Khi chọn nhiều cutoff để đánh giá liên tục, xác định trước các giai đoạn test không chồng lấn và không điều chỉnh tham số bằng kết quả test.

## Kết quả cũ cần tính lại và phần việc tiếp theo

Các ROI, Sharpe, Sortino, CAGR, chi phí, số cổ phiếu và p-value dựa trên backtest cũ không được tự giữ nguyên. Sửa đơn vị tiền, thời điểm bán, trượt giá và phép tổng hợp metrics có thể đổi kết quả. Đợt này không sửa hoặc tái chạy Monte Carlo N=100 và không chỉnh sửa Word.

Các việc còn cần một đợt thực nghiệm riêng: đánh giá đủ epoch trên các cửa sổ thời gian đã chốt; kiểm tra sự kiện doanh nghiệp và survivorship bias; dữ liệu cơ bản point-in-time thay metadata hiện tại; kiểm định Monte Carlo và lựa chọn nhiều chiến lược; lịch nghỉ lễ giao dịch; nghiệm thu live; cập nhật biểu đồ quỹ đạo/confidence theo đúng ý nghĩa đầu ra model. Không dùng điểm F1 ở lần một epoch để tuyên bố nâng chất lượng model production.

## Nguồn tham chiếu đã đối chiếu

1. Scikit-learn, Cross-validation evaluating estimator performance: https://scikit-learn.org/stable/modules/cross_validation.html
2. SHAP, TreeExplainer, phân biệt raw/probability: https://shap.readthedocs.io/en/stable/generated/shap.TreeExplainer.html
3. VSD, thông báo thay đổi thanh toán ngày 19/08/2022, phân bổ trước 13:00 để giao dịch chiều T+2: https://vsdc.vn/vi/ad/152750. Đây là căn cứ cho giả định bảo thủ của engine nến ngày, không phải xác nhận mọi văn bản hiện hành đến ngày triển khai.
