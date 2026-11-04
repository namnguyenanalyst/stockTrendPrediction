"""
Front matter content for Graduation Thesis
"""

FRONT_MATTER_DATA = {
    "university": "TRƯỜNG ĐẠI HỌC MỎ - ĐỊA CHẤT",
    "faculty": "KHOA CÔNG NGHỆ THÔNG TIN",
    "department": "BỘ MÔN TIN HỌC KINH TẾ",
    "thesis_title": "NGHIÊN CỨU VÀ XÂY DỰNG HỆ THỐNG DỰ BÁO XU HƯỚNG THỊ TRƯỜNG CHỨNG KHOÁN VÀ ĐÁNH GIÁ CHIẾN LƯỢC ĐẦU TƯ: TỪ MÔ HÌNH HỌC MÁY ĐỊNH LƯỢNG ĐẾN VẬN HÀNH THỰC CHIẾN",
    "student_name": "Nguyễn Hải Nam",
    "student_id": "2221050693",
    "class_name": "Tin học kinh tế K67",
    "supervisor": "TS. / ThS. Phạm Quang Hiển",
    "location_year": "Hà Nội, 2026",
    
    "commitment": [
        "Tôi xin cam đoan đây là công trình nghiên cứu và phát triển phần mềm của riêng tôi, được thực hiện dưới sự hướng dẫn khoa học và tận tình của Thầy giáo hướng dẫn TS./ThS. Phạm Quang Hiển.",
        "Toàn bộ các số liệu thống kê thu thập từ SSI Fast Connect API, kết quả huấn luyện mô hình học máy (LightGBM GBDT, PyTorch Global LSTM), phân tích giá trị giải thích SHAP, số liệu kiểm thử chiến lược Backtesting chu kỳ T+2 và kết quả kiểm định ngẫu nhiên Monte Carlo được trình bày trong báo cáo đều là số liệu trung thực, khách quan, được đo kiểm trực tiếp từ mã nguồn thực tế của dự án.",
        "Mọi sự kế thừa từ các công trình nghiên cứu khoa học trong và ngoài nước, các quy chế giao dịch của VSDC và Sở GDCK TP.HCM (HOSE) đều được trích dẫn nguồn gốc rõ ràng, minh bạch và tuân thủ nghiêm ngặt theo quy chuẩn quốc tế IEEE.",
        "Tôi xin hoàn toàn chịu trách nhiệm trước Hội đồng chấm Đồ án Tốt nghiệp, Nhà trường và Pháp luật về tính liêm chính học thuật của toàn bộ nội dung trong bản báo cáo này."
    ],
    
    "acknowledgments": [
        "Lời đầu tiên, em xin được bày tỏ lòng biết ơn sâu sắc và chân thành nhất tới Thầy giáo hướng dẫn TS./ThS. Phạm Quang Hiển. Trong suốt quá trình thực hiện Đồ án Tốt nghiệp, Thầy đã luôn dành thời gian định hướng phương pháp luận khoa học, kiên nhẫn chỉ bảo, gợi mở các giải pháp kỹ thuật sâu sắc và sửa chữa từng chi tiết báo cáo để em có thể hoàn thiện đề tài một cách trọn vẹn và chuẩn mực nhất.",
        "Em xin chân thành cảm ơn các Thầy Cô giáo trong Ban Chủ nhiệm Khoa Công nghệ Thông tin, các Thầy Cô giáo Bộ môn Tin học kinh tế - Trường Đại học Mỏ - Địa chất đã tận tình truyền đạt cho em những nền tảng tri thức quý báu về công nghệ phần mềm, toán kinh tế, thống kê dữ liệu và tài chính trong suốt 4 năm học tập và rèn luyện dưới mái trường.",
        "Cuối cùng, con xin gửi lời tri ân sâu sắc nhất tới Cha Mẹ và gia đình, những người đã luôn là điểm tựa tinh thần vững chắc, động viên và tạo mọi điều kiện tốt nhất cho con trong suốt quá trình học tập và hoàn thành đồ án tốt nghiệp này."
    ],
    
    "abstract_vi": [
        "Trong bối cảnh thị trường chứng khoán Việt Nam phát triển nhanh chóng với hơn 8 triệu tài khoản nhà đầu tư cá nhân, đa phần các nhà đầu tư mới (F0) thường gặp khó khăn trước các bẫy tâm lý (FOMO), thiếu công cụ quản trị rủi ro khoa học và khó tiếp cận các phương pháp định lượng chuyên nghiệp. Đồ án tốt nghiệp thực hiện nghiên cứu, thiết kế và xây dựng một Hệ thống Dự báo Xu hướng Thị trường Chứng khoán và Đánh giá Chiến lược Đầu tư tích hợp hai giai đoạn hoàn chỉnh: từ Nghiên cứu kiểm định định lượng (Offline Research) đến Hệ thống Vận hành thực chiến theo nhịp thị trường (Online Production Serving).",
        "Về mặt khoa học và phương pháp luận, đồ án loại bỏ bài toán hồi quy thị giá dễ rơi vào bẫy 'bám đuôi trễ 1 phiên', chuyển đổi thành bài toán phân loại có giám sát 3 lớp xu hướng (TĂNG / ĐI NGANG / GIẢM) với ngưỡng lọc nhiễu dao động +-1.0% (T+1) và +-2.0% (T+3) phù hợp với cơ cấu chi phí giao dịch tại Việt Nam. Hệ thống xây dựng bộ 13 đặc trưng kỹ thuật tương đối không thứ nguyên nhằm triệt tiêu hoàn toàn tính không dừng của chuỗi giá nến OHLCV; thiết lập khung kiểm định Walk-Forward 3 cửa sổ mở rộng kết hợp kỹ thuật cô lập ranh giới Purged Boundary và vùng đệm Warm-up Tail nhằm loại trừ 100% hiện tượng rò rỉ dữ liệu tương lai (Zero Data Leakage). Thực nghiệm đối chứng 3 tầng mô hình chứng minh: LightGBM GBDT đạt Macro F1 trung bình 0.2705 (vượt +31.9% so với mốc sàn Heuristic Baseline) và PyTorch Global LSTM đạt Macro F1 0.3412 (vượt +66.4% với độ ổn định cao qua các chu kỳ).",
        "Về mặt kỹ thuật phần mềm và vi cấu trúc, hệ thống hiện thực hóa Động cơ Backtesting phản ánh trung thực chu kỳ thanh toán bù trừ T+2 qua cấu trúc PositionLot, khấu trừ đầy đủ thuế chuyển nhượng 0.10%, phí môi giới 0.15%, trượt giá 0.05% và khớp lô chẵn 100 cổ phiếu. Kiểm định ngẫu nhiên Monte Carlo (100 kịch bản) chứng minh năng lực sinh lời của AI có ý nghĩa thống kê với p-value = 0.0200 < 0.05. Hệ thống được đóng gói hoàn chỉnh theo kiến trúc Full-stack Monorepo gồm Backend FastAPI Async, Web Dashboard Next.js 16 (TradingView Canvas 60fps), phân hệ Quản lý Chiến thuật định lượng chuẩn sàn DNSE EnTrade X (quản lý 2 trạng thái 'Triển khai' vs 'Chưa triển khai') và pipeline huấn luyện lại thực chiến tự động, được bảo chứng bởi bộ kiểm thử tự động 170 unit & integration tests đạt tỷ lệ vượt qua 100%."
    ],
    
    "abstract_en": [
        "With the rapid expansion of the Vietnamese stock market reaching over 8 million retail investor accounts, newcomer investors (F0) consistently struggle with emotional trading biases (FOMO) and lack systematic quantitative risk management tools. This graduation thesis investigates, designs, and implements an End-to-End Stock Trend Prediction and Quantitative Strategy Evaluation System, integrating a rigorous two-stage lifecycle: from Scientific Offline Quantitative Research to Live Production Market Operations.",
        "Scientifically, the study abandons traditional price regression to avoid the trivial one-day lag tracking fallacy, transforming the problem into supervised 3-class trend classification (UP / SIDEWAYS / DOWN) with threshold filtering of +-1.0% (T+1) and +-2.0% (T+3) aligned with domestic transaction friction. A set of 13 dimensionless stationary relative features is engineered from OHLCV panel data to resolve price non-stationarity. A 3-window Walk-Forward expanding framework combined with Purged Boundary and Warm-up Sequence Tail techniques eliminates 100% of lookahead and decision-time leakages. Empirical benchmarks demonstrate that LightGBM GBDT achieves an average Macro F1 of 0.2705 (+31.9% over Naive Heuristic Baseline) and PyTorch Global LSTM achieves 0.3412 (+66.4% improvement with high temporal stability).",
        "Engineering-wise, the platform implements a realistic Backtesting Engine reflecting Vietnam's T+2 settlement cycle via PositionLot management, deducting 0.10% transfer tax, 0.15% brokerage fee, 0.05% slippage, and 100-share board lot constraints. A 100-run Monte Carlo permutation test confirms statistically significant Alpha with empirical p-value = 0.0200 < 0.05. The system is packaged as a production Monorepo combining FastAPI Async backend, Next.js 16 Web Dashboard (60fps TradingView Canvas), a DNSE EnTrade X-inspired Saved Strategies Manager (Active Deployment vs Draft Testing), and an automated continuous retraining pipeline, validated by 170 unit and integration tests passing at 100%."
    ],
    
    "acronyms": [
        ("AI", "Artificial Intelligence", "Trí tuệ nhân tạo"),
        ("API", "Application Programming Interface", "Giao diện lập trình ứng dụng"),
        ("ATC", "At The Closing", "Phiên khớp lệnh định kỳ xác định giá đóng cửa"),
        ("ATO", "At The Opening", "Phiên khớp lệnh định kỳ xác định giá mở cửa"),
        ("CAGR", "Compound Annual Growth Rate", "Tỷ suất tăng trưởng kép năm hóa"),
        ("CCDS v2", "Cookiecutter Data Science v2", "Bộ tiêu chuẩn cấu trúc thư mục khoa học dữ liệu quốc tế"),
        ("CV", "Coefficient of Variation", "Hệ số biến thiên (Độ lệch chuẩn / Trung bình)"),
        ("EMA", "Exponential Moving Average", "Đường trung bình động hàm mũ"),
        ("FC-Data", "Fast Connect Data", "Cổng giao tiếp dữ liệu trực tuyến tốc độ cao của CTCK SSI"),
        ("GBDT", "Gradient Boosted Decision Trees", "Tập hợp cây quyết định tăng cường độ dốc"),
        ("HNX", "Hanoi Stock Exchange", "Sở Giao dịch Chứng khoán Hà Nội"),
        ("HOSE", "Ho Chi Minh Stock Exchange", "Sở Giao dịch Chứng khoán TP. Hồ Chí Minh"),
        ("IPO", "Initial Public Offering", "Phát hành cổ phiếu lần đầu ra công chúng"),
        ("LSTM", "Long Short-Term Memory", "Mạng nơ-ron hồi quy có cổng nhớ dài - ngắn hạn"),
        ("MACD", "Moving Average Convergence Divergence", "Chỉ báo phân kỳ hội tụ trung bình động"),
        ("MDD", "Maximum Drawdown", "Mức sụt giảm vốn tài sản tối đa từ đỉnh"),
        ("OHLCV", "Open - High - Low - Close - Volume", "Bộ 5 dữ liệu nến: Mở cửa, Cao nhất, Thấp nhất, Đóng cửa, Khối lượng"),
        ("OOS", "Out of Sample", "Dữ liệu kiểm thử ngoài mẫu độc lập"),
        ("REST", "Representational State Transfer", "Kiến trúc thiết kế dịch vụ web tiêu chuẩn"),
        ("RNN", "Recurrent Neural Network", "Mạng nơ-ron hồi quy"),
        ("ROI", "Return on Investment", "Tỷ suất lợi nhuận trên vốn đầu tư"),
        ("RSI", "Relative Strength Index", "Chỉ số sức mạnh tương đối (đo xung lực động lượng)"),
        ("SHAP", "SHapley Additive exPlanations", "Phương pháp giải thích mô hình dựa trên giá trị Shapley"),
        ("SMA", "Simple Moving Average", "Đường trung bình động đơn giản"),
        ("SSC", "State Securities Commission", "Ủy ban Chứng khoán Nhà nước"),
        ("TDD", "Test-Driven Development", "Phương pháp phát triển phần mềm hướng kiểm thử"),
        ("TTCK", "Thị trường chứng khoán", "Thị trường chứng khoán"),
        ("VaR", "Value at Risk", "Giá trị chịu rủi ro tại mức tin cậy xác định"),
        ("VSDC", "Vietnam Securities Depository and Clearing Corporation", "Tổng công ty Lưu ký và Bù trừ Chứng khoán Việt Nam"),
        ("XAI", "Explainable Artificial Intelligence", "Trí tuệ nhân tạo có thể giải thích được")
    ]
}
