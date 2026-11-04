"""
Back matter: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN, DANH MỤC TÀI LIỆU THAM KHẢO & PHỤ LỤC
"""

BACK_MATTER_DATA = {
    "conclusion": {
        "title": "KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN",
        "accomplishments": [
            "1. Xây dựng quy trình dữ liệu chuẩn mực và sạch 100%: Hệ thống đã kết nối thành công nguồn dữ liệu nến ngày chính thống từ SSI Fast Connect API, hiện thực hóa cơ chế nạp nến nối đuôi gia tăng (Incremental Sync), cơ chế ghi đĩa nguyên tử (Atomic Write) và lưu trữ bảng Long-format Panel phân vùng Parquet theo chuẩn Cookiecutter Data Science v2 (CCDS v2). Đồng thời, module market_session.py đã thiết lập chốt chặn an toàn căn cứ theo mốc 15:00 ATC giờ Việt Nam (UTC+7), bảo vệ tuyệt đối tính nhân quả thời gian thực.",
            "2. Kỹ nghệ bộ đặc trưng tương đối bảo đảm tính dừng thống kê: Dự án đã chuyển đổi thành công 100% dữ liệu thị giá tuyệt đối sang bộ 13 đặc trưng kỹ thuật tương đối không thứ nguyên (tỷ số vị trí nến, độ lệch chuẩn hóa SMA, hệ số biến thiên CV, tỷ số thanh khoản Volume Ratio, RSI và xung lực thị trường VN-Index). Thiết kế này giải quyết triệt để tính không dừng của chuỗi giá, độc lập với quy mô thị giá và cho phép một mô hình duy nhất có thể học tổng quát hóa trên toàn bộ 30 mã cổ phiếu rổ VN30.",
            "3. Xác lập kỷ luật chống rò rỉ dữ liệu chuỗi thời gian nghiêm ngặt: Trong khâu nghiên cứu, hệ thống cài đặt thành công khung kiểm định Walk-Forward 3 cửa sổ mở rộng kết hợp kỹ thuật Purged Boundary (cắt bỏ nhãn ranh giới) và Warm-up Sequence Tail (bảo toàn 100% mẫu kiểm thử cho LSTM). Trong khâu thực chiến, hệ thống áp dụng kỹ thuật Purged Horizon cắt bỏ 3 phiên chưa diễn ra khi dự phóng T+3 và cô lập 40 phiên Validation Buffer, triệt tiêu 100% hiện tượng rò rỉ dữ liệu tương lai (Lookahead Bias và Decision-Time Leakage).",
            "4. Huấn luyện đối chứng các mô hình học máy đạt hiệu quả vượt trội: Cả hai mô hình AI đều vượt trội rõ rệt so với mốc sàn Heuristic Baseline (Macro F1 = 0.2051): LightGBM GBDT đạt Macro F1 trung bình 0.2705 (+31.9%) với năng lực nhận diện pha đi ngang xuất sắc; PyTorch Global LSTM đạt Macro F1 trung bình 0.3412 (+66.4%) với độ ổn định cao qua các chu kỳ. Đặc biệt, mô hình thực chiến học trên 4.425 mẫu tích lũy đạt Macro F1 0.3875 (LSTM) và Accuracy 56.0% (LightGBM).",
            "5. Động cơ Backtesting phản ánh trung thực vi cấu trúc thị trường Việt Nam: Hệ thống mô phỏng chính xác chu kỳ bù trừ T+2 qua cấu trúc PositionLot, khớp lệnh tại giá Open_{t+1} kèm trượt giá 0.05%, khấu trừ đủ 0.15% phí môi giới, 0.10% thuế chuyển nhượng và lô chẵn 100 cổ phiếu. Kiểm định ngẫu nhiên Monte Carlo (100 kịch bản) chứng minh năng lực sinh lời của AI có ý nghĩa thống kê với p-value = 0.0200 < 0.05 (bác bỏ giả thuyết ăn may ngẫu nhiên).",
            "6. Hiện thực hóa hệ thống Full-stack Monorepo hoàn chỉnh và kiểm thử toàn diện: Xây dựng Backend FastAPI Async, Web Dashboard Next.js 16 (TradingView Canvas 60fps), tích hợp Phân hệ Quản lý Chiến thuật cá nhân chuẩn sàn DNSE EnTrade X (quản lý 2 trạng thái 'Triển khai' vs 'Chưa triển khai') và đóng gói Docker Compose, được bảo chứng bởi bộ kiểm thử tự động 170 unit & integration tests đạt tỷ lệ vượt qua 100%."
        ],
        "limitations": [
            "1. Phạm vi dữ liệu hiện tại tập trung chủ yếu vào chuỗi dữ liệu định lượng kỹ thuật (giá nến OHLCV và khối lượng giao dịch), chưa tích hợp các nguồn thông tin phi cấu trúc như tin tức tài chính hàng ngày, báo cáo tài chính phân tích chi tiết từng quý và chỉ số tâm lý trên các diễn đàn mạng xã hội.",
            "2. Các mô hình học máy chuỗi thời gian có độ trễ nhất định trước các sự kiện bất khả kháng vĩ mô mang tính đột ngột, các cú sốc địa chính trị hoặc các phiên can thiệp bất thường của thị trường ('thiên nga đen').",
            "3. Bộ lọc điều kiện chiến lược cần được bổ sung thêm cơ chế nhận diện bộ lọc trạng thái thị trường chung (Market Regime Filter) để chủ động cấm mở các vị thế thăm dò sớm trong các giai đoạn toàn thị trường bước vào pha suy thoái sâu hoặc điều chỉnh mạnh."
        ],
        "future_work": [
            "1. Nghiên cứu ứng dụng Mô hình Nền tảng Chuỗi thời gian (Time Series Foundation Models): Thử nghiệm fine-tune các mô hình nền tảng tiền huấn luyện quy mô lớn (như TimesFM của Google Research, Lag-Llama, PatchTST) làm mô hình đối chứng nâng cao trên thị trường chứng khoán Việt Nam.",
            "2. Xây dựng Mạng Nơ-ron Đồ thị (Graph Neural Networks - GNN): Mô hình hóa cấu trúc quan hệ sở hữu chéo, chuỗi cung ứng liên ngành và sự dịch chuyển của dòng tiền luân chuyển giữa các nhóm ngành trong rổ VN30.",
            "3. Tích hợp Mô hình Ngôn ngữ Lớn và Hệ thống Đa Tác tử (LLM & Multi-Agent Financial Reasoning): Ứng dụng công nghệ RAG (Retrieval-Augmented Generation) kết hợp LLM để tự động đọc hiểu tin tức báo chí tài chính tiếng Việt, xây dựng hệ thống đa tác tử (Multi-Agent) hỗ trợ phân tích định tính song hành cùng các tín hiệu định lượng."
        ]
    },
    
    "references": [
        "[1] F. Zhang, Z. Li, S. Peng, and Y. Chen, \"When Alpha Disappears: A One-Switch Benchmark for Decision-Time Leakage in Financial Backtests,\" arXiv preprint arXiv:2605.23959, May 2026. [Online]. Available: https://arxiv.org/abs/2605.23959",
        "[2] M. López de Prado, Advances in Financial Machine Learning, Hoboken, NJ, USA: John Wiley & Sons, 2018, ch. 3 (\"Financial Data Structures\") & ch. 5 (\"Fractionally Differentiated Features\").",
        "[3] A. Chen, \"A Statistical-Finance Benchmark for Same-Day Directional Stock Prediction: Walk-Forward Evidence from SPY,\" arXiv preprint arXiv:2608.26106, May 2026. [Online]. Available: https://arxiv.org/abs/2608.26106",
        "[4] M. López de Prado, Advances in Financial Machine Learning, Hoboken, NJ, USA: John Wiley & Sons, 2018, ch. 7 (\"Cross-Validation in Finance: Purged K-Fold\").",
        "[5] L. Grinsztajn, E. Oyallon, and G. Varoquaux, \"Why do tree-based models still outperform deep learning on tabular data?,\" in Advances in Neural Information Processing Systems (NeurIPS), vol. 35, Dec. 2022, pp. 507–520. [Online]. Available: https://arxiv.org/abs/2207.08815",
        "[6] B. Lim, S. Zohren, and S. Roberts, \"Enhancing Time Series Momentum Strategies Using Deep Neural Networks,\" The Journal of Financial Data Science, vol. 1, no. 4, pp. 19–38, Fall 2019, doi: 10.3905/jfds.2019.1.019. [Online]. Available: https://arxiv.org/abs/1904.04912",
        "[7] A. N. Angelopoulos and S. Bates, \"A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification,\" arXiv preprint arXiv:2107.07511, Jul. 2021 (revised 2023). [Online]. Available: https://arxiv.org/abs/2107.07511",
        "[8] I. Gibbs and E. Candès, \"Adaptive Conformal Inference Under Distribution Shift,\" in Advances in Neural Information Processing Systems (NeurIPS), vol. 34, Dec. 2021, pp. 1660–1672. [Online]. Available: https://arxiv.org/abs/2106.00170",
        "[9] S. M. Lundberg and S.-I. Lee, \"A Unified Approach to Interpreting Model Predictions,\" in Advances in Neural Information Processing Systems (NeurIPS), vol. 30, Dec. 2017, pp. 4765–4774. [Online]. Available: https://arxiv.org/abs/1705.07874",
        "[10] Trung tâm Lưu ký Chứng khoán Việt Nam (VSDC), \"Quy chế hoạt động bù trừ và thanh toán giao dịch chứng khoán,\" Quyết định số 109/QĐ-VSD, ban hành ngày 19/08/2022.",
        "[11] D. H. Bailey and M. López de Prado, \"The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality,\" The Journal of Portfolio Management, vol. 40, no. 5, pp. 94–107, Summer 2014, doi: 10.3905/jpm.2014.40.5.094.",
        "[12] D. Yin, T. Miki, V. Lesnichenko, and V. Gural, \"Implementation Risk in Portfolio Backtesting: A Previously Unquantified Source of Error,\" arXiv preprint arXiv:2603.20319, Mar. 2026. [Online]. Available: https://arxiv.org/abs/2603.20319",
        "[13] R. Löw, S. Maier-Paape, and A. Platen, \"Correctness of Backtest Engines,\" Computational Management Science, vol. 15, no. 3, pp. 443–465, Jul. 2018. [Online]. Available: https://arxiv.org/abs/1509.08248",
        "[14] W. Brock, J. Lakonishok, and B. LeBaron, \"Simple Technical Trading Rules and the Stochastic Properties of Stock Returns,\" The Journal of Finance, vol. 47, no. 5, pp. 1731–1764, Dec. 1992, doi: 10.1111/j.1540-6261.1992.tb04681.x.",
        "[15] P. Ernst, J. Thompson, and Y. Miao, \"Portfolio Selection: The Power of Equal Weight,\" arXiv preprint arXiv:1602.00782, Feb. 2016. [Online]. Available: https://arxiv.org/abs/1602.00782",
        "[16] K.-L. Bisdoulis, \"Assets Forecasting with Feature Engineering and Transformation Methods for LightGBM,\" arXiv preprint arXiv:2501.07580, Dec. 2024 (revised Jan. 2025). [Online]. Available: https://arxiv.org/abs/2501.07580",
        "[17] Bộ Tài chính, \"Quy định giao dịch cổ phiếu, chứng chỉ quỹ niêm yết, đăng ký giao dịch...\", Thông tư số 120/2020/TT-BTC; kết hợp Thông tư số 111/2013/TT-BTC hướng dẫn Luật Thuế TNCN.",
        "[18] B. Lim, S. O. Arik, N. Loeff, and T. Pfister, \"Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting,\" International Journal of Forecasting, vol. 37, no. 4, pp. 1748–1764, Oct.–Dec. 2021, doi: 10.1016/j.ijforecast.2021.03.012. [Online]. Available: https://arxiv.org/abs/1912.09363",
        "[19] R. Green, H. Day, Z. S. Abdallah, and T. M. Silva Filho, \"Epistemic Error Decomposition for Multi-step Time Series Forecasting: Rethinking Bias-Variance in Recursive and Direct Strategies,\" arXiv preprint arXiv:2511.11461, Nov. 2025. [Online]. Available: https://arxiv.org/abs/2511.11461"
    ],
    
    "appendix": [
        {
            "title": "Phụ lục A: Bảng Cấu hình Siêu tham số Mô hình Học máy",
            "content": [
                "1. Siêu tham số Mô hình LightGBM GBDT (DEFAULT_LGB_PARAMS):",
                "- objective: 'multiclass', num_class: 3, metric: 'multi_logloss'",
                "- max_depth: 5 (khống chế chiều sâu cây chống quá khớp)",
                "- num_leaves: 20, min_child_samples: 20",
                "- learning_rate: 0.03, subsample: 0.8, colsample_bytree: 0.8",
                "- n_estimators: 300, early_stopping_rounds: 30",
                "2. Siêu tham số Mạng nơ-ron PyTorch Global LSTM:",
                "- input_size: 14 (13 đặc trưng tương đối + 1 mã Symbol_Code)",
                "- hidden_size: 64, num_layers: 2 (stacked LSTM), dropout: 0.2",
                "- output_size: 3 (Softmax 3 lớp: Giảm, Đi ngang, Tăng)",
                "- sequence_length: 20 phiên, batch_size: 32",
                "- optimizer: Adam(lr = 0.001, weight_decay = 1e-4), loss: CrossEntropyLoss",
                "- epochs: 30, early_stopping_patience: 10"
            ]
        },
        {
            "title": "Phụ lục B: Hướng dẫn Cài đặt và Khởi chạy Hệ thống Monorepo",
            "content": [
                "1. Cài đặt môi trường Python với uv:",
                "   curl -LsSf https://astral.sh/uv/install.sh | sh",
                "   cd apps/ml && uv sync",
                "   cd ../api && uv sync",
                "2. Chạy kiểm thử tự động:",
                "   uv run pytest apps/ml/tests/ -v",
                "   uv run pytest apps/api/tests/ -v",
                "   cd apps/web && npm test",
                "3. Khởi chạy toàn bộ hệ thống bằng Docker Compose:",
                "   docker compose -f infra/docker-compose.yml up -d",
                "4. Truy cập giao diện:",
                "   - Web Dashboard: http://localhost:3000",
                "   - Swagger API Docs: http://localhost:8000/docs",
                "   - PostgreSQL Database: localhost:5432 (database: vn_stock)"
            ]
        }
    ]
}
