"""
Chapter 4: THIẾT KẾ VÀ HIỆN THỰC HÓA HỆ THỐNG
"""

CHAPTER_4_DATA = {
    "title": "CHƯƠNG 4: THIẾT KẾ VÀ HIỆN THỰC HÓA HỆ THỐNG",
    "sections": [
        {
            "id": "4.1",
            "title": "4.1. KIẾN TRÚC TỔNG THỂ MONOREPO VÀ LUẬN GIẢI TIÊU CHÍ LỰA CHỌN MÔ HÌNH",
            "subsections": [
                {
                    "id": "4.1.1",
                    "title": "4.1.1. Cấu trúc Monorepo phân tầng hoàn chỉnh",
                    "paragraphs": [
                        "Hệ thống được tổ chức theo kiến trúc Monorepo (Kho mã nguồn hợp nhất) phân tầng nghiêm ngặt, tuân thủ nguyên tắc phân tách trách nhiệm (Separation of Concerns) nhằm tối ưu hóa việc phát triển, kiểm thử và triển khai đồng bộ:",
                        "- apps/ml: Động cơ Khoa học dữ liệu và Tài chính định lượng (Python 3.10+, uv, PyTorch 2.x, LightGBM, Pandas, Apache Parquet). Chịu trách nhiệm toàn bộ vòng đời ML: từ Ingestion kết nối SSI FC-Data, tính toán đặc trưng, Walk-Forward Purged Boundary, Pipeline Huấn luyện lại Thực chiến, cho đến Động cơ Backtesting T+2 và kiểm định Monte Carlo.",
                        "- apps/api: Tầng dịch vụ Backend RESTful API hiệu năng cao (FastAPI, Pydantic V2, Uvicorn). Đóng gói toàn bộ logic từ apps/ml thành các API endpoints phi đồng bộ (Async), tích hợp cơ chế nạp trước mô hình qua Lifespan Context Manager và quản lý phiên thị trường theo mốc 15:00 ATC.",
                        "- apps/web: Tầng giao diện người dùng Web Dashboard tương tác (Next.js 16 App Router, React 19, TypeScript, Tailwind CSS). Tích hợp thư viện đồ thị TradingView Lightweight Charts v5.2 vẽ trên HTML5 Canvas 60fps, nến FireAnt kết hợp Quỹ đạo T+3 và Phân hệ Quản lý Chiến thuật cá nhân chuẩn sàn DNSE EnTrade X.",
                        "- packages/shared: Thư viện chia sẻ mã nguồn chung giữa Backend và Frontend (chứa các định nghĩa kiểu dữ liệu TypeScript Interfaces, hằng số cấu hình rổ VN30, danh mục ngành và tham số giao dịch vi cấu trúc).",
                        "- infra: Hạ tầng triển khai container hóa (Docker Compose, Dockerfile đa giai đoạn và cơ sở dữ liệu PostgreSQL 16)."
                    ]
                },
                {
                    "id": "4.1.2",
                    "title": "4.1.2. Luận giải tiêu chí lựa chọn mô hình và so sánh với các nghiên cứu trước",
                    "paragraphs": [
                        "Để bảo vệ quyết định kiến trúc trước Hội đồng khoa học, đồ án luận giải rõ ràng các tiêu chí lựa chọn mô hình học máy:",
                        "1. Vì sao loại bỏ bài toán Hồi quy giá tuyệt đối (Price Regression)?",
                        "- Các nghiên cứu trước đây thường dùng mạng nơ-ron để hồi quy giá đóng cửa ngày mai (Close_{t+1}). Trong thực tế, do chuỗi giá cổ phiếu là chuỗi bước ngẫu nhiên có độ trôi dạt (Random Walk with Drift), mô hình hồi quy luôn rơi vào trạng thái hội tụ tầm thường: dự đoán giá ngày mai bằng chính giá ngày hôm nay (P_hat_{t+1} xấp xỉ P_t). Mặc dù mô hình đạt sai số RMSE hoặc MAE rất nhỏ (ví dụ sai số chỉ 1-2%), nhưng đường dự báo luôn bị trễ đúng 1 phiên so với đường giá thật. Khi thị trường đảo chiều giảm mạnh, mô hình vẫn báo giá cao và khiến nhà đầu tư thua lỗ nặng.",
                        "- Đồ án chuyển đổi toàn diện sang bài toán Phân loại xu hướng 3 lớp có ngưỡng lọc nhiễu: Nhận diện trực tiếp trạng thái TĂNG, ĐI NGANG hoặc GIẢM. Mô hình buộc phải học các mẫu hình phân kỳ động lượng và áp lực cung cầu để phân tách nhãn, cung cấp tín hiệu hành động Mua/Bán rõ ràng cho nhà đầu tư.",
                        "2. Tiêu chí lựa chọn LightGBM làm mô hình nòng cốt chính (Primary Tabular Model):",
                        "- Như đã phân tích từ luận cứ NeurIPS 2022 của Grinsztajn et al., dữ liệu nến ngày và chỉ báo kỹ thuật có cấu trúc dạng bảng (Tabular Data) với các cột đặc trưng mang ý nghĩa kinh tế độc lập. Thuật toán GBDT của LightGBM có khả năng kháng các đặc trưng kém chất lượng (Uninformative features), bảo toàn cấu trúc bảng và học các hàm biên quyết định gãy khúc tốt hơn nhiều so với Deep Learning.",
                        "- Tốc độ huấn luyện siêu tốc nhờ cơ chế GOSS và EFB: Huấn luyện nhanh gấp 10 lần so với XGBoost truyền thống, cho phép hệ thống thực hiện huấn luyện lại định kỳ (Continuous Retraining) trên toàn bộ dữ liệu lịch sử tích lũy chỉ trong vài giây mỗi khi có nến mới.",
                        "3. Tiêu chí lựa chọn PyTorch Global LSTM làm mô hình đối chứng học sâu (Deep Learning Benchmark):",
                        "- Dựa trên khung Deep Momentum Networks của Viện Oxford-Man (Bryan Lim et al., 2019), mạng LSTM được thiết kế để tiếp nhận đầu vào tensor 3 chiều (N, 20, 14), khai thác mối quan hệ tương quan chuỗi trượt 20 phiên lịch sử.",
                        "- LSTM đóng vai trò là mô hình đối chứng chuyên sâu, đại diện cho trường phái trích xuất động lượng chuỗi thời gian, giúp đánh giá khách quan ưu nhược điểm giữa mô hình dạng bảng (LightGBM) và mô hình học sâu tuần tự (LSTM).",
                        "4. Tiêu chí lựa chọn Naive Baseline làm mốc sàn đối chứng (Performance Floor):",
                        "- Thiết lập nguyên tắc Heuristic quán tính thị trường không tham số: Nếu mô hình AI phức tạp không đánh bại được mốc sàn Naive Baseline (Macro F1 ~0.2051), hệ thống sẽ bị coi là không có giá trị ứng dụng thực tiễn."
                    ]
                }
            ]
        },
        {
            "id": "4.2",
            "title": "4.2. THIẾT KẾ MODULE INGESTION, QUẢN LÝ PHIÊN VÀ KỸ NGHỆ ĐẶC TRƯNG",
            "subsections": [
                {
                    "id": "4.2.1",
                    "title": "4.2.1. Module kết nối SSI Client và Ingestion dữ liệu",
                    "paragraphs": [
                        "Module apps/ml/vn_stock/ssi_client.py hiện thực hóa lớp SSIFastConnectClient quản lý toàn bộ giao tiếp mạng với máy chủ SSI FC-Data:",
                        "- Phương thức get_daily_ohlcv(symbol, from_date, to_date): Tự động định dạng ngày theo chuẩn dd/MM/yyyy; kiểm tra cache bộ nhớ JWT Access Token; tự động phân đoạn các khoảng thời gian dài thành các chunk 25 ngày; xử lý cơ chế ngủ giãn cách 1.2s và tự động thử lại 3 lần nếu xảy ra lỗi kết nối.",
                        "- Phương thức get_daily_index(index_id='VNINDEX', ...): Truy vấn chuỗi chỉ số toàn thị trường, trích xuất điểm số đóng cửa và tính toán chuỗi tỷ suất sinh lời thị trường chung VNINDEX_Return_1d.",
                        "Module apps/ml/vn_stock/data_ingestion.py điều phối quy trình nạp dữ liệu:",
                        "- Hàm validate_downloaded_data(): Thực hiện kiểm định 5 tiêu chuẩn toàn vẹn (thời gian đơn điệu, không trùng lặp, High >= Low, Close > 0, triệt tiêu NaN).",
                        "- Hàm _atomic_save_parquet(): Ghi tệp tạm .tmp và hoán đổi nguyên tử, chống hỏng file khi gặp sự cố bất ngờ.",
                        "- Hàm fetch_daily_ohlcv_incremental(): Tự động phát hiện ngày chốt cuối cùng trong kho lưu trữ, chỉ tải nối đuôi các phiên mới và cập nhật bảng Panel Parquet một cách nhanh chóng."
                    ]
                },
                {
                    "id": "4.2.2",
                    "title": "4.2.2. Module quản lý phiên giao dịch thời gian thực (market_session.py)",
                    "paragraphs": [
                        "Module apps/ml/vn_stock/market_session.py cài đặt các hàm nghiệp vụ cốt lõi:",
                        "- get_current_vn_time(): Trả về thời gian hiện tại chính xác theo múi giờ chuẩn Việt Nam UTC+7 (Asia/Ho_Chi_Minh).",
                        "- get_target_market_date(): Xác định phiên chốt dữ liệu căn cứ theo mốc đóng cửa an toàn 15:00 UTC+7. Nếu thời điểm gọi trước 15:00 các ngày làm việc, trả về ngày giao dịch liền trước (phiên T-1); nếu sau 15:00, trả về phiên hôm nay (phiên T); cuối tuần tự động lùi về thứ Sáu gần nhất.",
                        "- get_target_market_session_info(): Trả về cấu trúc thông tin phiên đầy đủ gồm: target_date, status ('closed' hoặc 'in_progress'), display_label (ví dụ: 'Phiên T-1 (23/10/2026)') và horizon_info (định hướng dự phóng T+1 -> T+3).",
                        "- get_future_trading_days(start_date, n_days): Sinh danh sách n_days ngày giao dịch tương lai, tự động bỏ qua các ngày Thứ Bảy và Chủ Nhật, phục vụ vẽ trục hoành cho biểu đồ Quỹ đạo dự phóng."
                    ]
                },
                {
                    "id": "4.2.3",
                    "title": "4.2.3. Module kỹ nghệ đặc trưng và tạo nhãn (features.py)",
                    "paragraphs": [
                        "Module apps/ml/vn_stock/features.py hiện thực hóa hai hàm trọng tâm:",
                        "- compute_features_per_symbol(df): Tính toán độc lập cho từng mã cổ phiếu toàn bộ 13 đặc trưng tương đối không thứ nguyên: 4 tỷ số nến (Open_Close_Ratio, High_Close_Ratio, Low_Close_Ratio, HL_Ratio), 3 độ lệch SMA (SMA_20_Dev, SMA_50_Dev, SMA_200_Dev), 2 hệ số biến thiên (CV_50, CV_200), tỷ số thanh khoản Vol_Ratio, chỉ báo động lượng RSI_14, tỷ suất sinh lời Return_1d và biến thị trường VNINDEX_Return_1d. Mọi phép toán đều là cửa sổ trượt quá khứ (Rolling backward), không sử dụng bất kỳ thông tin tương lai nào.",
                        "- create_labels_per_symbol(df, threshold=0.01): Dịch chuyển chuỗi tỷ suất sinh lời tương lai Next_Return = df['Close'].shift(-1) / df['Close'] - 1; sau đó áp dụng ngưỡng threshold để phân loại thành 3 nhãn số nguyên: 2 (TĂNG), 0 (GIẢM) và 1 (ĐI NGANG)."
                    ]
                }
            ]
        },
        {
            "id": "4.3",
            "title": "4.3. THIẾT KẾ KHUNG KIỂM ĐỊNH WALK-FORWARD VÀ KỸ THUẬT PURGED BOUNDARY (KHÂU NGHIÊN CỨU)",
            "subsections": [
                {
                    "id": "4.3.1",
                    "title": "4.3.1. Thuật toán phân chia 3 cửa sổ mở rộng Walk-Forward Expanding Windows",
                    "paragraphs": [
                        "Trong khâu nghiên cứu và thẩm định mô hình (Offline Research), tệp apps/ml/vn_stock/splitting_data.py cài đặt thuật toán phân chia Walk-Forward Expanding Windows thông qua hàm generate_walk_forward_windows():",
                        "- Nguyên tắc đồng bộ ngày giao dịch duy nhất (Unique Trading Dates): Thuật toán trích xuất danh sách toàn bộ các ngày giao dịch duy nhất có trong bảng Panel, sau đó chia tỷ lệ trên trục ngày duy nhất này. Nhờ đó, tại một mốc thời gian kiểm thử, tất cả các cổ phiếu trong bảng Panel đều cùng rơi vào tập Train, Val hoặc Test một cách nhất quán.",
                        "- Thiết lập cấu hình 3 Cửa sổ mở rộng:",
                        "  + Cửa sổ 1 (Window 1): Tập Train chiếm 50% thời gian đầu (khoảng 2.140 dòng dữ liệu bảng đa mã); tập Validation chiếm 15% tiếp theo (645 dòng); tập Test chiếm 15% tiếp theo (640 dòng).",
                        "  + Cửa sổ 2 (Window 2): Tập Train mở rộng lên 60% thời gian (khoảng 2.570 dòng); tập Validation chiếm 15% tiếp theo (640 dòng); tập Test chiếm 15% tiếp theo (645 dòng).",
                        "  + Cửa sổ 3 (Window 3): Tập Train mở rộng lên 70% thời gian (khoảng 2.995 dòng); tập Validation chiếm 15% tiếp theo (645 dòng); tập Test chiếm 15% thời gian ngoài mẫu cuối cùng (645 dòng, tương ứng 129 phiên kiểm thử thực tế từ 06/03/2026 đến 11/09/2026)."
                    ]
                },
                {
                    "id": "4.3.2",
                    "title": "4.3.2. Hiện thực hóa kỹ thuật Purged Boundary và Warm-up Sequence Tail",
                    "paragraphs": [
                        "Để bảo đảm tính liêm chính học thuật tuyệt đối, hai kỹ thuật chuyên sâu được lập trình chuẩn xác trong splitting_data.py:",
                        "1. Kỹ thuật Purged Boundary (purge_boundary=True):",
                        "- Do phép dịch chuyển nhãn shift(-1), dòng dữ liệu tại ngày cuối cùng của tập Train chứa giá trị đóng cửa của ngày đầu tiên trong tập Validation. Nếu giữ lại dòng này, mô hình sẽ bị rò rỉ thông tin tương lai.",
                        "- Hàm prepare_all_windows() tự động gán nhãn sentinel -1 cho toàn bộ các dòng thuộc ngày giao dịch cuối cùng của tập Train và tập Validation. Trong vòng lặp huấn luyện tại train.py, hàm drop_ignored_labels() sẽ phát hiện nhãn -1 và chủ động cắt bỏ mẫu ranh giới này khỏi hàm tính mất mát Loss, triệt tiêu 100% rò rỉ ranh giới.",
                        "2. Kỹ thuật Đệm Khởi động Chuỗi (Warm-up Sequence Tail):",
                        "- Mạng nơ-ron PyTorch LSTM yêu cầu đầu vào chuỗi độ dài seq_len = 20 phiên. Hàm get_warmup_tail() trích xuất đúng 19 phiên giao dịch cuối cùng của tập trước làm phần đệm khởi động gắn vào đầu tập sau.",
                        "- Nhờ có 19 phiên đệm này, mẫu kiểm thử đầu tiên của tập Validation (hoặc tập Test) vẫn có đủ 20 phiên ngữ cảnh lịch sử để trượt cửa sổ, giúp hệ thống bảo toàn nguyên vẹn 100% mẫu kiểm thử mà không bị mất mát dữ liệu và không gây rò rỉ nhãn.",
                        "3. Chuẩn hóa độc lập (Independent Scaling):",
                        "- Lớp StandardScaler chỉ được gọi phương thức fit() duy nhất trên tập Train của từng cửa sổ Walk-Forward độc lập. Sau đó, chỉ áp dụng phương thức transform() trên tập Validation và Test, đảm bảo giá trị trung bình và độ lệch chuẩn của tương lai không bao giờ bị lộ cho tập học."
                    ]
                }
            ]
        },
        {
            "id": "4.4",
            "title": "4.4. THIẾT KẾ VÀ HIỆN THỰC HÓA PIPELINE HUẤN LUYỆN LẠI THỰC CHIẾN (PRODUCTION RETRAINING PIPELINE)",
            "subsections": [
                {
                    "id": "4.4.1",
                    "title": "4.4.1. Sự chuyển hóa giữa Nghiên cứu và Thực chiến",
                    "paragraphs": [
                        "Một trong những điểm khác biệt căn bản giữa một bài toán nghiên cứu học thuật thuần túy và một hệ thống phần mềm thực tế là: Khi đưa vào vận hành thực chiến, hệ thống không thể sử dụng một mô hình cũ bị cắt khúc thời gian trong quá khứ, bởi vì điều kiện kinh tế vĩ mô và tương quan dòng tiền luôn dịch chuyển (Concept Drift).",
                        "Để thích ứng với thị trường thực tế, hệ thống cần một cơ chế tự động huấn luyện lại (Production Retraining Pipeline) có khả năng học trên 100% dữ liệu lịch sử tích lũy đến phiên chốt gần nhất, đồng thời phải duy trì kỷ luật chống rò rỉ dữ liệu nghiêm ngặt."
                    ]
                },
                {
                    "id": "4.4.2",
                    "title": "4.4.2. Kỹ thuật Purged Horizon trong thực chiến",
                    "paragraphs": [
                        "Bài toán thực chiến hướng tới dự phóng xu hướng cho chu kỳ vị thế hoàn chỉnh T+3 (horizon = 3) với ngưỡng lọc nhiễu 2.0% (threshold = 0.02). Tỷ suất sinh lời sau 3 phiên được xác định theo công thức:",
                        "Return_{t+3} = (Close_{t+3} - Close_t) / Close_t",
                        "Hãy xem xét thời điểm hiện tại khi ngày chốt phiên gần nhất là ngày T:",
                        "- Phiên T-2: Muốn biết nhãn, cần giá đóng cửa của phiên T+1 (chưa diễn ra).",
                        "- Phiên T-1: Muốn biết nhãn, cần giá đóng cửa của phiên T+2 (chưa diễn ra).",
                        "- Phiên T: Muốn biết nhãn, cần giá đóng cửa của phiên T+3 (chưa diễn ra).",
                        "Như vậy, tại thời điểm T, đúng 3 dòng dữ liệu cuối cùng của mỗi mã cổ phiếu hoàn toàn chưa có kết quả thực tế trong tương lai. Trong hàm create_multi_day_labels() tại splitting_data.py, sau khi thực hiện phép shift(-3), 3 dòng cuối cùng này sẽ nhận giá trị NaN ở cột nhãn. Hàm tự động thực hiện thao tác cắt bỏ (Purge): g = g.dropna(subset=['Label']).",
                        "Kỹ thuật Purged Horizon này bảo đảm hệ thống tuyệt đối không nạp các nhãn rỗng hoặc gán nhãn giả định vào mô hình, giữ vững tính liêm chính dữ liệu trong khâu thực chiến."
                    ]
                },
                {
                    "id": "4.4.3",
                    "title": "4.4.3. Tách biệt Validation Buffer và Khóa Scaler cố định",
                    "paragraphs": [
                        "Trong hàm prepare_production_training_data() tại splitting_data.py, quy trình tiền xử lý thực chiến được thực hiện qua hai bước then chốt:",
                        "1. Cô lập Vùng đệm Kiểm thực (Validation Buffer Isolation):",
                        "- Hệ thống trích xuất 40 phiên giao dịch gần nhất (~2 tháng giao dịch gần nhất) làm tập Validation Buffer độc lập.",
                        "- Tập Validation Buffer này chỉ thuần túy phục vụ cơ chế ngắt sớm (Early Stopping sau 30 vòng không cải thiện của LightGBM và lựa chọn checkpoint trọng số tốt nhất best_weights của PyTorch LSTM), ngăn chặn hoàn toàn hiện tượng học vẹt quá khớp.",
                        "2. Khóa Cố định Bộ chuẩn hóa (Frozen Scaler Artifact):",
                        "- Bộ chuẩn hóa StandardScaler được fit độc lập 100% trên tập Train lịch sử (không bao gồm Validation Buffer).",
                        "- Sau khi hoàn tất, bộ tham số chuẩn hóa được xuất ra tệp artifact cố định production_scaler_t3.pkl. Khi người dùng thực hiện suy luận trực tuyến trong phiên, hệ thống chỉ nạp tệp scaler này và gọi hàm transform(), tuyệt đối không fit lại trên dữ liệu thời gian thực."
                    ]
                },
                {
                    "id": "4.4.4",
                    "title": "4.4.4. Quy trình huấn luyện tự động (train_production_model) và Xuất Artifacts",
                    "paragraphs": [
                        "Hàm train_production_model() trong apps/ml/vn_stock/modeling/train.py điều phối toàn bộ quy trình huấn luyện lại tự động:",
                        "- Bước 1: Gọi sync_latest_market_data() tự động nạp nến nối đuôi gia tăng từ SSI FC-Data.",
                        "- Bước 2: Tạo nhãn đa phiên T+horizon (mặc định T+3) có ngưỡng lọc nhiễu 2.0% và áp dụng Purged Horizon.",
                        "- Bước 3: Phân chia tập Train và Validation Buffer 40 phiên không rò rỉ ranh giới.",
                        "- Bước 4: Huấn luyện song song mô hình LightGBM GBDT và mô hình PyTorch Global LSTM trên toàn bộ rổ cổ phiếu (hỗ trợ phạm vi CORE 5 mã hoặc toàn bộ VN30 30 mã).",
                        "- Bước 5: Đóng gói và lưu trữ 4 tệp artifacts sản xuất vào thư mục apps/ml/models/:",
                        "  + production_lgb_t3.txt (mô hình LightGBM đã huấn luyện).",
                        "  + production_lstm_t3.pth (checkpoint trọng số tốt nhất của PyTorch LSTM).",
                        "  + production_scaler_t3.pkl (bộ chuẩn hóa StandardScaler đã khóa cố định).",
                        "  + production_training_info_t3.json (tệp nhật ký ghi nhận đầy đủ ngày chốt phiên, số mẫu học 4.425 mẫu, siêu tham số và ma trận nhầm lẫn Confusion Matrix)."
                    ]
                },
                {
                    "id": "4.4.5",
                    "title": "4.4.5. Cơ chế Suy luận Trực tuyến Near-realtime và Xây dựng Quỹ đạo dự phóng T+3",
                    "paragraphs": [
                        "Trong tệp apps/ml/vn_stock/modeling/predict.py, hai hàm suy luận trực tuyến được cài đặt:",
                        "1. Hàm predict_trend(symbol, model_type, horizon=3):",
                        "- Tự động nạp bộ chuẩn hóa production_scaler_t3.pkl và checkpoint mô hình sản xuất tương ứng.",
                        "- Lấy nến chốt gần nhất từ market_session.py; chuẩn hóa 13 đặc trưng tương đối; đưa qua tầng phân loại Softmax để xuất ra xác suất 3 lớp (P_Giam, P_DiNgang, P_Tang) có tổng bằng 1.0 và chỉ số tin cậy Confidence = max(P) * 100%.",
                        "2. Hàm predict_trajectory(symbol, model_type, horizon=3):",
                        "- Xây dựng lộ trình dự phóng chi tiết cho chu kỳ vị thế 3 phiên theo vi cấu trúc VSDC:",
                        "  + Điểm T (Phiên hiện tại): Mức giá chốt nến căn cứ Close_T.",
                        "  + Phiên T+1: Điểm mở vị thế mua giả định tại giá mở cửa Open_{t+1} (có tính trượt giá 0.05%).",
                        "  + Phiên T+2: Trạng thái cổ phiếu đang trên đường về tài khoản, khóa quyền bán theo quy chế thanh toán.",
                        "  + Phiên T+3: Điểm cổ phiếu khả dụng trong tài khoản, sẵn sàng hiện thực hóa lợi nhuận hoặc kích hoạt cắt lỗ.",
                        "- Quỹ đạo này được xuất dưới dạng cấu trúc dữ liệu JSON để giao diện Web Dashboard hiển thị trực quan biểu đồ nến FireAnt kết hợp đường cong dự phóng."
                    ]
                }
            ]
        },
        {
            "id": "4.5",
            "title": "4.5. THIẾT KẾ ĐỘNG CƠ KIỂM THỬ CHIẾN LƯỢC (BACKTESTING ENGINE) VÀ KIỂM ĐỊNH MONTE CARLO",
            "subsections": [
                {
                    "id": "4.5.1",
                    "title": "4.5.1. Quản lý trạng thái lô cổ phiếu qua Dataclass PositionLot",
                    "paragraphs": [
                        "Để phản ánh trung thực quy chế thanh toán bù trừ T+2 của thị trường chứng khoán Việt Nam, động cơ kiểm thử trong apps/ml/vn_stock/backtest.py từ bỏ cách tiếp cận quản lý số dư gộp giản đơn, mà hiện thực hóa việc theo dõi vị thế chi tiết theo từng lô cổ phiếu thông qua cấu trúc dữ liệu @dataclass PositionLot:",
                        "- Mỗi khi khớp một lệnh Mua tại phiên có chỉ số buy_idx, hệ thống khởi tạo một đối tượng PositionLot lưu trữ: buy_idx (chỉ số ngày mua), shares (số lượng cổ phiếu), buy_price (giá khớp thực tế), cost_basis (tổng vốn đầu tư bao gồm cả phí môi giới) và chỉ số ngày chứng khoán về tài khoản:",
                        "settled_idx = buy_idx + 2",
                        "- Khi xuất hiện tín hiệu BÁN tại phiên s, hàm simulate_vietnam_trading() thực hiện duyệt qua toàn bộ kho hàng và phân tách thành hai danh sách:",
                        "  + settled_lots: Các lô cổ phiếu thỏa mãn điều kiện settled_idx <= s (cổ phiếu đã về tài khoản từ phiên chiều hôm trước, nhà đầu tư có toàn quyền bán).",
                        "  + unsettled_lots: Các lô cổ phiếu có settled_idx > s (cổ phiếu đang trên đường về tài khoản theo quy chế thanh toán bù trừ của VSDC).",
                        "- Lệnh bán chỉ được thực hiện trên khối lượng của settled_lots. Toàn bộ khối lượng trong unsettled_lots bị từ chối bán và giữ nguyên trong tài khoản. Thiết kế này ngăn chặn triệt để tình trạng bán non T+0 và bán khống, khắc phục lỗ hổng kinh điển của các nghiên cứu tài chính trước đây."
                    ]
                },
                {
                    "id": "4.5.2",
                    "title": "4.5.2. Logic khớp lệnh thực tế sát vi cấu trúc sàn Việt Nam",
                    "paragraphs": [
                        "Động cơ kiểm thử cài đặt logic khớp lệnh thực tế tuân thủ nghiêm ngặt 4 quy chuẩn vi cấu trúc:",
                        "1. Khớp lệnh tại giá mở cửa Open_{t+1}: Tín hiệu sinh ra cuối phiên t dựa trên Close_t chỉ được khớp tại phiên kế tiếp t+1 tại giá Open_{t+1} kèm tỷ lệ trượt giá thực thi Slippage 0.05%:",
                        "Giá mua thực tế = Open_{t+1} * (1 + 0.0005)",
                        "Giá bán thực tế = Open_{t+1} * (1 - 0.0005)",
                        "2. Khấu trừ đầy đủ Thuế và Phí giao dịch:",
                        "- Phí môi giới giao dịch: Fee = Giá trị khớp lệnh * 0.15% (cho cả chiều mua và chiều bán).",
                        "- Thuế chuyển nhượng chứng khoán: Tax = Giá trị bán * 0.10% (theo Thông tư 111/2013/TT-BTC).",
                        "3. Khớp lệnh theo lô chẵn 100 cổ phiếu:",
                        "Số cổ phiếu mua = floor( Tiền mặt khả dụng / (Giá mua thực tế * (1 + 0.0015)) / 100 ) * 100",
                        "Phần tiền mặt lẻ dư ra sau khi làm tròn lô chẵn được bảo toàn nguyên vẹn trong tài khoản (cash_after).",
                        "4. Quản trị rủi ro tự động trong phiên (Intraday Risk Controls):",
                        "- Kích hoạt Cắt lỗ (Stop Loss): Nếu giá thấp nhất Low_{t+1} chạm ngưỡng cắt lỗ, vị thế được bán ngay tại giá Stop Loss.",
                        "- Kích hoạt Chốt lời (Take Profit): Nếu giá cao nhất High_{t+1} chạm ngưỡng chốt lời, vị thế được hiện thực hóa lợi nhuận.",
                        "- Chặn lãi trượt (Trailing Stop): Liên tục nâng ngưỡng dừng lỗ theo mức giá đỉnh cao nhất (highest_price) đạt được kể từ khi mở vị thế."
                    ]
                },
                {
                    "id": "4.5.3",
                    "title": "4.5.3. Động cơ Backtest danh mục đa mã và Hệ thống 25+ chỉ số tài chính",
                    "paragraphs": [
                        "Hàm run_portfolio_backtest() cho phép kiểm thử đồng thời trên danh mục nhiều mã cổ phiếu (rổ VN30 hoặc danh mục theo ngành):",
                        "- Cơ chế phân bổ vốn đều 1/N: Vốn ban đầu (mặc định 100.000.000 VNĐ) được phân bổ đồng đều w_i = 1/N cho từng mã cổ phiếu trong danh mục, loại bỏ rủi ro sai lệch ước lượng ma trận hiệp phương sai theo lý thuyết của Ernst et al. (2016).",
                        "- Định giá tài sản hàng ngày (Mark-to-Market): Cuối mỗi phiên giao dịch, tổng tài sản danh mục (Equity) được tính bằng: Tiền mặt khả dụng + Tổng giá trị thị trường của toàn bộ các lô cổ phiếu đang nắm giữ tính theo giá đóng cửa Close_t.",
                        "- Tính toán toàn diện hệ thống 25+ chỉ số định lượng tài chính (lưu trong Dataclass BacktestMetrics): ROI%, CAGR 252 phiên, Alpha so với Buy & Hold, Tỷ số Sharpe năm hóa (Rf = 4.0%), Tỷ số Sortino năm hóa, Tỷ số Calmar, Mức sụt giảm tối đa MDD%, Giá trị chịu rủi ro VaR 95% ngày, CVaR 95%, Tỷ lệ thắng Win Rate%, Hệ số lợi nhuận Profit Factor, Tỷ số Lãi/Lỗ bình quân Payoff Ratio và thời gian nắm giữ bình quân."
                    ]
                },
                {
                    "id": "4.5.4",
                    "title": "4.5.4. Thuật toán kiểm định hoán vị ngẫu nhiên Monte Carlo 100 lần",
                    "paragraphs": [
                        "Để chứng minh hiệu quả sinh lời của chiến lược AI không phải do yếu tố may rủi ngẫu nhiên, hàm run_monte_carlo_random_test() thực hiện thuật toán kiểm định hoán vị ngẫu nhiên (Permutation Test) với N = 100 kịch bản đối chứng:",
                        "- Bước 1: Giữ nguyên toàn bộ chuỗi nến giá lịch sử, các ràng buộc thanh toán bù trừ T+2 và chi phí thuế phí thực tế.",
                        "- Bước 2: Sinh ngẫu nhiên 100 chuỗi tín hiệu MUA/BÁN độc lập tuân theo đúng phân phối xác suất lớp thực tế của dữ liệu kiểm thử.",
                        "- Bước 3: Đưa từng chuỗi tín hiệu ngẫu nhiên qua động cơ kiểm thử để thu được phân phối xác suất của 100 Tỷ số Sharpe ngẫu nhiên {SR_random_1, ..., SR_random_100}.",
                        "- Bước 4: Tính toán giá trị p-value thực nghiệm:",
                        "p_value = (Số lần mà SR_random >= SR_AI) / 100",
                        "Nếu p_value < 0.05, giả thuyết không H0 (cho rằng mô hình AI chỉ là kết quả ngẫu nhiên) bị bác bỏ ở mức ý nghĩa 5%, chứng minh năng lực sinh lời Alpha của mô hình có ý nghĩa thống kê khoa học vững chắc."
                    ]
                }
            ]
        },
        {
            "id": "4.6",
            "title": "4.6. THIẾT KẾ PHÂN HỆ QUẢN LÝ CHIẾN THUẬT CÁ NHÂN CHUẨN DNSE ENTRADE X",
            "subsections": [
                {
                    "id": "4.6.1",
                    "title": "4.6.1. Kiến trúc phân hệ hai chế độ chuyên nghiệp",
                    "paragraphs": [
                        "Phân hệ Quản lý Chiến thuật định lượng cá nhân (hiện thực hóa tại apps/web/src/components/backtest/SavedStrategiesManager.tsx) được thiết kế theo chuẩn trải nghiệm của các nền tảng giao dịch chứng khoán hiện đại (tham chiếu DNSE EnTrade X):",
                        "Phân hệ bao gồm hai chế độ vận hành độc lập nhưng kết nối chặt chẽ:",
                        "1. Chế độ Quản lý Danh mục Chiến thuật (Strategy Manager): Giao diện quản lý danh sách các chiến thuật định lượng cá nhân trực quan với bộ ba nút lọc chuẩn sàn: 'Tất cả' (All), 'Triển khai' (Active) và 'Chưa triển khai' (Draft).",
                        "2. Chế độ Phòng Lab Kiểm thử (Strategy Builder & Backtest Lab): Môi trường thử nghiệm tương tác cho phép cấu hình chi tiết điều kiện mua/bán, chạy giả lập trên dữ liệu lịch sử và phân tích hiệu suất chuyên sâu."
                    ]
                },
                {
                    "id": "4.6.2",
                    "title": "4.6.2. Cơ chế quản lý trạng thái chiến thuật thực chiến (Active vs Draft)",
                    "paragraphs": [
                        "Điểm đổi mới mang tính thực tiễn cao của phân hệ là cơ chế phân tách rõ ràng hai trạng thái vận hành của một chiến thuật định lượng:",
                        "- Trạng thái 'Triển khai' (Active Monitoring): Dành riêng cho các chiến thuật đã được người dùng kiểm thử kỹ lưỡng qua dữ liệu lịch sử đạt các chỉ số tài chính kỳ vọng (ROI cao, Sharpe > 1.0, Max Drawdown trong tầm kiểm soát) và được người dùng chính thức phê duyệt đưa vào vận hành theo dõi thị trường thực tế. Các chiến thuật Active sẽ được kết nối với hệ thống giám sát tín hiệu thời gian thực để phát cảnh báo Mua/Bán hàng ngày cho nhà đầu tư.",
                        "- Trạng thái 'Chưa triển khai' (Draft Testing): Dành cho các chiến thuật bản nháp đang trong quá trình nghiên cứu, thử nghiệm, tinh chỉnh các ngưỡng tham số hoặc lưu trữ để đối chứng.",
                        "- Người dùng có thể dễ dàng chuyển đổi trạng thái giữa Draft và Active chỉ bằng một thao tác nhấp chuột (Toggle Switch) hoặc nhấn nút 'Chạy lại' để kiểm tra lại hiệu quả trên dữ liệu thị trường mới nhất."
                    ]
                },
                {
                    "id": "4.6.3",
                    "title": "4.6.3. Hệ thống 12 điều kiện Mua, 12 điều kiện Bán và Quản trị rủi ro tự động",
                    "paragraphs": [
                        "Phòng Lab Kiểm thử cung cấp bộ tùy biến điều kiện định lượng toàn diện nhất hiện nay:",
                        "- Bộ 12 điều kiện Mua kỹ thuật: % Khối lượng đột biến so với trung bình 10 phiên, Chỉ số định giá P/B, Chỉ số P/E, Thị giá cổ phiếu, Vốn hóa thị trường, Giá trị giao dịch bình quân, Vị thế so với đường MA20/MA50/MA200, Dải dao động RSI-14, Tăng trưởng doanh thu quý, Tăng trưởng lợi nhuận sau thuế quý, Khối ngoại mua ròng và Tín hiệu giao cắt kỹ thuật (Breakout Bollinger Bands, MACD Histogram).",
                        "- Bộ 12 điều kiện Bán và Quy tắc Quản trị rủi ro tự động:",
                        "  + Cắt lỗ tự động (Stop Loss %): Tự động đóng vị thế khi thua lỗ vượt ngưỡng cấu hình (ví dụ: -5% đến -10%).",
                        "  + Chốt lời mục tiêu (Take Profit %): Hiện thực hóa lợi nhuận khi đạt kỳ vọng (ví dụ: +15% đến +25%).",
                        "  + Chặn lãi trượt (Trailing Stop %): Tự động nâng ngưỡng dừng lỗ theo giá đỉnh cao nhất đạt được (highest_price), bảo toàn lợi nhuận khi thị trường quay đầu giảm.",
                        "  + Giới hạn số ngày nắm giữ tối đa (Max Holding Days): Đóng vị thế nếu cổ phiếu đi ngang không sinh lời sau N phiên.",
                        "- Danh mục 8 Chiến lược Mẫu Định lượng (Strategy Presets): Nạp sẵn các mẫu hình kinh điển đã được chứng minh hiệu quả qua lịch sử: (1) Thuận xu hướng Break out EMA 20; (2) Xu hướng tăng mạnh kèm KLGD đột biến; (3) Định giá hợp lý & Dòng tiền xác nhận; (4) CP tăng trưởng Mini-Canslim; (5) Định giá ngân hàng rẻ P/B < 1; (6) Dò tín hiệu tăng sớm RSI thoát quá bán; (7) Chuyển từ sideway sang breakout; (8) Xác nhận đảo chiều khỏi vùng giảm dài hạn."
                    ]
                }
            ]
        },
        {
            "id": "4.7",
            "title": "4.7. THIẾT KẾ VÀ HIỆN THỰC HÓA BACKEND RESTFUL API (FASTAPI)",
            "subsections": [
                {
                    "id": "4.7.1",
                    "title": "4.7.1. Cấu trúc ứng dụng và Quản lý vòng đời ứng dụng (Lifespan Context Manager)",
                    "paragraphs": [
                        "Ứng dụng Backend API được phát triển bằng khung làm việc hiện đại FastAPI (Python 3.10+) tại thư mục apps/api/app/, tuân thủ kiến trúc phân tầng sạch (Clean Layered Architecture):",
                        "- app/core/config.py: Quản lý biến môi trường tập trung thông qua pydantic-settings.BaseSettings (đường dẫn dữ liệu, cổng kết nối, cấu hình CORS, danh mục rổ VN30).",
                        "- app/models/schemas.py: Chuẩn hóa dữ liệu đầu vào (Request) và đầu ra (Response) bằng Pydantic V2 viết bằng Rust, đảm bảo tính an toàn kiểu dữ liệu tuyệt đối và tốc độ xác thực siêu nhanh.",
                        "- app/routers/: Định nghĩa các điểm cuối REST API được phân nhóm theo module nghiệp vụ (stocks.py, predict.py, backtest.py).",
                        "- app/services/: Triển khai logic nghiệp vụ chuyên sâu kết nối trực tiếp tới động cơ ML (stock_service.py, prediction_service.py, backtest_service.py).",
                        "- Cơ chế Lifespan Context Manager (@asynccontextmanager): Quản lý sự kiện khởi động ứng dụng: Tự động tải trước (warm-up) mô hình LightGBM, mô hình PyTorch LSTM và bộ chuẩn hóa Scaler vào bộ nhớ RAM; nạp thông tin phiên thị trường từ market_session.py; kiểm tra tính toàn vẹn của các tệp Parquet. Nhờ cơ chế này, khi có yêu cầu truy vấn từ người dùng, máy chủ có thể trả kết quả suy luận ngay lập tức mà không mất thời gian nạp lại tệp trọng số từ ổ đĩa."
                    ]
                },
                {
                    "id": "4.7.2",
                    "title": "4.7.2. Danh mục các điểm cuối REST API thực chiến",
                    "paragraphs": [
                        "Hệ thống cung cấp danh mục endpoints RESTful toàn diện:",
                        "1. Nhóm Dữ liệu Thị trường và Phiên giao dịch (/api/stocks):",
                        "- GET /api/stocks/symbols: Danh mục mã cổ phiếu hỗ trợ và phân loại ngành.",
                        "- GET /api/stocks/history?symbol={symbol}: Trả về chuỗi nến ngày OHLCV phục vụ vẽ biểu đồ TradingView Canvas.",
                        "- GET /api/stocks/indicators?symbol={symbol}: Trả về chuỗi 13 đặc trưng kỹ thuật tương đối đã tính toán.",
                        "- GET /api/stocks/market-board: Bảng giá trực tuyến các mã rổ VN30 (thị giá, thay đổi %, khối lượng, giao dịch khối ngoại).",
                        "- GET /api/stocks/sync-status: Kiểm tra trạng thái phiên giao dịch căn cứ và độ tươi của dữ liệu.",
                        "- POST /api/stocks/sync: Kích hoạt tiến trình đồng bộ nến thị trường mới nhất từ SSI FC-Data.",
                        "2. Nhóm Suy luận AI và Quỹ đạo (/api/predict):",
                        "- GET /api/predict/live?symbol={symbol}&model_type={model}: Suy luận thời gian thực cho phiên chốt gần nhất, trả về nhãn khuyến nghị, phân bổ xác suất Softmax 3 lớp, mức tin cậy và Quỹ đạo dự phóng 3 phiên T+1 -> T+3.",
                        "- POST /api/predict/batch: Quét radar phân tích đồng loạt 5 mã cổ phiếu trọng tâm.",
                        "- POST /api/predict/retrain: Kích hoạt pipeline huấn luyện lại mô hình thực chiến T+3 trên dữ liệu tích lũy, tự động cập nhật các tệp artifacts trong thư mục models/.",
                        "3. Nhóm Động cơ Kiểm thử và Quản lý Chiến thuật (/api/backtest):",
                        "- POST /api/backtest/run: Chạy kiểm thử chiến lược tương tác đơn mã, trả về 25 chỉ số định lượng và nhật ký khớp lệnh T+2.",
                        "- POST /api/backtest/advanced: Chạy giả lập danh mục đa mã, áp dụng bộ lọc 12 điều kiện mua/bán DNSE EnTrade X và phân tích lưới chỉ số deal.",
                        "- GET /api/backtest/presets: Danh sách 8 chiến lược mẫu định lượng nạp sẵn.",
                        "- GET /api/backtest/signals/recent: Danh sách các tín hiệu Mua/Bán mới nhất trên thị trường."
                    ]
                }
            ]
        },
        {
            "id": "4.8",
            "title": "4.8. THIẾT KẾ VÀ HIỆN THỰC HÓA FRONTEND WEB DASHBOARD (NEXT.JS 16)",
            "subsections": [
                {
                    "id": "4.8.1",
                    "title": "4.8.1. Nền tảng công nghệ và Triết lý thiết kế thị giác",
                    "paragraphs": [
                        "Ứng dụng giao diện người dùng Web Dashboard được phát triển tại thư mục apps/web/ dựa trên nền tảng Next.js 16 App Router, React 19, TypeScript và Tailwind CSS:",
                        "- Triết lý thiết kế Institutional Trading Terminal: Giao diện được thiết kế theo tiêu chuẩn các bảng điều khiển giao dịch định lượng quốc tế hiện đại. Tông màu nền tối cao cấp (Slate 950 / Zinc 950) giúp giảm mỏi mắt khi theo dõi biểu đồ trong thời gian dài, viền mờ tinh tế (border-slate-800), độ tương phản chữ đạt chuẩn WCAG AAA.",
                        "- Quy chuẩn màu sắc tài chính chuẩn mực: Màu Xanh ngọc (#10B981) biểu thị Nến Tăng, Xu hướng TĂNG và Khuyến nghị MUA; Màu Đỏ san hô (#EF4444) biểu thị Nến Giảm, Xu hướng GIẢM, Khuyến nghị BÁN và Đường sụt giảm vốn; Màu Vàng hổ phách (#F59E0B) biểu thị Xu hướng ĐI NGANG và Khuyến nghị NẮM GIỮ; Màu Tím Indigo (#818CF8) đại diện cho Tín hiệu Trí tuệ Nhân tạo."
                    ]
                },
                {
                    "id": "4.8.2",
                    "title": "4.8.2. Thiết kế chi tiết các phân hệ màn hình chính",
                    "paragraphs": [
                        "Giao diện Web Dashboard tích hợp 3 màn hình chuyên sâu:",
                        "1. Thanh điều hướng đỉnh cao (TopHeader.tsx):",
                        "- Hiển thị trạng thái phiên trực tuyến căn cứ theo mốc 15:00 ATC (Phiên T / T-1), giờ Việt Nam chuẩn (UTC+7).",
                        "- Nút bấm kích hoạt đồng bộ dữ liệu SSI trực tuyến chỉ với 1 click.",
                        "- Bộ tìm kiếm nhanh mã cổ phiếu theo từng nhóm ngành kinh tế (Ngân hàng, Bất động sản, Thép, Bán lẻ, Công nghệ...).",
                        "2. Màn hình 1: Thị trường & Phân tích Kỹ thuật (MarketOverviewTab.tsx):",
                        "- Biểu đồ nến tương tác Canvas TradingView Lightweight Charts v5.2 kết hợp đường SMA(20) và cột khối lượng phân màu, đạt tốc độ khung hình mượt mà 60fps cho hàng nghìn điểm dữ liệu.",
                        "- Biểu đồ dao động RSI(14) có vạch ngưỡng Quá mua (70) và Quá bán (30).",
                        "- Lưới 6 thẻ chỉ báo kỹ thuật hiển thị chi tiết các đặc trưng tương đối (SMA20 Dev, SMA50 Dev, Hệ số biến thiên CV_50, Tỷ lệ khối lượng Vol_Ratio...).",
                        "3. Màn hình 2: Tín hiệu AI, Quỹ đạo T+3 & Huấn luyện lại (AIPredictionTab.tsx):",
                        "- Thẻ Khuyến nghị Trung tâm: Tín hiệu MUA / BÁN / NẮM GIỮ với độ tin cậy Confidence % và thanh radar phân bổ xác suất Softmax 3 lớp.",
                        "- Biểu đồ Quỹ đạo Dự phóng T+1 -> T+3 (FireAntTrajectoryChart.tsx): Trực quan hóa hành trình 3 phiên theo vi cấu trúc VSDC: T+1 mở vị thế tại giá Open, T+2 chờ hàng về khóa quyền bán, T+3 cổ phiếu khả dụng sẵn sàng chốt lời.",
                        "- Modal Huấn luyện lại Mô hình (Retrain Modal): Cho phép người dùng tùy biến Epochs, Learning Rate, Horizon và phạm vi (CORE hoặc VN30) để kích hoạt huấn luyện lại thực chiến.",
                        "4. Màn hình 3: Phòng Giả lập Chiến lược DNSE EnTrade X Bố cục 2 Cột (BacktestSimulatorTab.tsx):",
                        "- Cột Trái (Bộ Điều khiển): Tích hợp phân hệ SavedStrategiesManager quản lý chiến thuật theo 3 nút lọc (Tất cả / Triển khai / Chưa triển khai); bộ tùy biến 12 điều kiện mua và 12 điều kiện bán qua dải thanh trượt DualRangeSlider; danh sách 8 chiến lược mẫu Presets; các quy tắc quản trị rủi ro tự động (Stop Loss %, Take Profit %, Trailing Stop %, Max Holding Days).",
                        "- Cột Phải (Báo cáo Hiệu suất Chuyên sâu): Thẻ tóm tắt vốn cuối và ROI%; Lưới chỉ số Deal Performance; Biểu đồ đường cong tài sản tích lũy (EquityCurveChart.tsx) so sánh song song chiến lược AI vs Buy & Hold; Đồ thị sụt giảm vốn Underwater Drawdown; Bảng phân bổ danh mục và Bảng nhật ký giao dịch Trade Log chi tiết từng vòng khớp lệnh T+2."
                    ]
                }
            ]
        },
        {
            "id": "4.9",
            "title": "4.9. ĐÓNG GÓI CONTAINER HÓA VÀ HỆ THỐNG KIỂM THỬ TỰ ĐỘNG",
            "subsections": [
                {
                    "id": "4.9.1",
                    "title": "4.9.1. Đóng gói Container hóa với Docker Compose",
                    "paragraphs": [
                        "Toàn bộ hệ thống Monorepo được đóng gói và điều phối thống nhất thông qua tệp cấu hình infra/docker-compose.yml gồm 3 cụm dịch vụ độc lập:",
                        "1. Dịch vụ Cơ sở dữ liệu (postgres): Chạy image chính thức postgres:16-alpine, quản lý lưu trữ dữ liệu bền vững qua Docker Named Volume (postgres_data), thiết lập cổng 5432 và kiểm tra sức khỏe tự động qua pg_isready.",
                        "2. Dịch vụ Backend API (api): Xây dựng từ Dockerfile đa giai đoạn (Multi-stage build) dựa trên nền tảng python:3.10-slim, sử dụng uv để cài đặt các thư viện Python siêu tốc, mở cổng 8000 và tích hợp endpoint healthcheck (/health).",
                        "3. Dịch vụ Frontend Web Dashboard (web): Xây dựng từ node:20-alpine với quy trình tối ưu hóa Next.js standalone build, mở cổng 3000 phục vụ người dùng.",
                        "Kiến trúc Docker Compose bảo đảm toàn bộ hệ thống có thể được thiết lập và khởi chạy đồng bộ trên bất kỳ máy chủ nào chỉ với một câu lệnh duy nhất (docker compose up -d), loại bỏ hoàn toàn các lỗi sai lệch môi trường (Environment Drift)."
                    ]
                },
                {
                    "id": "4.9.2",
                    "title": "4.9.2. Hệ thống kiểm thử tự động toàn diện đạt 170 tests PASSED 100%",
                    "paragraphs": [
                        "Để bảo đảm tính ổn định, ngăn ngừa lỗi hồi quy (Regression Bugs) và đáp ứng chuẩn mực kỹ thuật phần mềm cao nhất, hệ thống xây dựng bộ kiểm thử tự động toàn diện trên cả 3 phân hệ:",
                        "- Phân hệ apps/ml: Đạt 106 unit tests với PyTest, bao phủ toàn bộ logic Ingestion, SSI Client, Quản lý phiên market_session, Kỹ nghệ đặc trưng, Walk-Forward Purged Boundary, Pipeline Huấn luyện lại thực chiến và Động cơ Backtesting T+2.",
                        "- Phân hệ apps/api: Đạt 45 unit & integration tests với PyTest và HTTPX AsyncClient, kiểm tra toàn bộ các REST endpoints (/api/stocks, /api/predict, /api/backtest), xác thực schema Pydantic V2 và cơ chế xử lý lỗi ngoại lệ.",
                        "- Phân hệ apps/web: Đạt 19 unit & component tests với Vitest và React Testing Library, kiểm tra tính đúng đắn của các components giao diện, bộ lọc SavedStrategiesManager, logic thanh trượt DualRangeSlider và render biểu đồ.",
                        "Tổng cộng toàn bộ hệ thống Monorepo sở hữu 170 bài kiểm thử tự động, đạt tỷ lệ vượt qua tuyệt đối 100% (170/170 tests PASSED), khẳng định chất lượng kỹ thuật vượt trội và độ tin cậy vững chắc của phần mềm đồ án tốt nghiệp."
                    ]
                }
            ]
        }
    ]
}
