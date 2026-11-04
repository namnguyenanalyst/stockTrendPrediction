"""
Tables data for Graduation Thesis
"""

TABLES_DATA = {
    "table_1_1": {
        "title": "Bảng 1.1: So sánh đối chiếu các công trình nghiên cứu trong và ngoài nước",
        "headers": ["Nhóm nghiên cứu", "Phương pháp & Mô hình", "Ưu điểm chính", "Khoảng trống / Hạn chế"],
        "rows": [
            ["Nghiên cứu quốc tế cổ điển (Fama 1970, Box-Jenkins)", "EMH, ARIMA, GARCH", "Nền tảng lý thuyết xác suất thống kê vững chắc", "Giả định tuyến tính, không nắm bắt được phi tuyến và mẫu hình phức tạp"],
            ["Nghiên cứu Deep Learning (Lim et al. 2019, 2021)", "Deep Momentum, Multi-horizon LSTM", "Nắm bắt quan hệ chuỗi đa quy mô thời gian xuất sắc", "Chi phí tính toán cao, dễ quá khớp nếu không có cơ chế chuẩn hóa độc lập"],
            ["Nghiên cứu Tabular GBDT (Grinsztajn NeurIPS 2022)", "LightGBM, XGBoost, CatBoost", "Kháng nhiễu tốt, bảo toàn cấu trúc bảng, học hàm biên gãy khúc", "Thường xử lý đơn phiên, cần kỹ nghệ đặc trưng tương đối bảo đảm tính dừng"],
            ["Nghiên cứu trong nước hiện nay", "Hồi quy giá SVM, LSTM trên VN-Index", "Khảo sát trên dữ liệu Việt Nam", "Dính bẫy hồi quy trễ 1 phiên, rò rỉ dữ liệu, bỏ qua vi cấu trúc T+2 và thuế phí"],
            ["Đề tài đồ án (Đề xuất)", "LightGBM + PyTorch LSTM + Backtest T+2 + DNSE EnTrade X", "Phân loại 3 lớp lọc nhiễu, 13 đặc trưng dừng, Walk-Forward Purged Boundary, Monte Carlo", "Được đóng gói thành hệ thống thực chiến Full-stack Monorepo hoàn chỉnh"]
        ]
    },
    "table_1_2": {
        "title": "Bảng 1.2: Danh mục 5 mã cổ phiếu VN30 nghiên cứu trọng điểm",
        "headers": ["Mã CK", "Tên doanh nghiệp", "Ngành kinh tế trụ cột", "Sàn niêm yết", "Tỷ trọng vốn hóa & Vai trò"],
        "rows": [
            ["VIC", "Tập đoàn Vingroup", "Bất động sản & Công nghiệp đa ngành", "HOSE", "Trụ cột vốn hóa hàng đầu, dẫn dắt tâm lý thị trường chung"],
            ["HPG", "Tập đoàn Hòa Phát", "Thép & Công nghiệp sản xuất nặng", "HOSE", "Đại diện chu kỳ kinh tế sản xuất, thanh khoản lớn nhất thị trường"],
            ["FPT", "Công ty Cổ phần FPT", "Công nghệ thông tin & Viễn thông", "HOSE", "Cổ phiếu tăng trưởng bền vững, đại diện nhóm ngành công nghệ cao"],
            ["VNM", "CTCP Sữa Việt Nam (Vinamilk)", "Hàng tiêu dùng thiết yếu & Thực phẩm", "HOSE", "Cổ phiếu phòng thủ dòng tiền lớn, tỷ lệ chi trả cổ tức cao"],
            ["MWG", "CTCP Đầu tư Thế Giới Di Động", "Bán lẻ hàng tiêu dùng kỹ thuật số", "HOSE", "Hàn thử biểu sức mua nội địa và chu kỳ tiêu dùng bán lẻ"]
        ]
    },
    "table_2_1": {
        "title": "Bảng 2.1: Tổng hợp công thức toán học và ý nghĩa kinh tế các chỉ báo kỹ thuật cốt lõi",
        "headers": ["Chỉ báo kỹ thuật", "Công thức tính toán (Thuần text)", "Ý nghĩa kinh tế & Tín hiệu nhận diện"],
        "rows": [
            ["SMA 20/50/200", "SMA_k(t) = (Close_t + ... + Close_{t-k+1}) / k", "Đường xu hướng trung bình động; giá nằm trên đường SMA xác nhận chu kỳ tăng giá"],
            ["EMA 12/26", "EMA_t = Close_t * alpha + EMA_{t-1} * (1 - alpha)", "Đường trung bình hàm mũ ưu tiên dữ liệu gần nhất, giảm độ trễ phản ứng so với SMA"],
            ["RSI 14", "RSI = 100 - (100 / (1 + Avg_Gain / Avg_Loss))", "Dao động 0 - 100; RSI > 70 là vùng quá mua rủi ro, RSI < 30 là vùng quá bán bắt đáy"],
            ["MACD (12, 26, 9)", "MACD = EMA_12 - EMA_26; Signal = EMA_9(MACD)", "Giao cắt MACD cắt lên Signal báo hiệu động lượng tăng; cắt xuống báo hiệu động lượng giảm"],
            ["Bollinger Bands", "Upper/Lower = SMA_20 +- 2 * Std_20", "Dải biên độ dao động giá; co hẹp báo hiệu sắp bùng nổ, chạm biên báo hiệu cản kỹ thuật"],
            ["Volume Ratio", "Vol_Ratio = Volume_t / SMA_Vol_20(t)", "Chuẩn hóa thanh khoản; Vol_Ratio > 1.5 xác nhận dòng tiền lớn nhập cuộc quyết liệt"]
        ]
    },
    "table_2_2": {
        "title": "Bảng 2.2: So sánh lý thuyết giữa mô hình dạng cây GBDT và Học sâu Deep Learning trên dữ liệu bảng",
        "headers": ["Tiêu chí so sánh", "Mô hình dạng cây (LightGBM GBDT)", "Mô hình mạng nơ-ron sâu (Deep Learning)", "Ý nghĩa trên dữ liệu nến tài chính"],
        "rows": [
            ["Tính kháng đặc trưng nhiễu", "Rất cao (tự động bỏ qua đặc trưng vô nghĩa khi phân nhánh)", "Kém (Backpropagation buộc cập nhật trọng số cho cả biến rác)", "Dữ liệu nến chứa nhiều tương quan giả; GBDT ít bị quá khớp"],
            ["Bảo toàn cấu trúc bảng", "Hoàn hảo (phân chia trực giao theo từng cột đặc trưng riêng)", "Bị phá vỡ (phép nhân ma trận xoay làm trộn lẫn các biến)", "Cột RSI và cột Volume mang ý nghĩa vật lý riêng, không thể pha trộn"],
            ["Học biên quyết định gãy khúc", "Rất tốt (là hàm hằng từng khúc tự nhiên)", "Kém (có thiên kiến làm mịn hàm trơn Smoothness Bias)", "Quy luật tài chính thường gãy khúc tại các mốc tâm lý (cắt lỗ -5%, trần/sàn)"],
            ["Tốc độ huấn luyện", "Siêu nhanh (cơ chế GOSS và EFB tăng tốc 10x)", "Chậm (đòi hỏi lặp nhiều epochs qua GPU/CPU)", "Cho phép huấn luyện lại thực chiến (Continuous Retraining) trong vài giây"]
        ]
    },
    "table_3_1": {
        "title": "Bảng 3.1: Ma trận 13 đặc trưng kỹ thuật tương đối không thứ nguyên trong features.py",
        "headers": ["Tên đặc trưng", "Công thức toán học thuần text", "Nhóm bản chất", "Đặc tính chuỗi thời gian"],
        "rows": [
            ["Open_Close_Ratio", "(Open_t - Close_t) / Close_t", "Vị trí thân nến", "Dừng I(0), không thứ nguyên"],
            ["High_Close_Ratio", "(High_t - Close_t) / Close_t", "Bóng nến trên", "Dừng I(0), không thứ nguyên"],
            ["Low_Close_Ratio", "(Low_t - Close_t) / Close_t", "Bóng nến dưới", "Dừng I(0), không thứ nguyên"],
            ["HL_Ratio", "(High_t - Low_t) / Close_t", "Biên độ nội phiên", "Dừng I(0), không thứ nguyên"],
            ["SMA_20_Dev", "(Close_t - SMA_20) / SMA_20", "Xu hướng ngắn hạn", "Dừng I(0), không thứ nguyên"],
            ["SMA_50_Dev", "(Close_t - SMA_50) / SMA_50", "Xu hướng trung hạn", "Dừng I(0), không thứ nguyên"],
            ["SMA_200_Dev", "(Close_t - SMA_200) / SMA_200", "Xu hướng dài hạn", "Dừng I(0), không thứ nguyên"],
            ["CV_50", "Std_50 / SMA_50", "Hệ số biến thiên trung hạn", "Dừng I(0), không thứ nguyên"],
            ["CV_200", "Std_200 / SMA_200", "Hệ số biến thiên dài hạn", "Dừng I(0), không thứ nguyên"],
            ["Vol_Ratio", "Volume_t / SMA_Vol_20", "Thanh khoản tương đối", "Dừng I(0), không thứ nguyên"],
            ["RSI", "RSI_14(t)", "Xung lực động lượng", "Dừng I(0), khoảng [0, 100]"],
            ["Return_1d", "(Close_t - Close_{t-1}) / Close_{t-1}", "Quán tính ngắn hạn", "Dừng I(0), không thứ nguyên"],
            ["VNINDEX_Return_1d", "(VNINDEX_t - VNINDEX_{t-1}) / VNINDEX_{t-1}", "Xung lực toàn thị trường", "Dừng I(0), không thứ nguyên"]
        ]
    },
    "table_3_2": {
        "title": "Bảng 3.2: Danh mục yêu cầu chức năng thực chiến (FR-01 đến FR-08)",
        "headers": ["Mã FR", "Tên yêu cầu chức năng", "Mô tả chi tiết chức năng", "Mức độ ưu tiên"],
        "rows": [
            ["FR-01", "Đồng bộ nến nối đuôi gia tăng", "Kết nối SSI FC-Data, chỉ tải các phiên mới từ ngày chốt cuối, ghi đĩa nguyên tử", "Bắt buộc (P0)"],
            ["FR-02", "Kỹ nghệ đặc trưng & Quản lý phiên", "Tính 13 chỉ báo tương đối, tự động chốt phiên theo mốc 15:00 ATC qua market_session.py", "Bắt buộc (P0)"],
            ["FR-03", "Suy luận AI & Quỹ đạo T+3", "Xuất tín hiệu Softmax 3 lớp, mức tin cậy và Quỹ đạo 3 phiên theo chu kỳ thanh toán VSDC", "Bắt buộc (P0)"],
            ["FR-04", "Tiến trình Tự trị Huấn luyện lại Định kỳ", "Worker tự động định kỳ qua header secret X-Internal-Worker-Secret, Purged Horizon 3 phiên, Validation Buffer 40 phiên", "Bắt buộc (P0)"],
            ["FR-05", "Động cơ Backtest T+2 & Monte Carlo", "Khớp lệnh Open_{t+1}, quản lý PositionLot T+2, trừ phí 0.15%, thuế 0.10%, lô 100, 25 chỉ số", "Bắt buộc (P0)"],
            ["FR-06", "Quản lý Chiến thuật DNSE EnTrade X", "2 chế độ: Manager ('Triển khai' vs 'Chưa triển khai') & Builder (12 đk mua/bán, 8 presets)", "Bắt buộc (P0)"],
            ["FR-07", "Giao diện Web Dashboard Trực quan", "Biểu đồ Canvas TradingView 60fps, nến FireAnt kết hợp Quỹ đạo T+3, Equity Curve", "Bắt buộc (P0)"],
            ["FR-08", "Quản trị Định danh IAM & Thống kê", "Quản lý tài khoản, RBAC và 5 chỉ số thống kê tổng hợp (PoLP: không lộ chiến lược/dữ liệu người dùng)", "Bắt buộc (P0)"]
        ]
    },
    "table_4_1": {
        "title": "Bảng 4.1: Cấu hình phân chia 3 cửa sổ Walk-Forward Expanding Windows trong khâu nghiên cứu",
        "headers": ["Cửa sổ", "Tỷ lệ tập Train (Số mẫu)", "Tỷ lệ tập Validation (Số mẫu)", "Tỷ lệ tập Test ngoài mẫu (Số mẫu)", "Kỹ thuật chống rò rỉ"],
        "rows": [
            ["Cửa sổ 1 (W1)", "50% thời gian (2.140 mẫu)", "15% thời gian (645 mẫu)", "15% thời gian (640 mẫu)", "Purged Boundary ranh giới + Warm-up 19 phiên"],
            ["Cửa sổ 2 (W2)", "60% thời gian (2.570 mẫu)", "15% thời gian (640 mẫu)", "15% thời gian (645 mẫu)", "Purged Boundary ranh giới + Warm-up 19 phiên"],
            ["Cửa sổ 3 (W3)", "70% thời gian (2.995 mẫu)", "15% thời gian (645 mẫu)", "15% thời gian (645 mẫu - 129 phiên OOS)", "Purged Boundary ranh giới + Warm-up 19 phiên"]
        ]
    },
    "table_4_2": {
        "title": "Bảng 4.2: Danh mục các REST API Endpoints chính của hệ thống Backend FastAPI",
        "headers": ["Phương thức", "Đường dẫn (Endpoint)", "Nhóm chức năng", "Mô tả nghiệp vụ", "Dữ liệu trả về"],
        "rows": [
            ["GET", "/api/stocks/history", "Dữ liệu thị trường", "Truy vấn chuỗi nến ngày OHLCV phục vụ biểu đồ", "StockHistoryResponse"],
            ["GET", "/api/stocks/indicators", "Dữ liệu thị trường", "Truy vấn chuỗi 13 đặc trưng kỹ thuật tương đối", "StockIndicatorsResponse"],
            ["GET", "/api/stocks/market-board", "Bảng giá trực tuyến", "Bảng giá trực tuyến rổ VN30 kèm thanh khoản", "MarketBoardResponse"],
            ["POST", "/api/stocks/sync", "Phiên & Đồng bộ", "Kích hoạt đồng bộ nến nối đuôi gia tăng từ SSI", "Status: success"],
            ["GET", "/api/predict/live", "Suy luận AI", "Suy luận Softmax 3 lớp kèm Quỹ đạo dự phóng T+3", "PredictionResponse"],
            ["GET", "/api/predict/status", "Trạng thái mô hình", "Kiểm tra phiên nến ATC chốt và thời điểm cập nhật mô hình gần nhất", "PredictStatusResponse"],
            ["POST", "/api/predict/retrain", "Huấn luyện tự trị nội bộ", "Worker định kỳ gọi nội bộ kèm X-Internal-Worker-Secret (chống DoS)", "Status & Training Info"],
            ["POST", "/api/backtest/run", "Động cơ Backtest", "Chạy kiểm thử tương tác đơn mã chu kỳ T+2", "BacktestResponse (25 chỉ số)"],
            ["POST", "/api/backtest/advanced", "Động cơ Backtest", "Giả lập danh mục đa mã theo bộ lọc DNSE EnTrade X", "AdvancedBacktestResponse"],
            ["GET", "/api/v1/admin/stats", "Quản trị hệ thống", "Thống kê tổng hợp 5 chỉ số người dùng cho Admin theo chuẩn PoLP", "AdminStatsResponse"]
        ]
    },
    "table_5_1": {
        "title": "Bảng 5.1: Kết quả thực nghiệm mô hình cơ sở không tham số Naive Heuristic Baseline",
        "headers": ["Cửa sổ Walk-Forward", "Accuracy (%)", "Macro Precision", "Macro Recall", "Macro F1-score"],
        "rows": [
            ["Cửa sổ 1 (W1)", "45.16%", "0.1505", "0.3333", "0.2074"],
            ["Cửa sổ 2 (W2)", "40.00%", "0.1333", "0.3333", "0.1905"],
            ["Cửa sổ 3 (W3)", "48.37%", "0.1612", "0.3333", "0.2173"],
            ["Trung bình (Mean +- Std)", "44.51% +- 3.46%", "0.1483 +- 0.0115", "0.3333 +- 0.0000", "0.2051 +- 0.0111"]
        ]
    },
    "table_5_2": {
        "title": "Bảng 5.2: Kết quả thực nghiệm mô hình học máy dạng bảng LightGBM GBDT Classifier",
        "headers": ["Cửa sổ Walk-Forward", "Accuracy (%)", "Macro Precision", "Macro Recall", "Macro F1-score", "Mức cải thiện F1"],
        "rows": [
            ["Cửa sổ 1 (W1)", "46.25%", "0.3340", "0.3479", "0.2477", "+19.4% so với Baseline"],
            ["Cửa sổ 2 (W2)", "42.81%", "0.3541", "0.3644", "0.2989", "+56.9% so với Baseline"],
            ["Cửa sổ 3 (W3)", "44.03%", "0.3402", "0.3512", "0.2647", "+21.8% so với Baseline"],
            ["Trung bình (Mean +- Std)", "44.36% +- 1.43%", "0.3428 +- 0.0084", "0.3545 +- 0.0071", "0.2705 +- 0.0213", "+31.9% (Vượt trội mốc sàn)"]
        ]
    },
    "table_5_3": {
        "title": "Bảng 5.3: Kết quả thực nghiệm mô hình học sâu chuỗi thời gian PyTorch Global LSTM Classifier",
        "headers": ["Cửa sổ Walk-Forward", "Accuracy (%)", "Macro Precision", "Macro Recall", "Macro F1-score", "Mức cải thiện F1"],
        "rows": [
            ["Cửa sổ 1 (W1)", "37.97%", "0.3488", "0.3549", "0.3358", "+61.9% so với Baseline"],
            ["Cửa sổ 2 (W2)", "33.33%", "0.3496", "0.3438", "0.3359", "+76.3% so với Baseline"],
            ["Cửa sổ 3 (W3)", "39.69%", "0.3621", "0.3698", "0.3518 (Đỉnh)", "+61.9% so với Baseline"],
            ["Trung bình (Mean +- Std)", "37.00% +- 2.69%", "0.3535 +- 0.0061", "0.3562 +- 0.0107", "0.3412 +- 0.0075", "+66.4% (Độ ổn định rất cao)"]
        ]
    },
    "table_5_4": {
        "title": "Bảng 5.4: Bảng tổng hợp 25 chỉ số định lượng tài chính Backtest Out-of-Sample trên 5 mã VN30",
        "headers": ["Chỉ số định lượng tài chính", "Cổ phiếu VIC", "Cổ phiếu VNM", "Cổ phiếu HPG", "Cổ phiếu FPT", "Cổ phiếu MWG"],
        "rows": [
            ["Vốn khởi điểm", "100.000.000 VNĐ", "100.000.000 VNĐ", "100.000.000 VNĐ", "100.000.000 VNĐ", "100.000.000 VNĐ"],
            ["Vốn kết thúc ròng", "186.237.940 VNĐ", "102.641.564 VNĐ", "89.739.387 VNĐ", "93.980.207 VNĐ", "87.737.545 VNĐ"],
            ["Tỷ suất lợi nhuận (ROI %)", "+86.24%", "+2.64%", "-10.26%", "-6.02%", "-12.26%"],
            ["ROI Chiến lược Buy & Hold", "+62.86%", "+7.34%", "-4.45%", "-1.07%", "-4.29%"],
            ["Alpha so với Buy & Hold", "+23.38%", "-4.70%", "-5.81%", "-4.95%", "-7.98%"],
            ["Tỷ số Sharpe năm hóa (Rf=4%)", "3.1684 (Xuất sắc)", "+0.1543", "-0.9754", "-0.3853", "-0.6879"],
            ["Tỷ số Sortino năm hóa", "4.5037", "+0.1897", "-1.2140", "-0.4520", "-0.8120"],
            ["Mức sụt giảm tối đa (MDD %)", "14.10% (Bảo vệ tốt)", "10.31%", "20.16%", "21.37%", "27.49%"],
            ["Tỷ lệ thắng (Win Rate %)", "66.67% (2W / 1L)", "100.0% (1W / 0L)", "0.0% (0W / 1L)", "0.0% (0W / 1L)", "0.0% (0W / 1L)"],
            ["Hệ số lợi nhuận (Profit Factor)", "15.20", "Vô cùng (không lỗ)", "0.00", "0.00", "0.00"],
            ["Tổng thuế và phí đã trừ", "1.617.604 VNĐ", "407.011 VNĐ", "374.693 VNĐ", "385.325 VNĐ", "369.653 VNĐ"],
            ["Hành vi quản trị rủi ro AI", "Chốt lời đỉnh sóng", "Bảo toàn vốn dương", "Cắt lỗ, giữ tiền mặt", "Cắt lỗ, giữ tiền mặt", "Cắt lỗ, giữ tiền mặt"]
        ]
    },
    "table_5_5": {
        "title": "Bảng 5.5: Kết quả thực nghiệm kiểm định Monte Carlo 100 lần trên cổ phiếu VIC",
        "headers": ["Thông số thống kê", "Tỷ số Sharpe ngẫu nhiên", "Tỷ suất sinh lời ROI % ngẫu nhiên", "Chiến lược AI", "Kết luận kiểm định"],
        "rows": [
            ["Giá trị trung bình (Mean)", "1.0102", "+18.42%", "3.1684 (Sharpe)", "AI vượt trội phân phối ngẫu nhiên"],
            ["Độ lệch chuẩn (Std)", "1.0182", "19.85%", "--", "Phương sai ngẫu nhiên cao"],
            ["Giá trị trung vị (Median)", "0.9419", "+16.30%", "--", "--"],
            ["Phân vị thứ 5 (5th Percentile)", "-0.7302", "-14.20%", "--", "--"],
            ["Phân vị thứ 95 (95th Percentile)", "2.9087", "+54.10%", "--", "Ngưỡng giới hạn ý nghĩa 5%"],
            ["Giá trị thực nghiệm AI", "3.1684 (Vượt phân vị 95%)", "+86.24% (Vượt xa phân vị 95%)", "--", "--"],
            ["Giá trị p-value thực nghiệm", "p = 0.0200 < 0.05", "p = 0.0200 < 0.05", "--", "Bác bỏ H0, Alpha có ý nghĩa thống kê"]
        ]
    },
    "table_5_6": {
        "title": "Bảng 5.6: Kết quả đo kiểm hiệu năng mô hình thực chiến T+3 trên 4.425 mẫu (production_training_info_t3.json)",
        "headers": ["Mô hình thực chiến", "Quy mô tập dữ liệu", "Độ chính xác (Accuracy)", "Macro F1-score", "Weighted F1-score", "Đặc tính ma trận nhầm lẫn"],
        "rows": [
            ["LightGBM GBDT (T+3)", "4.425 mẫu (4.225 Train / 200 Val)", "56.0%", "0.2416", "0.4096", "Dự đoán đúng 112/113 phiên đi ngang trong Val; phòng thủ xuất sắc"],
            ["PyTorch LSTM (T+3)", "4.425 mẫu (4.225 Train / 200 Val)", "42.0%", "0.3875 (Đỉnh cao)", "0.4415", "Phân bổ đều 3 lớp: 28 Tăng đúng, 46 Đi ngang đúng, 10 Giảm đúng"]
        ]
    },
    "table_5_7": {
        "title": "Bảng 5.7: Đo kiểm độ trễ và thời gian phản hồi API thực chiến (Latency Benchmarks)",
        "headers": ["Endpoint API", "Phương thức", "Kịch bản đo kiểm", "Thời gian phản hồi (ms)", "Tiêu chuẩn NFR", "Đánh giá"],
        "rows": [
            ["/api/stocks/history", "GET", "Truy vấn 500 nến OHLCV từ Parquet", "85 ms", "< 500 ms", "Đạt chuẩn xuất sắc"],
            ["/api/predict/live", "GET", "Dữ liệu có sẵn, suy luận Softmax T+3", "420 ms", "< 500 ms", "Đạt chuẩn thời gian thực"],
            ["/api/predict/live", "GET", "Kích hoạt đồng bộ nến mới từ SSI FC-Data", "1.150 ms", "< 1.500 ms", "Đạt chuẩn đồng bộ mạng"],
            ["/api/backtest/advanced", "POST", "Chạy giả lập 12 điều kiện DNSE EnTrade X", "640 ms", "< 800 ms", "Đạt chuẩn tính toán nhanh"],
            ["/health", "GET", "Docker healthcheck kiểm tra trạng thái", "12 ms", "< 50 ms", "Đạt chuẩn giám sát"]
        ]
    },
    "table_5_8": {
        "title": "Bảng 5.8: Tổng hợp kết quả 170 unit & integration tests tự động trên Monorepo",
        "headers": ["Phân hệ (Package)", "Công cụ kiểm thử", "Số lượng test cases", "Thời gian chạy", "Tỷ lệ vượt qua (Pass Rate)"],
        "rows": [
            ["apps/ml (ML & Quant Engine)", "PyTest 9.x", "106 tests", "14.82s", "106/106 PASSED (100%)"],
            ["apps/api (Backend REST API)", "PyTest + HTTPX", "45 tests", "6.15s", "45/45 PASSED (100%)"],
            ["apps/web (Frontend Dashboard)", "Vitest + React Testing Library", "19 tests", "4.20s", "19/19 PASSED (100%)"],
            ["Toàn bộ hệ thống Monorepo", "PyTest & Vitest", "170 tests", "25.17s", "170/170 PASSED (100% Hoàn hảo)"]
        ]
    }
}
