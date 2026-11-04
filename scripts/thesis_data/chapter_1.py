"""
Chapter 1: TỔNG QUAN ĐỀ TÀI
"""

CHAPTER_1_DATA = {
    "title": "CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI",
    "sections": [
        {
            "id": "1.1",
            "title": "1.1. LÝ DO CHỌN ĐỀ TÀI",
            "subsections": [
                {
                    "id": "1.1.1",
                    "title": "1.1.1. Bối cảnh kinh tế – công nghệ và tính cấp thiết của đề tài",
                    "paragraphs": [
                        "Thị trường chứng khoán Việt Nam trong giai đoạn 2020 – 2026 đã ghi nhận những bước chuyển mình mạnh mẽ cả về quy mô vốn hóa, thanh khoản lẫn số lượng nhà đầu tư tham gia. Theo số liệu thống kê chính thức từ Tổng công ty Lưu ký và Bù trừ Chứng khoán Việt Nam (VSDC), tính đến cuối năm 2025, toàn thị trường đã vượt mốc 8 triệu tài khoản giao dịch chứng khoán của nhà đầu tư cá nhân, tương đương gần 8% dân số quốc gia. Thị trường chứng khoán ngày càng khẳng định vị thế là kênh dẫn vốn trung và dài hạn thiết yếu của nền kinh tế, đồng thời là kênh đầu tư gia tăng tài sản hấp dẫn đối với đông đảo người dân.",
                        "Tuy nhiên, sự gia tăng nhanh chóng của lớp nhà đầu tư mới (thường được gọi là nhà đầu tư F0) cũng bộc lộ những rủi ro và hạn chế mang tính hệ thống. Đa số các nhà đầu tư cá nhân tham gia thị trường đều thiếu nền tảng kiến thức bài bản về kinh tế vĩ mô, phân tích tài chính doanh nghiệp và đặc biệt là thiếu kỷ luật trong quản trị rủi ro danh mục. Dưới tác động mạnh mẽ của thông tin nhiễu loạn trên các diễn đàn mạng xã hội, nhà đầu tư cá nhân thường xuyên bị chi phối bởi các bẫy tâm lý kinh điển như tâm lý đám đông, lòng tham khi thị trường hưng phấn (FOMO - Fear of Missing Out) và sự hoảng loạn bán tháo ở vùng đáy (Panic Selling). Hậu quả thực tế ghi nhận qua các chu kỳ điều chỉnh sâu của thị trường (điển hình như năm 2022) là hàng trăm nghìn nhà đầu tư cá nhân phải gánh chịu những khoản thua lỗ nặng nề, làm suy giảm niềm tin vào tính minh bạch của thị trường tài chính.",
                        "Song hành cùng bối cảnh kinh tế, sự bùng nổ của cuộc Cách mạng Công nghiệp lần thứ tư với các công nghệ mũi nhọn như Học máy (Machine Learning), Học sâu (Deep Learning) và Dữ liệu lớn (Big Data) đã và đang tái định hình toàn diện ngành tài chính toàn cầu. Tại các thị trường tài chính phát triển (như Mỹ, châu Âu, Nhật Bản), các định chế tài chính và quỹ đầu cơ định lượng (Quant Funds) đã ứng dụng triệt để các thuật toán tăng cường độ dốc (GBDT) và mạng nơ-ron hồi quy chuỗi thời gian (LSTM) để tự động hóa quá trình nhận diện mẫu hình dữ liệu và kiểm soát rủi ro danh mục. Ngược lại, tại Việt Nam, phần lớn các công cụ hỗ trợ nhà đầu tư cá nhân hiện nay vẫn dừng lại ở các đồ thị phân tích kỹ thuật tĩnh truyền thống hoặc các hội nhóm tư vấn mang đậm định kiến cảm tính.",
                        "Trước thực trạng đó, việc nghiên cứu, thiết kế và xây dựng một hệ thống phần mềm hỗ trợ ra quyết định đầu tư ứng dụng trí tuệ nhân tạo và tài chính định lượng, có khả năng vận hành thực chiến bám sát nhịp đập thị trường chứng khoán Việt Nam, là một đòi hỏi vô cùng cấp thiết. Hệ thống không chỉ giúp nhà đầu tư cá nhân tiếp cận các công cụ định lượng khoa học, khách quan, mà còn cung cấp cơ chế phòng vệ vốn tự động trước những biến động khôn lường của thị trường."
                    ]
                },
                {
                    "id": "1.1.2",
                    "title": "1.1.2. Tổng quan tình hình nghiên cứu trong và ngoài nước",
                    "paragraphs": [
                        "Bài toán dự báo xu hướng thị trường chứng khoán và đánh giá chiến lược đầu tư đã thu hút sự quan tâm của nhiều thế hệ các nhà kinh tế học, toán học và kỹ sư khoa học máy tính trên toàn thế giới.",
                        "*Tình hình nghiên cứu trên thế giới:*",
                        "Lý thuyết tài chính cổ điển khởi đầu từ Giả thuyết Thị trường Hiệu quả (Efficient Market Hypothesis - EMH) của Eugene Fama (1970), khẳng định rằng giá chứng khoán luôn phản ánh tức thời và đầy đủ mọi thông tin sẵn có, do đó biến động giá tuân theo bước đi ngẫu nhiên (Random Walk) và không thể dự báo trước để đạt được lợi nhuận vượt trội (Alpha). Tuy nhiên, trường phái Tài chính Hành vi (Behavioral Finance) với các công trình đoạt giải Nobel của Daniel Kahneman và Amos Tversky đã chứng minh rằng các nhà đầu tư trên thị trường không hoàn toàn duy lý; tâm lý bầy đàn và các phản ứng thái quá tạo ra các dị biệt định lượng và mẫu hình xu hướng có tính quy luật.",
                        "Về mặt thuật toán, quá trình nghiên cứu đã trải qua các bước tiến lớn: từ các mô hình kinh tế lượng chuỗi thời gian cổ điển như ARIMA, GARCH; sang mạng nơ-ron hồi quy có cổng nhớ dài - ngắn hạn (Long Short-Term Memory - LSTM) của Sepp Hochreiter và Jürgen Schmidhuber (1997) được Bryan Lim và cộng sự tại Viện Tài chính Định lượng Oxford-Man (2019) chứng minh là có khả năng trích xuất động lượng xu hướng đa chu kỳ xuất sắc; cho đến công trình đột phá tại NeurIPS 2022 của Léo Grinsztajn và cộng sự khẳng định các thuật toán dựa trên cây quyết định tăng cường độ dốc (GBDT như LightGBM) vượt trội mạng nơ-ron sâu trên dữ liệu dạng bảng tài chính.",
                        "Đặc biệt, trong giai đoạn gần đây, giới học thuật quốc tế đặc biệt nhấn mạnh đến tính chuẩn mực trong kiểm định chuỗi thời gian: Marcos López de Prado (2018) xác lập khung Purged Cross-Validation loại trừ rò rỉ ranh giới; Alex Chen (2026) chứng minh việc gán nhãn có ngưỡng lọc nhiễu kết hợp Walk-Forward Validation giúp cải thiện độ chính xác dự báo vượt trội; và F. Zhang cùng cộng sự (2026) cảnh báo hiện tượng rò rỉ thời điểm quyết định (Decision-Time Leakage) làm biến dạng hoàn toàn hiệu quả thực tế của các động cơ backtest.",
                        "*Tình hình nghiên cứu trong nước và các khoảng trống lớn còn tồn tại:*",
                        "Tại Việt Nam, trong những năm gần đây đã có một số công trình nghiên cứu của các trường đại học khối kinh tế và công nghệ thử nghiệm các mô hình học máy (Random Forest, SVM, LSTM) trên chỉ số VN-Index hoặc một số mã cổ phiếu riêng lẻ. Tuy nhiên, qua khảo sát thực tế, tác giả nhận thấy các nghiên cứu trong nước hiện nay đang tồn tại 4 khoảng trống học thuật và kỹ thuật rất lớn:",
                        "1. Bẫy hồi quy giá 'bám đuôi trễ 1 phiên': Hầu hết các nghiên cứu tiếp cận theo hướng hồi quy dự báo mức giá tuyệt đối của ngày mai (Close_{t+1}). Cách tiếp cận này khiến mô hình rơi vào bẫy học vẹt giá trị hôm nay để dự đoán ngày mai (P_hat_{t+1} xấp xỉ P_t), tuy đạt sai số RMSE/MAE nhỏ nhưng hoàn toàn không đưa ra được tín hiệu định hướng hành động (Mua hay Bán).",
                        "2. Rò rỉ dữ liệu tương lai nghiêm ngặt (Lookahead Bias): Nhiều đề tài sử dụng phương pháp chia tập K-Fold ngẫu nhiên hoặc chuẩn hóa dữ liệu toàn cục (StandardScaler fit trên toàn bộ dữ liệu gộp), vô tình để thông tin tương lai rò rỉ vào tập học, tạo ra kết quả kiểm định 'quá khớp ảo'.",
                        "3. Xa rời vi cấu trúc thực tế của thị trường chứng khoán Việt Nam: Các nghiên cứu thường giả định giao dịch lý tưởng (mua bán tự do T+0, không tính phí môi giới, không tính thuế chuyển nhượng, không tính trượt giá và khớp khối lượng lẻ). Trong thực tế, chu kỳ thanh toán bù trừ T+2.5 của VSDC và mức chi phí thuế phí ~0.40%/vòng quay là những rào cản rất lớn, có thể biến một mô hình có lãi trên lý thuyết thành thua lỗ nặng nề trong thực tế.",
                        "4. Thiếu vắng năng lực đóng gói và vận hành thực chiến (Production Serving): Phần lớn các đề tài chỉ dừng lại ở các đoạn mã phân tích tĩnh trong tệp Jupyter Notebook, chưa từng được thiết kế kiến trúc phần mềm hoàn chỉnh, chưa có khả năng kết nối API dữ liệu thời gian thực và chưa có cơ chế quản lý chốt phiên thị trường để phục vụ người dùng."
                    ]
                },
                {
                    "id": "1.1.3",
                    "title": "1.1.3. Tính mới và Đóng góp của đề tài",
                    "paragraphs": [
                        "Nhằm giải quyết trọn vẹn các khoảng trống nói trên, đồ án đề xuất và hiện thực hóa một Hệ thống Phần mềm Tích hợp hoàn chỉnh (End-to-End Monorepo System) kết hợp hài hòa giữa Kỷ luật nghiên cứu khoa học định lượng (Offline Research) và Năng lực kỹ thuật phần mềm vận hành thực chiến (Online Production Serving).",
                        "Các đóng góp cốt lõi của đề tài được tổng hợp qua 6 điểm đổi mới sáng tạo:",
                        "Về mặt Phương pháp luận Khoa học và Tài chính định lượng:",
                        "1. Chuyển đổi toàn diện sang bài toán Phân loại xu hướng 3 lớp có ngưỡng lọc nhiễu: Loại bỏ hoàn toàn bài toán hồi quy giá vô bổ, thiết lập bài toán phân loại 3 lớp (TĂNG / ĐI NGANG / GIẢM) với ngưỡng +-1.0% cho chân trời T+1 và +-2.0% cho chân trời T+3, lọc triệt để nhiễu dao động nhỏ và bù đắp trọn vẹn chi phí giao dịch.",
                        "2. Kỹ nghệ bộ 13 đặc trưng kỹ thuật tương đối không thứ nguyên: Giải quyết triệt để tính không dừng (Non-stationarity) của chuỗi giá nến OHLCV, chuẩn hóa toàn bộ đặc trưng thành các tỷ số độ lệch tương đối không phụ thuộc vào thị giá tuyệt đối, cho phép một mô hình duy nhất học tổng quát hóa trên toàn bộ rổ cổ phiếu VN30.",
                        "3. Khung kiểm định Walk-Forward Purged Boundary và Kiểm định thống kê Monte Carlo: Cài đặt quy trình kiểm định 3 cửa sổ mở rộng kết hợp kỹ thuật cô lập ranh giới Purged Boundary và vùng đệm Warm-up Sequence Tail, triệt tiêu 100% rò rỉ dữ liệu. Thực hiện 100 kịch bản mô phỏng ngẫu nhiên Monte Carlo chứng minh năng lực sinh lời vượt trội của AI có ý nghĩa thống kê (p-value = 0.0200 < 0.05).",
                        "Về mặt Kỹ thuật Phần mềm và Vận hành Thực chiến:",
                        "4. Động cơ Backtesting sát thực tế vi cấu trúc Việt Nam 100%: Quản lý chu kỳ thanh toán bù trừ T+2 theo Quyết định 109/QĐ-VSD của VSDC thông qua cấu trúc PositionLot, chặn hoàn toàn bán non T+0 và bán khống; khấu trừ chuẩn xác thuế chuyển nhượng 0.10%, phí môi giới 0.15%, trượt giá 0.05% và khớp theo lô chẵn 100 cổ phiếu.",
                        "5. Cơ chế quản lý phiên thời gian thực mốc 15:00 ATC và Pipeline Huấn luyện lại thực chiến: Module market_session.py khóa nến dở dang giữa phiên bảo toàn tính nhân quả thời gian thực; pipeline tự động huấn luyện lại trên toàn bộ dữ liệu lịch sử tích lũy với kỹ thuật Purged Horizon 3 phiên và Validation Buffer 40 phiên.",
                        "6. Hệ thống Full-stack Monorepo với Phân hệ Quản lý Chiến thuật chuẩn sàn DNSE EnTrade X: Xây dựng Backend FastAPI Async, Web Dashboard Next.js 16 (TradingView Canvas 60fps), tích hợp phân hệ Quản lý Chiến thuật cá nhân với 2 trạng thái 'Triển khai' (Active) và 'Chưa triển khai' (Draft), được bảo chứng bởi bộ kiểm thử tự động 170 tests đạt tỷ lệ vượt qua 100%."
                    ]
                }
            ]
        },
        {
            "id": "1.2",
            "title": "1.2. MỤC TIÊU CỦA ĐỀ TÀI",
            "subsections": [
                {
                    "id": "1.2.1",
                    "title": "1.2.1. Phát biểu bài toán nghiên cứu",
                    "paragraphs": [
                        "Đề tài giải quyết tích hợp hai bài toán liên hoàn tương ứng với hai pha của vòng đời học máy tài chính:",
                        "*Bài toán 1: Bài toán Nghiên cứu Kiểm định Khoa học (Offline Quantitative Research)*",
                        "Cho tập dữ liệu bảng chuỗi thời gian nến ngày OHLCV đa mã (Long-format Panel) của các cổ phiếu thuộc rổ VN30 và chỉ số VN-Index từ ngày 01/01/2022 đến ngày 23/10/2026. Tại cuối mỗi phiên giao dịch t, sau khi phiên ATC kết thúc, hệ thống trích xuất véc-tơ 13 đặc trưng tương đối không thứ nguyên x_t. Mục tiêu là xây dựng mô hình học máy ánh xạ x_t sang phân bổ xác suất Softmax 3 lớp P(y_t = k | x_t) với k thuộc {0: GIẢM, 1: ĐI NGANG, 2: TĂNG} tại các chân trời T+1 và T+3:",
                        "Nhãn = 2 (TĂNG) nếu Next_Return >= +theta",
                        "Nhãn = 0 (GIẢM) nếu Next_Return <= -theta",
                        "Nhãn = 1 (ĐI NGANG) nếu -theta < Next_Return < +theta",
                        "với ngưỡng theta = 1.0% (T+1) và theta = 2.0% (T+3). Sau đó, mô phỏng khớp lệnh thực tế tại giá mở cửa phiên kế tiếp Open_{t+1} dưới các ràng buộc vi cấu trúc thanh toán bù trừ T+2, thuế chuyển nhượng 0.10%, phí môi giới 0.15% và kiểm định ý nghĩa thống kê bằng phương pháp Monte Carlo.",
                        "*Bài toán 2: Bài toán Vận hành Thực chiến (Online Production Serving)*",
                        "Đóng gói toàn bộ mô hình và quy trình định lượng thành một hệ thống phần mềm phân tầng hoạt động thời gian thực. Hệ thống tự động thu nhận dữ liệu nến mới từ SSI FC-Data API; nhận diện trạng thái phiên thị trường theo mốc chốt 15:00 ATC để suy luận trực tuyến an toàn mà không bị sai lệch thời điểm quyết định; cung cấp dịch vụ huấn luyện lại mô hình thích ứng với dữ liệu mới; và cung cấp giao diện trực quan hỗ trợ nhà đầu tư quản lý các chiến thuật định lượng ở hai trạng thái 'Triển khai' (Active) và 'Chưa triển khai' (Draft)."
                    ]
                },
                {
                    "id": "1.2.2",
                    "title": "1.2.2. Mục tiêu tổng quát",
                    "paragraphs": [
                        "Mục tiêu tổng quát của đề tài là: Nghiên cứu, thiết kế và phát triển thành công một Hệ thống Phần mềm Tích hợp (End-to-End System) ứng dụng học máy và tài chính định lượng, chuyển hóa từ mô hình thực nghiệm khoa học trong phòng thí nghiệm sang một công cụ hỗ trợ ra quyết định đầu tư và quản trị rủi ro vận hành thực chiến trên thị trường chứng khoán Việt Nam, đảm bảo tính liêm chính học thuật, tính khả thi kinh tế và độ ổn định kỹ thuật cao."
                    ]
                },
                {
                    "id": "1.2.3",
                    "title": "1.2.3. Các mục tiêu cụ thể",
                    "paragraphs": [
                        "Để đạt được mục tiêu tổng quát, đề tài xác lập 5 mục tiêu cụ thể có thể đo lường định lượng được:",
                        "1. Xây dựng Data Pipeline tự động chuẩn mực: Thu thập dữ liệu nến ngày chính thống từ SSI Fast Connect API từ 01/01/2022 đến 23/10/2026; thực hiện quy trình kiểm định toàn vẹn 5 tiêu chí; tổ chức lưu trữ dạng bảng Long-format Panel phân vùng Parquet theo chuẩn Cookiecutter Data Science v2 (CCDS v2); xây dựng cơ chế nạp nến nối đuôi gia tăng (Incremental Sync) và quản lý phiên theo mốc 15:00 ATC.",
                        "2. Kỹ nghệ đặc trưng và Khung chống rò rỉ dữ liệu: Trích xuất bộ 13 chỉ báo kỹ thuật tương đối không thứ nguyên; thiết lập khung kiểm định Walk-Forward 3 cửa sổ mở rộng kết hợp kỹ thuật Purged Boundary và Warm-up Sequence Tail, triệt tiêu 100% rò rỉ dữ liệu tương lai.",
                        "3. Huấn luyện đối chứng 3 tầng mô hình: Huấn luyện và đánh giá khách quan 3 mô hình (Naive Baseline, LightGBM GBDT, PyTorch Global LSTM). Mô hình nòng cốt LightGBM phải đạt chỉ số Macro F1 vượt trội mốc sàn tối thiểu ít nhất 25%; mô hình PyTorch LSTM phải chứng minh được tính ổn định cao qua các chu kỳ thị trường.",
                        "4. Xây dựng Động cơ Backtesting sát vi cấu trúc và Kiểm định Monte Carlo: Mô phỏng chính xác chu kỳ bù trừ T+2, khấu trừ phí môi giới 0.15%, thuế 0.10%, trượt giá 0.05%, lô chẵn 100 cổ phiếu; tính toán hệ thống 25+ chỉ số định lượng tài chính chuẩn quốc tế; thực hiện kiểm định hoán vị ngẫu nhiên Monte Carlo (100 kịch bản) đạt mức ý nghĩa thống kê p-value < 0.05.",
                        "5. Hiện thực hóa hệ thống Full-stack Monorepo hoàn chỉnh: Xây dựng Backend RESTful API bằng FastAPI Async (thời gian phản hồi < 500ms); xây dựng Web Dashboard bằng Next.js 16 (TradingView Canvas 60fps) tích hợp Phân hệ Quản lý Chiến thuật chuẩn sàn DNSE EnTrade X; đóng gói Docker Compose và vượt qua 100% bộ kiểm thử tự động gồm 170 unit & integration tests."
                    ]
                }
            ]
        },
        {
            "id": "1.3",
            "title": "1.3. PHẠM VI CỦA ĐỀ TÀI",
            "subsections": [
                {
                    "id": "1.3.1",
                    "title": "1.3.1. Đối tượng nghiên cứu",
                    "paragraphs": [
                        "Đề tài tập trung nghiên cứu các đối tượng khoa học và công nghệ sau:",
                        "* Dữ liệu chuỗi thời gian tài chính nến ngày (OHLCV) và khối lượng giao dịch của các cổ phiếu niêm yết trên thị trường chứng khoán Việt Nam cùng chỉ số thị trường VN-Index.",
                        "* Các phương pháp phân tích kỹ thuật và kỹ nghệ đặc trưng tương đối bảo đảm tính dừng thống kê trên chuỗi thời gian tài chính.",
                        "* Thuật toán học máy dạng bảng tăng cường độ dốc (LightGBM GBDT) và kiến trúc mạng nơ-ron học sâu hồi quy chuỗi thời gian (PyTorch Global LSTM).",
                        "* Các phương pháp luận kiểm định chuỗi thời gian không rò rỉ dữ liệu (Walk-Forward Expanding Windows, Purged Cross-Validation) và các kỹ thuật giải thích mô hình (SHAP, Conformal Prediction Softmax).",
                        "* Vi cấu trúc giao dịch thực tế của Sở GDCK TP.HCM (HOSE) và quy chế bù trừ thanh toán của VSDC.",
                        "* Kiến trúc phần mềm Monorepo phân tầng và quy trình vận hành học máy thực chiến (Production Financial ML Lifecycle)."
                    ]
                },
                {
                    "id": "1.3.2",
                    "title": "1.3.2. Phạm vi nghiên cứu",
                    "paragraphs": [
                        "Phạm vi nghiên cứu của đề tài được giới hạn và khoanh vùng cụ thể theo các chiều kích thước sau:",
                        "a. Về phạm vi không gian (Thị trường và Danh mục cổ phiếu):",
                        "- Sàn giao dịch: Sở Giao dịch Chứng khoán TP. Hồ Chí Minh (HOSE) - thị trường cổ phiếu niêm yết có quy mô vốn hóa lớn nhất và tính minh bạch cao nhất tại Việt Nam.",
                        "- Danh mục nghiên cứu: Rổ chỉ số VN30, trong đó tập trung nghiên cứu thực nghiệm chuyên sâu trên 5 mã cổ phiếu tiêu biểu đại diện cho các ngành kinh tế trụ cột:",
                        "  + VIC (Tập đoàn Vingroup): Đại diện ngành Bất động sản và Công nghiệp đa ngành.",
                        "  + HPG (Tập đoàn Hòa Phát): Đại diện ngành Thép và Công nghiệp nặng.",
                        "  + FPT (Công ty Cổ phần FPT): Đại diện ngành Công nghệ thông tin và Viễn thông.",
                        "  + VNM (Công ty Cổ phần Sữa Việt Nam): Đại diện ngành Tiêu dùng thiết yếu và Thực phẩm.",
                        "  + MWG (Công ty Cổ phần Đầu tư Thế Giới Di Động): Đại diện ngành Bán lẻ hàng tiêu dùng.",
                        "  + Cùng chỉ số toàn thị trường VN-Index đóng vai trò là biến ngoại sinh định hướng dòng tiền chung.",
                        "b. Về phạm vi thời gian (Khoảng dữ liệu thực nghiệm):",
                        "- Giai đoạn dữ liệu: Từ ngày 01/01/2022 đến ngày 23/10/2026, với tổng cộng 1.196 phiên giao dịch liên tục được thu thập chính thức từ SSI Fast Connect API.",
                        "- Tính đại diện chu kỳ:",
                        "  + Năm 2022: Thị trường rơi vào chu kỳ suy thoái sâu (Bear Market) dưới tác động của chính sách thắt chặt tiền tệ và xử lý sai phạm thị trường; giai đoạn này đóng vai trò làm vùng đệm lịch sử khởi động (~250 phiên warm-up history) giúp các chỉ báo chu kỳ dài hạn (SMA_200, CV_200) hội tụ giá trị chuẩn xác.",
                        "  + Giai đoạn 2023 – 2026: Cửa sổ nghiên cứu chính thức (Study Window từ ngày 03/04/2023 với 888 phiên sạch, loại bỏ hoàn toàn ảnh hưởng chia tách cổ phiếu MWG trước đó), ghi nhận thị trường tạo đáy phục hồi, tích lũy phân hóa và bước vào chu kỳ tăng trưởng mới.",
                        "c. Về tần suất dữ liệu và chân trời dự báo:",
                        "- Tần suất nến: Dữ liệu nến ngày (End-of-day / Daily OHLCV). Đề tài không thực hiện giao dịch tần suất cao (High-Frequency Trading) theo tick dữ liệu từng giây do rào cản hạ tầng và vi cấu trúc Việt Nam chưa hỗ trợ giao dịch trong ngày.",
                        "- Chân trời dự báo (Prediction Horizon):",
                        "  + Dự báo định hướng ngắn hạn 1 phiên kế tiếp (T+1).",
                        "  + Dự phóng quỹ đạo xu hướng cho chu kỳ vị thế nắm giữ hoàn chỉnh (T+3), tương thích với chu kỳ thanh toán bù trừ T+2.5 của VSDC.",
                        "d. Về các giả định nghiệp vụ và ràng buộc giao dịch:",
                        "- Chiều vị thế: Chỉ áp dụng vị thế MUA (Long-only), không áp dụng vị thế BÁN KHỐNG (Short-selling) do thị trường chứng khoán cơ sở Việt Nam hiện chưa cho phép bán khống.",
                        "- Thực thi lệnh: Khớp lệnh tại giá mở cửa Open_{t+1} kèm trượt giá thực thi Slippage 0.05%, chặn hoàn toàn lỗi khớp lệnh cùng ngày.",
                        "- Khối lượng: Khớp theo lô chẵn 100 cổ phiếu theo quy định Thông tư 120/2020/TT-BTC.",
                        "- Thuế và phí: Khấu trừ thuế chuyển nhượng 0.10% giá trị bán và phí môi giới 0.15% cả hai chiều mua và bán.",
                        "- Chu kỳ thanh toán bù trừ: Tuân thủ quy chế bù trừ T+2 theo Quyết định 109/QĐ-VSD, từ chối bán khi cổ phiếu chưa về tài khoản."
                    ]
                }
            ]
        },
        {
            "id": "1.4",
            "title": "1.4. NỘI DUNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU",
            "subsections": [
                {
                    "id": "1.4.1",
                    "title": "1.4.1. Các nội dung nghiên cứu chính",
                    "paragraphs": [
                        "Đề tài xác lập 5 nội dung nghiên cứu liên hoàn tương ứng với 5 giai đoạn phát triển và tương thích chặt chẽ với mạch dẫn dắt của 5 chương báo cáo:",
                        "1. Khảo sát cơ sở lý thuyết, phân tích kỹ thuật và vi cấu trúc thị trường chứng khoán Việt Nam: Nghiên cứu nền tảng lý thuyết thị trường chứng khoán, cơ chế khớp lệnh HOSE; bản chất dữ liệu nến Nhật OHLCV và các nhóm chỉ báo kỹ thuật; nguyên lý thuật toán LightGBM GBDT và mạng PyTorch LSTM; khảo sát quy định pháp lý VSDC chu kỳ T+2, thuế phí; cơ sở lý thuyết vòng đời học máy thực chiến Production Financial ML Lifecycle và kiến trúc Monorepo.",
                        "2. Khảo sát bài toán thực tế, phân tích yêu cầu hệ thống và kỹ nghệ dữ liệu đặc trưng: Khảo sát hành vi nhà đầu tư theo 4 khung giờ giao dịch HOSE với mốc 15:00 ATC; đặc tả nguồn dữ liệu SSI FC-Data API; xây dựng quy trình làm sạch 5 tiêu chuẩn và lưu trữ bảng Panel Parquet theo chuẩn CCDS v2; kỹ nghệ bộ 13 đặc trưng kỹ thuật tương đối không thứ nguyên; thiết kế nhãn 3 lớp có ngưỡng biến động +-1.0% và +-2.0%; phân tích yêu cầu chức năng (FR), phi chức năng (NFR), Use Case và thiết kế CSDL PostgreSQL 16.",
                        "3. Thiết kế và hiện thực hóa các mô hình học máy định lượng: Thiết lập khung Walk-Forward 3 cửa sổ mở rộng kết hợp Purged Boundary và Warm-up Tail trong khâu nghiên cứu; huấn luyện đối chứng 3 tầng mô hình (Naive Baseline, LightGBM, PyTorch LSTM); hiện thực hóa Pipeline Huấn luyện lại Thực chiến tự động học trên 100% dữ liệu lịch sử tích lũy với kỹ thuật Purged Horizon 3 phiên và Validation Buffer 40 phiên; lượng hóa độ bất định Softmax và bóc tách đặc trưng bằng SHAP.",
                        "4. Thiết kế động cơ kiểm thử chiến lược (Backtesting Engine) và phân hệ quản lý chiến thuật cá nhân: Cài đặt động cơ Backtesting sát vi cấu trúc T+2 qua PositionLot, khớp lệnh Open_{t+1}, khấu trừ thuế 0.10%, phí 0.15%, trượt giá 0.05%, lô chẵn 100 cổ phiếu; tính toán 25+ chỉ số tài chính định lượng chuẩn quốc tế; thực hiện kiểm định hoán vị ngẫu nhiên Monte Carlo 100 lần; thiết kế Phân hệ Quản lý Chiến thuật cá nhân chuẩn sàn DNSE EnTrade X (quản lý 2 trạng thái 'Triển khai' vs 'Chưa triển khai').",
                        "5. Đóng gói hệ thống phần mềm Full-stack Monorepo và kiểm thử đánh giá toàn diện: Xây dựng Backend RESTful API bằng FastAPI Async; xây dựng Frontend Web Dashboard bằng Next.js 16 App Router (TradingView Canvas 60fps); đóng gói Docker Compose; thiết kế và vận hành hệ thống kiểm thử tự động 170 unit & integration tests đạt tỷ lệ vượt qua 100%; đo kiểm độ trễ API và hiệu năng vận hành thực tế."
                    ]
                },
                {
                    "id": "1.4.2",
                    "title": "1.4.2. Phương pháp nghiên cứu áp dụng",
                    "paragraphs": [
                        "Đề tài áp dụng đồng bộ 5 phương pháp nghiên cứu khoa học chuẩn mực:",
                        "1. Phương pháp thu thập, tiền xử lý và quản trị dữ liệu chuỗi thời gian lớn: Thu thập dữ liệu API bản quyền từ SSI Fast Connect API; kiểm soát giới hạn tần suất; tiền kiểm định 5 tiêu chuẩn toàn vẹn dữ liệu tài chính; lưu trữ bảng Panel đa mã dạng dài phân vùng Apache Parquet theo chuẩn Cookiecutter Data Science v2 (CCDS v2).",
                        "2. Phương pháp phân tích kinh tế định lượng và tài chính hành vi: Chuyển đổi dữ liệu thị giá thành bộ 13 đặc trưng kỹ thuật tương đối không thứ nguyên nhằm triệt tiêu tính không dừng; mô hình hóa vi cấu trúc thị trường Việt Nam (chu kỳ T+2, thuế phí 0.40%, lô chẵn 100); đánh giá danh mục qua hệ thống 25+ chỉ số định lượng tài chính (ROI, CAGR, Sharpe, Sortino, Calmar, MDD, VaR 95%, Win Rate, Profit Factor).",
                        "3. Phương pháp mô hình hóa học máy và học sâu có giám sát: Ứng dụng kỹ thuật phân loại đa lớp có giám sát với phân bổ Softmax và dải tin cậy; kết hợp mô hình học máy dạng bảng LightGBM GBDT và mạng nơ-ron học sâu chuỗi thời gian PyTorch LSTM; áp dụng lý thuyết giá trị Shapley (SHAP Values) để bóc tách minh bạch đóng góp cận biên của từng chỉ báo tài chính.",
                        "4. Phương pháp thực nghiệm kiểm định chuỗi thời gian và mô phỏng ngẫu nhiên: Áp dụng khung Walk-Forward Expanding Windows (3 cửa sổ) kết hợp Purged Boundary và Warm-up Sequence Tail trong khâu nghiên cứu; áp dụng Purged Horizon trong khâu thực chiến; thực hiện mô phỏng hoán vị ngẫu nhiên Monte Carlo 100 lần để tính toán p-value thực nghiệm, chứng minh tính có ý nghĩa thống kê của chiến lược.",
                        "5. Phương pháp kỹ thuật phần mềm hiện đại và kiến trúc vận hành thực chiến: Ứng dụng kiến trúc Monorepo phân tầng; áp dụng chuẩn mực Clean Code và phương pháp phát triển hướng kiểm thử (TDD) theo chuẩn AAA (Arrange - Act - Assert) với 170 tests tự động đạt 100%; thiết kế kiến trúc phục vụ học máy tài chính thực chiến đảm bảo tính nhân quả thời gian thực mốc 15:00 ATC."
                    ]
                },
                {
                    "id": "1.4.3",
                    "title": "1.4.3. Bố cục của Đồ án Tốt nghiệp",
                    "paragraphs": [
                        "Báo cáo Đồ án Tốt nghiệp được tổ chức mạch lạc thành 5 chương chính, phần kết luận, tài liệu tham khảo và phụ lục:",
                        "* Chương 1: Tổng quan đề tài - Trình bày bối cảnh kinh tế - công nghệ, tính cấp thiết, tổng quan nghiên cứu trong/ngoài nước, tính mới, mục tiêu nghiên cứu, đối tượng, phạm vi nghiên cứu, nội dung và phương pháp nghiên cứu.",
                        "* Chương 2: Cơ sở lý thuyết và công nghệ liên quan - Hệ thống hóa nền tảng lý thuyết phân tích kỹ thuật, thuật toán LightGBM GBDT, mạng PyTorch LSTM, kỹ thuật chống rò rỉ dữ liệu Walk-Forward Purged Boundary, độ bất định Softmax và SHAP, lý thuyết Backtesting vi cấu trúc T+2, kiểm định Monte Carlo, vòng đời học máy thực chiến và stack công nghệ Monorepo.",
                        "* Chương 3: Khảo sát, phân tích yêu cầu và thiết kế dữ liệu - Khảo sát hành vi nhà đầu tư 4 khung giờ HOSE; đặc tả nguồn dữ liệu SSI FC-Data; quy trình làm sạch 5 tiêu chuẩn và lưu trữ Panel Parquet CCDS v2; công thức 13 đặc trưng tương đối; phân tích yêu cầu chức năng, phi chức năng, Use Case và thiết kế CSDL PostgreSQL 16.",
                        "* Chương 4: Thiết kế và hiện thực hóa hệ thống - Chi tiết hóa kiến trúc Monorepo phân tầng; thiết kế Ingestion và Market Session mốc 15:00 ATC; thiết kế Walk-Forward 3 cửa sổ Purged Boundary; thiết kế Pipeline Huấn luyện lại Thực chiến; thiết kế Động cơ Backtesting T+2; thiết kế Phân hệ Quản lý Chiến thuật cá nhân chuẩn DNSE EnTrade X; thiết kế Backend FastAPI, Frontend Next.js 16 và đóng gói Docker với 170 tests.",
                        "* Chương 5: Kết quả thực nghiệm và đánh giá hệ thống - Thiết lập thực nghiệm; kết quả so sánh đối chứng 3 mô hình Walk-Forward (Naive Baseline, LightGBM, LSTM); phân tích độ bất định Softmax và bóc tách đặc trưng SHAP; kết quả Backtest OOS trên 5 mã VN30 (phân tích sâu case VIC); kiểm định thống kê Monte Carlo (p = 0.0200 < 0.05); đo kiểm hiệu năng Vận hành Thực chiến trên 4.425 mẫu và đo kiểm độ trễ API live; demo sản phẩm và kết quả kiểm thử 170 tests.",
                        "* Phần kết luận, Tài liệu tham khảo và Phụ lục - Tổng kết các kết quả đạt được, chỉ rõ hạn chế tồn tại, đề xuất hướng phát triển mở rộng; danh mục 19 tài liệu tham khảo chuẩn IEEE; và phụ lục kỹ thuật."
                    ]
                }
            ]
        }
    ]
}
