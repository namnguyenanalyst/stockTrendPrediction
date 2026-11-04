"""
Chapter 3: KHẢO SÁT, PHÂN TÍCH YÊU CẦU VÀ THIẾT KẾ DỮ LIỆU
"""

CHAPTER_3_DATA = {
    "title": "CHƯƠNG 3: KHẢO SÁT, PHÂN TÍCH YÊU CẦU VÀ THIẾT KẾ DỮ LIỆU",
    "sections": [
        {
            "id": "3.1",
            "title": "3.1. KHẢO SÁT HIỆN TRẠNG, MÔ HÌNH BÀI TOÁN VÀ QUY TRÌNH TỔNG THỂ",
            "subsections": [
                {
                    "id": "3.1.1",
                    "title": "3.1.1. Khảo sát hành vi nhà đầu tư theo nhịp sinh học phiên giao dịch",
                    "paragraphs": [
                        "Để xây dựng một hệ thống hỗ trợ ra quyết định đầu tư có tính khả thi cao, việc khảo sát thực tế hành vi và tâm lý của nhà đầu tư cá nhân trên thị trường chứng khoán Việt Nam là bước đi tiên quyết. Qua khảo sát thực tế diễn biến tại sàn HOSE, hành vi ra quyết định của nhà đầu tư vận động tuần hoàn theo 4 khung giờ sinh học chính trong ngày:",
                        "1. Khung giờ trước mở cửa (08:30 – 09:00): Đây là khoảng thời gian nhà đầu tư tiếp nhận các luồng tin tức kinh tế vĩ mô, thông tin doanh nghiệp công bố đêm hôm trước và cập nhật diễn biến các chỉ số tài chính quốc tế (Dow Jones, S&P 500, Nikkei). Nhà đầu tư có nhu cầu rà soát lại danh mục hiện hữu, kiểm tra trạng thái các chiến thuật đang vận hành và xem xét các tín hiệu khuyến nghị định lượng để chuẩn bị lệnh giao dịch cho phiên sáng.",
                        "2. Khung giờ trong phiên giao dịch (09:00 – 14:30): Bao gồm phiên khớp lệnh định kỳ ATO (09:00 – 09:15) và hai phiên khớp lệnh liên tục (09:15 – 11:30 và 13:00 – 14:30). Trong giai đoạn này, bảng điện tử nhảy múa liên tục với hàng nghìn giao dịch mỗi giây; sự rung lắc mạnh của thị giá rất dễ kích hoạt các phản ứng cảm xúc tiêu cực như hưng phấn mua đuổi giá trần (FOMO) hoặc hoảng loạn bán tháo ở các nhịp điều chỉnh kỹ thuật. Trong khoảng thời gian này, cây nến ngày hôm nay chưa hoàn chỉnh (giá đóng cửa chưa xác lập); nếu hệ thống đưa ra các tín hiệu dự báo vội vã dựa trên mức giá dở dang nội phiên, nhà đầu tư rất dễ bị dẫn dắt vào các quyết định sai lầm.",
                        "3. Khung giờ phiên đóng cửa ATC và Chốt ngày (14:30 – 15:00): Phiên khớp lệnh định kỳ đóng cửa ATC (14:30 – 14:45) là thời điểm quan trọng nhất trong ngày, xác lập mức giá đóng cửa chính thức mang tính pháp lý của từng cổ phiếu. Sau 14:45 đến 15:00, các công ty chứng khoán và định chế cung cấp dữ liệu (như SSI) hoàn tất tổng hợp và đóng băng chuỗi nến ngày hoàn chỉnh.",
                        "4. Khung giờ sau phiên giao dịch (sau 15:00): Đây là 'thời điểm vàng' trong chu trình phân tích đầu tư. Khi thị trường đã đóng cửa và nến ngày đã chốt nguyên vẹn, tâm lý nhà đầu tư trở về trạng thái ổn định và duy lý. Đây là thời điểm thích hợp nhất để hệ thống kích hoạt luồng suy luận trực tuyến an toàn (Live Inference), chạy dự phóng quỹ đạo T+1 -> T+3, kích hoạt huấn luyện lại mô hình học máy (Continuous Retraining) và cho phép người dùng kiểm thử giả lập lại các chiến thuật định lượng trước khi bước vào ngày giao dịch tiếp theo."
                    ]
                },
                {
                    "id": "3.1.2",
                    "title": "3.1.2. Xác định bài toán cốt lõi hai pha",
                    "paragraphs": [
                        "Dựa trên khảo sát thực tế, đồ án xác định cấu trúc giải quyết bài toán theo hai pha liên hoàn chặt chẽ:",
                        "*Pha 1: Nghiên cứu Kiểm định Định lượng (Offline Research & Validation)*",
                        "- Tập trung vào tính chuẩn mực khoa học và kỷ luật học máy: Huấn luyện và so sánh đối chứng 3 tầng mô hình (Naive Heuristic Baseline, LightGBM GBDT và PyTorch Global LSTM) qua khung kiểm định Walk-Forward 3 cửa sổ mở rộng.",
                        "- Áp dụng kỹ thuật Purged Boundary và Warm-up Sequence Tail để loại bỏ hoàn toàn hiện tượng rò rỉ dữ liệu tương lai.",
                        "- Kiểm thử chiến lược ngoài mẫu (Out-of-Sample Backtesting) sát với vi cấu trúc thanh toán bù trừ T+2, trừ đủ thuế phí và kiểm định ý nghĩa thống kê bằng mô phỏng ngẫu nhiên Monte Carlo.",
                        "*Pha 2: Vận hành Thực chiến (Online Production Serving)*",
                        "- Tiếp nhận dữ liệu nến ngày mới nhất từ SSI Fast Connect API thông qua cơ chế nạp nối đuôi gia tăng (Incremental Sync).",
                        "- Quản lý trạng thái phiên thời gian thực qua module market_session.py căn cứ mốc chốt 15:00 ATC để bảo toàn tính nhân quả thời gian thực.",
                        "- Huấn luyện lại mô hình thực chiến (Production Retraining) trên 100% dữ liệu lịch sử tích lũy với kỹ thuật Purged Horizon 3 phiên và cô lập Validation Buffer 40 phiên.",
                        "- Cung cấp dịch vụ suy luận thời gian thực (/api/predict/live) xuất tín hiệu 3 lớp Softmax, dải tin cậy và Quỹ đạo dự phóng T+1 -> T+3; kết hợp Phân hệ Quản lý Chiến thuật cá nhân chuẩn DNSE EnTrade X cho phép quản lý chiến thuật ở 2 trạng thái 'Triển khai' (Active) và 'Chưa triển khai' (Draft)."
                    ]
                },
                {
                    "id": "3.1.3",
                    "title": "3.1.3. Quy trình áp dụng mô hình tổng thể (End-to-End Workflow)",
                    "paragraphs": [
                        "Quy trình áp dụng mô hình tổng thể của hệ thống là một vòng tuần hoàn khép kín gồm 6 công đoạn liên hoàn:",
                        "Công đoạn 1 (Thu nhận và Làm sạch dữ liệu): Kết nối SSI FC-Data API -> Thu thập nến OHLCV và VN-Index -> Kiểm định 5 tiêu chuẩn toàn vẹn -> Lưu trữ bảng Long-format Panel Parquet theo chuẩn CCDS v2.",
                        "Công đoạn 2 (Kỹ nghệ Đặc trưng & Quản lý Phiên): Tính toán bộ 13 đặc trưng kỹ thuật tương đối không thứ nguyên độc lập cho từng mã cổ phiếu -> Quản lý phiên giao dịch theo mốc 15:00 ATC qua market_session.py.",
                        "Công đoạn 3 (Phân chia Thời gian & Huấn luyện Đối chứng): Áp dụng Walk-Forward 3 cửa sổ mở rộng với Purged Boundary và Warm-up Tail -> Huấn luyện đối chứng Naive Baseline, LightGBM và PyTorch LSTM -> Đánh giá Macro F1-score.",
                        "Công đoạn 4 (Vận hành Thực chiến & Huấn luyện lại Liên tục): Kích hoạt train_production_model trên toàn bộ dữ liệu lịch sử tích lũy -> Cắt bỏ 3 phiên chưa diễn ra (Purged Horizon T+3) -> Cô lập 40 phiên Validation Buffer -> Khóa bộ chuẩn hóa production_scaler_t3.pkl -> Xuất artifacts sản xuất.",
                        "Công đoạn 5 (Kiểm thử Chiến lược Sát Vi cấu trúc): Động cơ Backtesting mô phỏng khớp lệnh tại giá Open_{t+1} kèm trượt giá 0.05% -> Quản lý chu kỳ T+2 qua PositionLot -> Trừ phí môi giới 0.15%, thuế 0.10%, lô chẵn 100 -> Tính toán 25+ chỉ số tài chính -> Kiểm định Monte Carlo 100 lần.",
                        "Công đoạn 6 (Phục vụ Người dùng qua Web Dashboard): Cung cấp REST API qua FastAPI Async -> Web Dashboard Next.js 16 trực quan hóa biểu đồ TradingView Canvas 60fps, nến FireAnt kết hợp Quỹ đạo T+3 và Phân hệ Quản lý Chiến thuật cá nhân DNSE EnTrade X."
                    ]
                },
                {
                    "id": "3.1.4",
                    "title": "3.1.4. Phân tích tác nhân, Tiến trình tự trị và Chuẩn mực đạo đức nghề nghiệp CFA",
                    "paragraphs": [
                        "Để hiện thực hóa một hệ thống phần mềm hỗ trợ ra quyết định đầu tư an toàn và tin cậy, việc mô hình hóa chính xác các đối tượng tương tác, phân định ranh giới giữa tác vụ của con người và dịch vụ nền tự trị của máy móc, đồng thời thiết lập các nguyên tắc đạo đức nghề nghiệp tài chính là cơ sở kiến trúc then chốt.",
                        "1. Hai tác nhân chuẩn hóa (System Actors):",
                        "- Nhà đầu tư cá nhân (Retail User): Là tác nhân trực tiếp khai thác các tín hiệu định lượng từ mô hình học máy đa kỳ hạn T+3 để hỗ trợ ra quyết định mua/bán cổ phiếu; thiết lập và vận hành phòng giả lập kiểm thử chiến lược giao dịch định lượng chuẩn sàn DNSE EnTrade X phù hợp với khẩu vị rủi ro cá nhân hóa (Bảo thủ - conservative, Cân bằng - balanced, Tăng trưởng mạo hiểm - aggressive); sở hữu và quản lý độc lập các bộ tham số đầu tư (Watchlists, Strategy Presets, Backtest Experiments). Toàn bộ dữ liệu của nhà đầu tư được cách ly nghiêm ngặt ở tầng ứng dụng (application-level tenant isolation) theo điều kiện ràng buộc khóa ngoại where(Model.user_id == current_user.id). Hệ thống không cam kết 'bảo mật tuyệt đối 100%' (vốn là tuyên bố phi thực tế trong an ninh thông tin) mà xây dựng cơ chế phòng thủ theo chiều sâu (Defense-in-Depth) với các chốt chặn kiểm thử xâm nhập.",
                        "- Quản trị viên Hệ thống (System Administrator): Là tác nhân vận hành kỹ thuật tuân thủ nghiêm ngặt Nguyên tắc Đặc quyền Tối thiểu (Principle of Least Privilege - PoLP). Quản trị viên chỉ có quyền quản trị định danh và phân quyền truy cập (IAM - khóa/mở tài khoản, phân bổ vai trò ADMIN hoặc TRADER) và giám sát 5 chỉ số thống kê tổng hợp về người dùng trên toàn hệ thống (tổng người dùng, người dùng mới đăng ký hôm nay/7 ngày/30 ngày theo mốc 0h00 UTC+7 và số người dùng đang hoạt động trực tuyến trong 5 phút). Quản trị viên tuyệt đối không có quyền truy cập, tra cứu hay can thiệp vào chiến lược đầu tư, danh mục theo dõi, tham số tùy biến hay kết quả backtest của người dùng khác (mọi truy vấn vào ID tài nguyên của người dùng khác đều bị chặn và trả về mã lỗi HTTP 404 Not Found).",
                        "2. Hệ thống Tiến trình Nền Tự trị (System Autonomous Background Services - DataOps/MLOps):",
                        "Khác với các ứng dụng truyền thống nơi người dùng phải bấm nút để tải dữ liệu hoặc huấn luyện mô hình, hệ thống chuyển giao toàn bộ các tác vụ hạ tầng sang các tiến trình nền tự trị:",
                        "- Dịch vụ tự động thu thập nến SSI Fast Connect API (DataOps): Vận hành theo cơ chế Lazy JIT Fetch kết hợp Khóa đơn luồng (Single-flight Lock). Khi hệ thống phát hiện phiên nến ATC chốt mới nhất chưa có trong kho dữ liệu Parquet cục bộ, chỉ duy nhất một luồng tiến trình được phép gọi API kết nối tới SSI để đồng bộ gia tăng, các luồng đồng thời khác sẽ xếp hàng chờ hoặc tái sử dụng dữ liệu sẵn có, triệt tiêu hoàn toàn nguy cơ dồn request làm cạn kiệt hạn mức giới hạn (Rate Limit) của SSI.",
                        "- Dịch vụ tự động huấn luyện lại định kỳ hàng tuần (MLOps Scheduled Retrain Worker): Vận hành tự động theo lịch định kỳ cuối tuần, gọi endpoint huấn luyện nội bộ được bảo vệ bởi mã bí mật X-Internal-Worker-Secret (ngăn chặn hoàn toàn nguy cơ tấn công từ chối dịch vụ DoS từ môi trường bên ngoài). Dịch vụ huấn luyện lại song song LightGBM GBDT và PyTorch Global LSTM trên 100% dữ liệu lịch sử tích lũy, áp dụng cơ chế cắt bỏ 3 phiên cuối (Purged Horizon T+3) và cô lập 40 phiên Validation Buffer, tự động xuất và thay thế nguyên tử (Atomic Replace) các bộ artifacts phục vụ suy luận trực tuyến.",
                        "3. Sáu Use Case chuẩn hóa của hệ thống:",
                        "- UC-01: Đăng ký, Đăng nhập và Quản lý Phiên xác thực JWT (Người dùng)",
                        "- UC-02: Tra cứu Diễn biến Thị trường và Biểu đồ Kỹ thuật Tương tác (Người dùng)",
                        "- UC-03: Khai thác Tín hiệu AI và Dự phóng Quỹ đạo Chu kỳ T+3 (Người dùng)",
                        "- UC-04: Thiết lập Phòng Giả lập Chiến lược DNSE EnTrade X và Đo lường Rủi ro (Người dùng)",
                        "- UC-05: Quản lý Danh mục Chiến thuật Cá nhân và Lưu vết Nhật ký Backtest (Người dùng)",
                        "- UC-06: Quản trị Định danh, Phân quyền Truy cập và Giám sát Thống kê Tổng hợp Người dùng (Admin)",
                        "4. Đối chiếu Chuẩn mực Đạo đức Nghề nghiệp CFA (CFA Institute Code of Ethics & Standards of Professional Conduct):",
                        "Trong lĩnh vực công nghệ tài chính (FinTech) và giao dịch định lượng, đạo đức nghề nghiệp đóng vai trò quyết định tính bền vững và sự minh bạch của hệ thống. Hệ thống được thiết kế đối chiếu trực tiếp với Bộ Quy tắc Đạo đức và Chuẩn mực Ứng xử Nghề nghiệp chính thức của Viện CFA Hoa Kỳ (CFA Institute):",
                        "- Standard III(A) Loyalty, Prudence and Care (Lòng trung thành, Cẩn trọng và Chu đáo): Chuẩn mực quy định chuyên gia tài chính phải hành động vì lợi ích tốt nhất của khách hàng và thực thi sự cẩn trọng tối đa. Hệ thống hiện thực hóa chuẩn mực này thông qua: (1) Triệt tiêu hoàn toàn rò rỉ dữ liệu tương lai (Lookahead Bias) và tuyệt đối không đưa ra khuyến nghị dựa trên nến dở dang giữa phiên, ngăn ngừa tổn thất do thông tin giả mạo; (2) Động cơ Backtesting mô phỏng trung thực vi cấu trúc thị trường Việt Nam (khấu trừ đầy đủ phí giao dịch 0.15%, thuế bán 0.10%, trượt giá 0.05% và độ trễ chu kỳ thanh toán VSDC T+2), không thổi phồng hiệu quả đầu tư; (3) Cung cấp phân bổ xác suất Softmax 3 lớp khách quan và mức độ tin cậy toán học, giúp nhà đầu tư kiểm soát kỳ vọng và quản trị rủi ro danh mục phù hợp với khẩu vị rủi ro cá nhân.",
                        "- Standard III(E) Preservation of Confidentiality (Bảo toàn tính Bảo mật Thông tin Khách hàng): Chuẩn mực quy định phải bảo vệ nghiêm ngặt thông tin hiện tại, quá khứ và tiềm năng của khách hàng. Hệ thống tuân thủ chuẩn mực này qua kiến trúc kỹ thuật: (1) Cách ly dữ liệu người dùng ở tầng ứng dụng (application-level tenant isolation) chặn đứng mọi rủi ro lộ lọt chiến lược bí mật giữa các tài khoản; (2) Áp dụng nguyên tắc đặc quyền tối thiểu (PoLP) tước bỏ hoàn toàn khả năng xem lén hay sao chép chiến thuật của tài khoản Quản trị viên (Admin chỉ được thấy các chỉ số thống kê ẩn danh); (3) Mật khẩu được mã hóa một chiều bằng giải thuật Bcrypt an toàn, phiên làm việc được bảo vệ bằng cơ chế Dual JWT thời hạn ngắn. Hệ thống không sử dụng các tuyên bố tiếp thị phóng đại như 'bảo mật tuyệt đối 100%' mà bảo đảm an ninh qua kiến trúc phòng thủ đa tầng và quy trình kiểm thử tự động nghiêm ngặt."
                    ]
                }
            ]
        },
        {
            "id": "3.2",
            "title": "3.2. THU THẬP DỮ LIỆU VÀ ĐẶC TẢ NGUỒN SSI FAST CONNECT API",
            "subsections": [
                {
                    "id": "3.2.1",
                    "title": "3.2.1. Khảo sát cấu trúc SSI Fast Connect API",
                    "paragraphs": [
                        "Để đảm bảo tính chính xác và tính pháp lý của dữ liệu đầu vào, đề tài không sử dụng các phương thức cào dữ liệu không chính thức (web scraping) dễ bị lỗi và thiếu ổn định. Toàn bộ chuỗi dữ liệu nến ngày được thu thập trực tiếp từ cổng giao diện lập trình ứng dụng chính thức SSI Fast Connect Data API (FC-Data: fc-data.ssi.com.vn) do Công ty Cổ phần Chứng khoán SSI phát hành.",
                        "Cơ chế xác thực và bảo mật:",
                        "- Hệ thống sử dụng cặp khóa định danh ConsumerID và ConsumerSecret được cấp phép chính thức từ SSI.",
                        "- Lớp SSIFastConnectClient trong module ssi_client.py thực hiện gửi yêu cầu xác thực tới endpoint /api/v2/Market/AccessToken để nhận mã thông báo truy cập JWT (JSON Web Token) có thời hạn hiệu lực 24 giờ. Hệ thống thiết lập bộ nhớ đệm cache token cục bộ với thời gian an toàn 6 giờ, tự động tái sử dụng token hợp lệ và tự động làm mới khi token hết hạn, giúp giảm thiểu tối đa các yêu cầu xác thực không cần thiết.",
                        "Các endpoint dữ liệu cốt lõi:",
                        "- Endpoint truy vấn nến ngày cổ phiếu (/api/v2/Market/DailyOhlc): Tiếp nhận các tham số mã cổ phiếu (Symbol), ngày bắt đầu (fromDate), ngày kết thúc (toDate), số trang (pageIndex) và kích thước trang (pageSize). Dữ liệu trả về bao gồm ngày giao dịch, giá mở cửa, cao nhất, thấp nhất, đóng cửa và khối lượng khớp lệnh.",
                        "- Endpoint truy vấn chỉ số thị trường (/api/v2/Market/DailyIndex): Tiếp nhận mã chỉ số (indexId='VNINDEX'), ngày bắt đầu và kết thúc; trả về điểm số mở cửa, đóng cửa và thanh khoản của toàn bộ rổ chỉ số VN-Index."
                    ]
                },
                {
                    "id": "3.2.2",
                    "title": "3.2.2. Xử lý giới hạn tần suất và Đồng bộ gia tăng (Incremental Sync)",
                    "paragraphs": [
                        "Trong quá trình tích hợp với hệ thống API của định chế tài chính, hai thách thức kỹ thuật lớn đã được giải quyết:",
                        "1. Xử lý giới hạn tần suất truy vấn (Rate Limits):",
                        "- Cổng SSI FC-Data áp đặt chính sách giới hạn số lượng yêu cầu trong một đơn vị thời gian để bảo vệ máy chủ. Nếu gửi truy vấn chuỗi lịch sử quá dài (ví dụ hơn 30 ngày trong một yêu cầu), API sẽ từ chối hoặc trả về dữ liệu rỗng.",
                        "- Giải pháp: Trong ssi_client.py, thuật toán tự động chia nhỏ khoảng thời gian truy vấn thành các phân đoạn nhỏ (chunks) có kích thước tối đa 25 ngày/chunk. Giữa mỗi lần gọi phân đoạn, hệ thống áp dụng cơ chế ngủ trễ cố định 1.2 giây (rate limit sleep).",
                        "- Cơ chế thử lại tự động (Exponential Retry): Khi gặp sự cố mạng hoặc phản hồi lỗi từ máy chủ, hệ thống tự động thử lại tối đa 3 lần với khoảng thời gian chờ tăng dần trước khi báo lỗi.",
                        "2. Cơ chế Đồng bộ Gia tăng (Incremental Sync):",
                        "- Thay vì mỗi ngày phải tải lại toàn bộ lịch sử 1.196 phiên từ năm 2022 (gây lãng phí băng thông và vi phạm giới hạn tần suất của SSI), hàm fetch_daily_ohlcv_incremental() trong data_ingestion.py tự động kiểm tra ngày chốt giao dịch cuối cùng có trong kho dữ liệu Parquet cục bộ (ví dụ: ngày t-1).",
                        "- Hệ thống chỉ gửi yêu cầu API để tải nối đuôi duy nhất các phiên giao dịch mới phát sinh từ ngày t-1 đến phiên hiện tại, sau đó ghép nối mượt mà vào bảng dữ liệu hiện có. Cơ chế này giúp thời gian đồng bộ dữ liệu chỉ mất khoảng 1.15 giây mỗi ngày."
                    ]
                },
                {
                    "id": "3.2.3",
                    "title": "3.2.3. Cơ chế ghi đĩa nguyên tử (Atomic Write)",
                    "paragraphs": [
                        "Trong môi trường vận hành thực tế, sự cố mất điện, mất kết nối mạng đột ngột hoặc tiến trình bị ngắt giữa chừng trong lúc ghi dữ liệu có thể dẫn đến việc tệp lưu trữ bị hỏng nửa chừng (Corrupted File), gây sụp đổ toàn bộ hệ thống.",
                        "Để triệt tiêu rủi ro này, hàm _atomic_save_parquet() trong data_ingestion.py được thiết kế theo nguyên lý ghi đĩa nguyên tử (Atomic File System Operations):",
                        "- Bước 1: Dữ liệu mới được ghi hoàn chỉnh vào một tệp tạm thời có phần mở rộng .tmp nằm trong cùng thư mục lưu trữ.",
                        "- Bước 2: Kiểm tra kích thước và tính hợp lệ của tệp tạm thời.",
                        "- Bước 3: Thực hiện thao tác đổi tên nguyên tử (Atomic Rename / Replace) từ tệp .tmp sang tệp đích chính thức .parquet.",
                        "Nhờ cơ chế này, ở cấp độ hệ điều hành, tệp dữ liệu chính thức luôn ở trạng thái toàn vẹn 100%, không bao giờ tồn tại trạng thái tệp bị ghi dở dang."
                    ]
                }
            ]
        },
        {
            "id": "3.3",
            "title": "3.3. QUY TRÌNH LÀM SẠCH, KIỂM ĐỊNH TOÀN VẸN VÀ PHÂN TẦNG DỮ LIỆU",
            "subsections": [
                {
                    "id": "3.3.1",
                    "title": "3.3.1. Tiền kiểm định 5 tiêu chuẩn toàn vẹn",
                    "paragraphs": [
                        "Dữ liệu thô tải về từ API trước khi được đưa vào kho lưu trữ phải vượt qua hàm tiền kiểm định nghiêm ngặt validate_downloaded_data() với 5 tiêu chuẩn dữ liệu tài chính bắt buộc:",
                        "1. Tính đơn điệu tăng dần của thời gian: Chuỗi ngày giao dịch (Date) phải được sắp xếp theo thứ tự thời gian tăng dần nghiêm ngặt (Date_{t} > Date_{t-1}).",
                        "2. Tính duy nhất không trùng lặp: Không được tồn tại hai bản ghi có cùng ngày giao dịch cho cùng một mã cổ phiếu.",
                        "3. Tính hợp lý của biên độ dao động giá: Mức giá cao nhất trong ngày phải luôn lớn hơn hoặc bằng mức giá thấp nhất (High >= Low); đồng thời High >= max(Open, Close) và Low <= min(Open, Close).",
                        "4. Tính dương của thị giá và thanh khoản: Toàn bộ các mức giá Open, High, Low, Close và khối lượng Volume phải nhận giá trị số học dương (Close > 0, Volume > 0).",
                        "5. Triệt tiêu giá trị rỗng: Không được chứa bất kỳ giá trị khuyết thiếu (NaN, Null hoặc Inf) nào trên toàn bộ các cột cốt lõi."
                    ]
                },
                {
                    "id": "3.3.2",
                    "title": "3.3.2. Phân tầng lưu trữ theo chuẩn Cookiecutter Data Science v2 (CCDS v2)",
                    "paragraphs": [
                        "Hệ thống tổ chức dữ liệu theo chuẩn mực khoa học dữ liệu quốc tế CCDS v2 tại thư mục apps/ml/data/ gồm 3 phân tầng lưu trữ rạch ròi:",
                        "- Tầng Raw (data/raw/): Lưu trữ dữ liệu thô nguyên bản nhận được từ SSI API dưới dạng tệp Parquet độc lập cho từng mã cổ phiếu ({Symbol}.parquet) và chỉ số thị trường (VNINDEX.parquet). Tầng này đóng vai trò là bản sao lưu dự phòng an toàn (Backup).",
                        "- Tầng Interim (data/interim/panel/): Lưu trữ bảng dữ liệu đã qua làm sạch, chuẩn hóa tên cột tiếng Anh, ghép nối chỉ số VN-Index và tổ chức dưới dạng bảng Panel đa mã phân vùng Parquet.",
                        "- Tầng Processed (data/processed/): Lưu trữ bảng đặc trưng kỹ thuật hoàn chỉnh gồm 13 chỉ báo tương đối đã được gán nhãn xu hướng, sẵn sàng nạp trực tiếp vào các mô hình học máy.",
                        "- Thư mục Model Artifacts (models/): Lưu trữ các tệp checkpoint trọng số mô hình (.txt, .pth), bộ tham số chuẩn hóa (.pkl) và nhật ký huấn luyện thực chiến (production_training_info_t3.json)."
                    ]
                },
                {
                    "id": "3.3.3",
                    "title": "3.3.3. Ghép bảng Panel đa mã dạng dài (Long-format Panel)",
                    "paragraphs": [
                        "Thay vì lưu trữ dữ liệu dàn trải theo chiều ngang (Wide format - mỗi mã cổ phiếu là một tập hợp các cột giá), đồ án thiết kế bảng dữ liệu dạng dài (Long-format Panel Data):",
                        "- Cấu trúc bảng gồm các cột định danh: Date (ngày giao dịch), Symbol (mã cổ phiếu, ví dụ VIC, HPG...), bộ giá nến (Open, High, Low, Close, Volume) và tỷ suất sinh lời của thị trường chung (VNINDEX_Return_1d).",
                        "- Tối ưu hóa lưu trữ phân vùng (Partitioned Parquet): Bảng dữ liệu được lưu trữ phân vùng theo mã cổ phiếu (partition_cols=['Symbol']) sử dụng định dạng Apache Parquet với chuẩn nén Snappy. Khi một dịch vụ chỉ cần truy vấn dữ liệu của mã FPT, hệ thống chỉ đọc đúng phân vùng thư mục Symbol=FPT mà không cần quét toàn bộ tệp, giúp tiết kiệm hơn 75% dung lượng RAM và tăng tốc độ đọc I/O lên gấp 5 đến 10 lần so với định dạng CSV truyền thống."
                    ]
                }
            ]
        },
        {
            "id": "3.4",
            "title": "3.4. KỸ NGHỆ 13 ĐẶC TRƯNG TƯƠNG ĐỐI KHÔNG THỨ NGUYÊN VÀ GÁN NHÃN CÓ NGƯỠNG",
            "subsections": [
                {
                    "id": "3.4.1",
                    "title": "3.4.1. Bộ 13 đặc trưng kỹ thuật tương đối không thứ nguyên",
                    "paragraphs": [
                        "Theo đúng mã nguồn hiện thực hóa tại module apps/ml/vn_stock/features.py (hàm compute_features_per_symbol), toàn bộ 13 đặc trưng kỹ thuật được thiết kế chuẩn xác dưới dạng các tỷ số tương đối không thứ nguyên (Dimensionless Ratios) nhằm triệt tiêu hoàn toàn tính không dừng của chuỗi giá nến:",
                        "Nhóm 1: Tỷ lệ vị trí và biên độ nến trong phiên (4 đặc trưng):",
                        "1. Open_Close_Ratio = (Open_t - Close_t) / Close_t: Đo lường mức độ biến động giữa giá mở cửa và giá đóng cửa; phản ánh xung lực giằng co giữa phe mua và phe bán trong phiên.",
                        "2. High_Close_Ratio = (High_t - Close_t) / Close_t: Đo lường độ dài của bóng nến trên so với giá đóng cửa; phản ánh áp lực bán chặn trên khi thị giá chạm vùng đỉnh nội phiên.",
                        "3. Low_Close_Ratio = (Low_t - Close_t) / Close_t: Đo lường độ dài bóng nến dưới so với giá đóng cửa; phản ánh lực cầu bắt đáy đỡ giá khi thị giá rơi xuống vùng đáy nội phiên.",
                        "4. HL_Ratio = (High_t - Low_t) / Close_t: Đo lường tổng biên độ dao động cực đại trong phiên; phản ánh mức độ biến động mạnh hay hẹp của ngày giao dịch.",
                        "Nhóm 2: Độ lệch chuẩn hóa so với các đường trung bình động xu hướng (3 đặc trưng):",
                        "5. SMA_20_Dev = (Close_t - SMA_20_t) / SMA_20_t: Đo lường độ lệch tương đối của thị giá so với xu hướng ngắn hạn 20 phiên (tương đương 1 tháng).",
                        "6. SMA_50_Dev = (Close_t - SMA_50_t) / SMA_50_t: Đo lường độ lệch tương đối so với xu hướng trung hạn 50 phiên (tương đương 1 quý).",
                        "7. SMA_200_Dev = (Close_t - SMA_200_t) / SMA_200_t: Đo lường độ lệch tương đối so với xu hướng dài hạn 200 phiên (tương đương 1 năm); giá nằm trên SMA_200 xác nhận chu kỳ tăng giá dài hạn.",
                        "Nhóm 3: Hệ số biến thiên và Thanh khoản tương đối (3 đặc trưng):",
                        "8. CV_50 = Std_50_t / SMA_50_t: Hệ số biến thiên chu kỳ trung hạn 50 phiên; đo lường mức độ rủi ro phân tán của thị giá so với giá trị trung bình.",
                        "9. CV_200 = Std_200_t / SMA_200_t: Hệ số biến thiên chu kỳ dài hạn 200 phiên; đo lường mức độ bất định của chu kỳ vĩ mô dài hạn.",
                        "10. Vol_Ratio = Volume_t / SMA_Vol_20_t: Tỷ số thanh khoản khối lượng; chuẩn hóa khối lượng phiên hiện tại so với khối lượng trung bình 20 phiên gần nhất, nhận diện các phiên bùng nổ dòng tiền lớn.",
                        "Nhóm 4: Động lượng và Xung lực thị trường chung (3 đặc trưng):",
                        "11. RSI = RSI_14(t): Chỉ số sức mạnh tương đối chu kỳ 14 phiên, dao động từ 0 đến 100, đo lường xung lực động lượng và nhận diện vùng quá mua/quá bán.",
                        "12. Return_1d = (Close_t - Close_{t-1}) / Close_{t-1}: Tỷ suất sinh lời của phiên gần nhất, phản ánh quán tính biến động tức thời của cổ phiếu.",
                        "13. VNINDEX_Return_1d = (VNINDEX_t - VNINDEX_{t-1}) / VNINDEX_{t-1}: Tỷ suất sinh lời của chỉ số VN-Index, phản ánh tâm lý và xu thế vận động của dòng tiền toàn thị trường.",
                        "Biến định danh bổ trợ: Symbol_Code được mã hóa số nguyên (từ 0 đến 29) cho 30 cổ phiếu rổ VN30, cung cấp thông tin định danh mã khi huấn luyện mô hình Global Panel đa mã."
                    ]
                },
                {
                    "id": "3.4.2",
                    "title": "3.4.2. Cơ chế gán nhãn 3 lớp có ngưỡng biến động",
                    "paragraphs": [
                        "Theo hàm create_labels_per_symbol() trong features.py và create_multi_day_labels() trong splitting_data.py, cơ chế gán nhãn 3 lớp có giám sát được thiết lập như sau:",
                        "Đối với Chân trời ngắn hạn 1 phiên (Horizon T+1):",
                        "Tỷ suất sinh lời phiên kế tiếp: Return_T1 = (Close_{t+1} - Close_t) / Close_t",
                        "Ngưỡng lọc nhiễu chuẩn: theta_1 = 1.0%",
                        "- Nhãn 2 (TĂNG): Return_T1 >= +1.0% -> Khuyến nghị MUA (BUY)",
                        "- Nhãn 0 (GIẢM): Return_T1 <= -1.0% -> Khuyến nghị BÁN (SELL)",
                        "- Nhãn 1 (ĐI NGANG): -1.0% < Return_T1 < +1.0% -> Khuyến nghị NẮM GIỮ (HOLD)",
                        "Đối với Chân trời nắm giữ thực chiến 3 phiên (Horizon T+3):",
                        "Tỷ suất sinh lời sau 3 phiên: Return_T3 = (Close_{t+3} - Close_t) / Close_t",
                        "Ngưỡng lọc nhiễu chuẩn: theta_3 = 2.0%",
                        "- Nhãn 2 (TĂNG): Return_T3 >= +2.0% -> Khuyến nghị MUA (BUY)",
                        "- Nhãn 0 (GIẢM): Return_T3 <= -2.0% -> Khuyến nghị BÁN (SELL)",
                        "- Nhãn 1 (ĐI NGANG): -2.0% < Return_T3 < +2.0% -> Khuyến nghị NẮM GIỮ (HOLD)",
                        "Ý nghĩa kinh tế của việc áp dụng ngưỡng lọc nhiễu:",
                        "Trong giao dịch thực tế, một biến động nhỏ dưới 1.0% thường chỉ là dao động ngẫu nhiên nội phiên. Hơn nữa, tổng chi phí một vòng quay giao dịch thực tế tại Việt Nam (phí mua 0.15% + phí bán 0.15% + thuế bán 0.10% = 0.40%). Nếu mở vị thế trên các biến động quá nhỏ, lợi nhuận sẽ bị bào mòn hoàn toàn bởi thuế phí. Ngưỡng lọc nhiễu +-1.0% và +-2.0% bảo đảm biên lợi nhuận kỳ vọng luôn vượt trội so với chi phí giao dịch, nâng cao tính khả thi thực chiến của mô hình."
                    ]
                },
                {
                    "id": "3.4.3",
                    "title": "3.4.3. Module quản lý phiên giao dịch thời gian thực (market_session.py)",
                    "paragraphs": [
                        "Module apps/ml/vn_stock/market_session.py đóng vai trò là chốt chặn bảo vệ tính toàn vẹn nhân quả thời gian thực của toàn bộ hệ thống:",
                        "- Khai báo múi giờ chuẩn Việt Nam: VN_TIMEZONE = 'Asia/Ho_Chi_Minh' (UTC+7).",
                        "- Khai báo mốc đóng cửa phiên an toàn: MARKET_CLOSE_TIME = 15:00:00 (kết thúc phiên ATC 14:45 + 15 phút tổng hợp dữ liệu).",
                        "- Hàm get_target_market_date():",
                        "  + Nếu thời điểm hiện tại trước 15:00 UTC+7 các ngày làm việc (Thứ 2 đến Thứ 6): Cây nến ngày hôm nay chưa hoàn chỉnh giá đóng cửa ATC; hàm tự động xác định phiên chốt dữ liệu căn cứ là ngày giao dịch liền trước (phiên T-1) để dự phóng an toàn cho chu kỳ T -> T+2.",
                        "  + Nếu thời điểm hiện tại sau 15:00 UTC+7: Nến ngày hôm nay đã đóng cửa chính thức; hàm xác định phiên chốt là phiên hôm nay (phiên T) để dự phóng chu kỳ T+1 -> T+3.",
                        "  + Vào các ngày cuối tuần (Thứ 7, Chủ Nhật) hoặc ngày nghỉ Lễ: Hàm tự động lùi về phiên Thứ 6 gần nhất có giao dịch chính thức.",
                        "Cơ chế này ngăn chặn tuyệt đối tình trạng máy chủ AI suy luận trên nến dở dang giữa phiên, triệt tiêu hoàn toàn sai số thời điểm quyết định ngoài đời thực."
                    ]
                }
            ]
        },
        {
            "id": "3.5",
            "title": "3.5. PHÂN TÍCH YÊU CẦU CHỨC NĂNG VÀ PHI CHỨC NĂNG HỆ THỐNG THỰC CHIẾN",
            "subsections": [
                {
                    "id": "3.5.1",
                    "title": "3.5.1. Yêu cầu chức năng thực chiến (Functional Requirements - FR)",
                    "paragraphs": [
                        "Hệ thống được thiết kế đáp ứng 8 yêu cầu chức năng cốt lõi phục vụ nhà đầu tư cá nhân và quản trị viên hệ thống:",
                        "- FR-01: Thu nhận và Đồng bộ dữ liệu nối đuôi gia tăng (Incremental Data Sync): Tự động kết nối SSI FC-Data API, kiểm tra phiên chốt cuối trong kho Parquet, chỉ tải các phiên mới và ghi đĩa nguyên tử bảo vệ tính toàn vẹn.",
                        "- FR-02: Kỹ nghệ đặc trưng và Quản lý phiên thời gian thực (Feature Engineering & Market Session): Tự động tính toán 13 chỉ báo tương đối không thứ nguyên; tự động nhận diện trạng thái thị trường theo mốc 15:00 ATC để khóa/mở nến ngày an toàn.",
                        "- FR-03: Suy luận AI trực tuyến và Dự phóng Quỹ đạo T+3 (Live AI Prediction & Multi-horizon Trajectory): Cung cấp dịch vụ suy luận thời gian thực (/api/predict/live) xuất phân bổ xác suất Softmax 3 lớp, mức độ tin cậy và trực quan hóa Quỹ đạo 3 phiên T+1 -> T+3 theo chu kỳ thanh toán VSDC.",
                        "- FR-04: Tiến trình Tự trị Huấn luyện lại Định kỳ Hàng tuần (DataOps/MLOps Scheduled Retrain Worker): Tự động kích hoạt định kỳ qua worker nền nội bộ bảo vệ bởi mã bí mật X-Internal-Worker-Secret (triệt tiêu nguy cơ DoS, không mở endpoint kích hoạt công khai), huấn luyện lại LightGBM và LSTM trên 100% dữ liệu lịch sử tích lũy, có cơ chế Purged Horizon 3 phiên và Validation Buffer 40 phiên, tự động cập nhật và xuất các bộ artifacts sản xuất.",
                        "- FR-05: Động cơ Backtesting sát vi cấu trúc và Kiểm định Monte Carlo: Mô phỏng khớp lệnh tại giá Open_{t+1} kèm trượt giá 0.05%, quản lý chu kỳ T+2 qua PositionLot, trừ phí 0.15%, thuế 0.10%, lô chẵn 100, tính 25+ chỉ số tài chính và chạy Monte Carlo 100 lần.",
                        "- FR-06: Phân hệ Quản lý Chiến thuật cá nhân chuẩn DNSE EnTrade X: Cung cấp 2 chế độ: Chế độ Quản lý Chiến thuật (bộ ba nút lọc 'Tất cả', 'Triển khai' - Active, 'Chưa triển khai' - Draft); Chế độ Phòng Lab Kiểm thử (tùy biến 12 điều kiện mua, 12 điều kiện bán, 8 presets mẫu và quản trị rủi ro tự động Stop Loss, Take Profit, Trailing Stop).",
                        "- FR-07: Giao diện Web Dashboard Trực quan Tương tác: Trực quan hóa biểu đồ nến Canvas TradingView Lightweight Charts 60fps, nến FireAnt, biểu đồ đường cong tài sản tích lũy (Equity Curve) và bảng phân tích deal.",
                        "- FR-08: Quản trị Định danh IAM và Giám sát Thống kê Tổng hợp Người dùng (System Admin IAM & Aggregated Stats): Cung cấp chức năng quản trị tài khoản, phân quyền vai trò (Role-Based Access Control) và giám sát 5 chỉ số thống kê tổng hợp (tổng người dùng, đăng ký mới hôm nay/7 ngày/30 ngày theo mốc 0h00 UTC+7 và số người dùng online trong 5 phút), tuân thủ nguyên tắc đặc quyền tối thiểu (PoLP) tuyệt đối không truy cập dữ liệu cá nhân hay chiến lược của người dùng khác."
                    ]
                },
                {
                    "id": "3.5.2",
                    "title": "3.5.2. Yêu cầu phi chức năng (Non-Functional Requirements - NFR)",
                    "paragraphs": [
                        "Các tiêu chuẩn chất lượng kỹ thuật mà hệ thống phải đáp ứng bao gồm:",
                        "- NFR-01: Hiệu năng và Độ trễ (Performance & Latency): Thời gian phản hồi API < 500ms cho các truy vấn dữ liệu thông thường; < 1.2s khi kích hoạt đồng bộ dữ liệu trực tuyến từ SSI; < 800ms cho tác vụ chạy backtest danh mục phức tạp.",
                        "- NFR-02: Tính toàn vẹn và Liêm chính học thuật (Zero Data Leakage): Triệt tiêu 100% rò rỉ dữ liệu tương lai (Lookahead Bias) và rò rỉ thời điểm quyết định (Decision-Time Leakage) trong cả khâu nghiên cứu lẫn vận hành thực chiến.",
                        "- NFR-03: Độ tin cậy và Độ bao phủ kiểm thử (Reliability & Test Coverage): Hệ thống phải được bảo chứng bằng bộ kiểm thử tự động toàn diện đạt 100% tỷ lệ vượt qua trên cả 3 tầng ML, API và Web.",
                        "- NFR-04: Trải nghiệm người dùng và Khả năng truy cập (UX & Accessibility): Giao diện Web Dashboard thiết kế theo phong cách Institutional Trading Terminal hiện đại, tông màu tối cao cấp (Dark Mode) giảm mỏi mắt, đạt tốc độ khung hình mượt mà 60fps trên biểu đồ nến Canvas."
                    ]
                }
            ]
        },
        {
            "id": "3.6",
            "title": "3.6. PHÂN TÍCH CA SỬ DỤNG (USE CASE ANALYSIS)",
            "subsections": [
                {
                    "id": "3.6.1",
                    "title": "3.6.1. Tác nhân hệ thống và Danh mục ca sử dụng chuẩn hóa",
                    "paragraphs": [
                        "Hệ thống xác định hai tác nhân người dùng và phân định rõ ranh giới với các tiến trình nền tự trị:",
                        "1. Nhà đầu tư cá nhân (Retail User): Người sử dụng giao diện Web Dashboard để theo dõi thị trường, xem khuyến nghị AI, tra cứu Quỹ đạo T+3, kiểm thử chiến lược và quản lý danh mục chiến thuật cá nhân theo 3 khẩu vị rủi ro (Bảo thủ - conservative, Cân bằng - balanced, Tăng trưởng mạo hiểm - aggressive). Toàn bộ dữ liệu của người dùng được cách ly nghiêm ngặt ở tầng ứng dụng (application-level tenant isolation) theo mệnh đề where(Model.user_id == current_user.id). Hệ thống xây dựng cơ chế phòng thủ theo chiều sâu (Defense-in-Depth) thay vì tuyên bố bảo mật tuyệt đối 100%.",
                        "2. Quản trị viên Hệ thống (System Administrator): Tuân thủ nguyên tắc đặc quyền tối thiểu (PoLP), chỉ thực hiện quản trị định danh và phân quyền (IAM - khóa/mở tài khoản, phân vai trò ADMIN hoặc TRADER) và theo dõi 5 chỉ số thống kê tổng hợp người dùng. Quản trị viên tuyệt đối không có quyền truy cập, tra cứu hay can thiệp vào chiến lược đầu tư, watchlist, preset hay kết quả backtest của người dùng khác (mọi truy vấn vào ID tài nguyên người khác đều bị chặn và trả về HTTP 404).",
                        "3. Hệ thống Tiến trình Nền Tự trị (System Autonomous Background Services - DataOps/MLOps): Dịch vụ tự động nạp nến SSI (Lazy JIT Fetch với Single-flight Lock) và Worker huấn luyện lại định kỳ hàng tuần với mã xác thực nội bộ X-Internal-Worker-Secret. Đây là các dịch vụ nền tự trị của hạ tầng, không phải là Use Case tương tác của con người.",
                        "Danh mục 6 ca sử dụng chuẩn hóa (Standard Use Cases):",
                        "- UC-01: Đăng ký, Đăng nhập và Quản lý Phiên xác thực JWT (Người dùng)",
                        "- UC-02: Tra cứu Diễn biến Thị trường và Biểu đồ Kỹ thuật Tương tác (Người dùng)",
                        "- UC-03: Khai thác Tín hiệu AI và Dự phóng Quỹ đạo Chu kỳ T+3 (Người dùng)",
                        "- UC-04: Thiết lập Phòng Giả lập Chiến lược DNSE EnTrade X và Đo lường Rủi ro (Người dùng)",
                        "- UC-05: Quản lý Danh mục Chiến thuật Cá nhân và Lưu vết Nhật ký Backtest (Người dùng)",
                        "- UC-06: Quản trị Định danh, Phân quyền Truy cập và Giám sát Thống kê Tổng hợp Người dùng (Admin)"
                    ]
                },
                {
                    "id": "3.6.2",
                    "title": "3.6.2. Đặc tả các ca sử dụng cốt lõi",
                    "paragraphs": [
                        "Đặc tả Use Case UC-01: Đăng ký, Đăng nhập và Quản lý Phiên xác thực JWT",
                        "- Tác nhân: Người dùng (Nhà đầu tư cá nhân hoặc Quản trị viên).",
                        "- Tiền điều kiện: Hệ thống Backend API đang hoạt động; cơ sở dữ liệu PostgreSQL 16 sẵn sàng kết nối.",
                        "- Luồng sự kiện chính:",
                        "  1. Người dùng mở giao diện Đăng ký hoặc Đăng nhập trên Web Dashboard.",
                        "  2. Người dùng nhập email, mật khẩu và chọn khẩu vị rủi ro ('conservative', 'balanced', 'aggressive').",
                        "  3. Backend xác thực thông tin, băm mật khẩu bằng giải thuật Bcrypt an toàn, khởi tạo tài khoản và sinh cặp mã thông báo Dual JWT (Access Token 30 phút và Refresh Token 7 ngày).",
                        "  4. Frontend lưu trữ Access Token trong bộ nhớ phiên và cập nhật ngữ cảnh người dùng (AuthContext). Mỗi yêu cầu tiếp theo tự động cập nhật mốc hoạt động gần nhất (last_seen_at) phục vụ thống kê trực tuyến.",
                        "- Hậu điều kiện: Người dùng đăng nhập thành công và truy cập vào các phân hệ chức năng tương ứng với vai trò được cấp phép.",
                        "Đặc tả Use Case UC-03: Khai thác Tín hiệu AI và Dự phóng Quỹ đạo Chu kỳ T+3",
                        "- Tác nhân: Nhà đầu tư cá nhân.",
                        "- Tiền điều kiện: Hệ thống Backend API đã nạp sẵn mô hình và scaler; người dùng đã chọn một mã cổ phiếu (ví dụ: VIC, HPG).",
                        "- Luồng sự kiện chính:",
                        "  1. Người dùng chọn tab 'Tín hiệu AI' trên Web Dashboard.",
                        "  2. Giao diện gửi yêu cầu GET tới /api/predict/live?symbol=VIC&model_type=lightgbm (hoặc lstm).",
                        "  3. Backend kiểm tra phiên thị trường qua market_session.py; nạp đặc trưng phiên chốt ATC gần nhất; gọi mô hình LightGBM hoặc LSTM tính phân bổ xác suất Softmax 3 lớp, mức độ tin cậy và xây dựng Quỹ đạo 3 phiên T+1 -> T+3 theo chu kỳ thanh toán VSDC.",
                        "  4. Giao diện hiển thị huy hiệu trạng thái tự trị ('Mô hình AI tự động cập nhật định kỳ hàng tuần | Căn cứ phiên chốt ATC'), thẻ khuyến nghị màu (Xanh/Đỏ/Vàng), thanh radar xác suất Softmax và biểu đồ nến FireAnt kết hợp Quỹ đạo dự phóng.",
                        "- Hậu điều kiện: Nhà đầu tư nắm bắt được tín hiệu định lượng khách quan và lộ trình cổ phiếu về tài khoản an toàn.",
                        "Đặc tả Use Case UC-04: Thiết lập Phòng Giả lập Chiến lược DNSE EnTrade X và Đo lường Rủi ro",
                        "- Tác nhân: Nhà đầu tư cá nhân.",
                        "- Tiền điều kiện: Dữ liệu nến lịch sử đã được làm sạch và lưu trữ đầy đủ trong kho Parquet.",
                        "- Luồng sự kiện chính:",
                        "  1. Người dùng mở tab 'Giả lập Chiến lược' và chọn cấu hình điều kiện mua/bán từ 12 chỉ báo kỹ thuật hoặc chọn một trong 8 chiến lược mẫu (Trend Following, RSI Reversal, Bollinger Breakout, v.v.).",
                        "  2. Người dùng thiết lập các quy tắc quản trị rủi ro danh mục (Cắt lỗ - Stop Loss, Chốt lời - Take Profit, Chặn lỗ kéo theo - Trailing Stop) phù hợp với khẩu vị rủi ro đã đăng ký.",
                        "  3. Người dùng nhấn nút 'Chạy kiểm thử', Backend kích hoạt động cơ Backtesting mô phỏng khớp lệnh tại giá Open_{t+1} kèm trượt giá 0.05%, tuân thủ chu kỳ T+2, khấu trừ phí 0.15% và thuế 0.10%.",
                        "  4. Hệ thống trả về báo cáo định lượng với 25+ chỉ số tài chính (ROI, Sharpe, Sortino, Max Drawdown, Win Rate), đường cong tài sản trực quan và kết quả kiểm định Monte Carlo 100 lần.",
                        "- Hậu điều kiện: Nhà đầu tư kiểm chứng được tính khả thi và mức độ rủi ro của chiến lược trước khi quyết định đầu tư vốn thực tế.",
                        "Đặc tả Use Case UC-05: Quản lý Danh mục Chiến thuật Cá nhân và Lưu vết Nhật ký Backtest",
                        "- Tác nhân: Nhà đầu tư cá nhân.",
                        "- Tiền điều kiện: Người dùng đã thực hiện ít nhất một lần kiểm thử chiến lược thành công.",
                        "- Luồng sự kiện chính:",
                        "  1. Người dùng nhấn 'Lưu chiến lược', nhập tên chiến thuật và chọn trạng thái ('Triển khai' - Active hoặc 'Chưa triển khai' - Draft).",
                        "  2. Backend lưu thông tin chiến lược vào CSDL PostgreSQL 16 gắn liền với current_user.id. Mọi truy vấn đọc/sửa/xóa đều được ràng buộc bảo đảm cách ly dữ liệu tầng ứng dụng tuyệt đối.",
                        "  3. Người dùng có thể lọc danh sách theo trạng thái Active/Draft, bật/tắt công tắc gạt trạng thái, hoặc nhấn 'Chạy lại' để tái kiểm định trên dữ liệu nến mới nhất.",
                        "- Hậu điều kiện: Chiến lược và lịch sử backtest được lưu trữ bền vững, bảo mật và chỉ có tác giả mới có thể truy cập.",
                        "Đặc tả Use Case UC-06: Quản trị Định danh, Phân quyền Truy cập và Giám sát Thống kê Tổng hợp Người dùng",
                        "- Tác nhân: Quản trị viên Hệ thống (System Administrator).",
                        "- Tiền điều kiện: Quản trị viên đã đăng nhập với tài khoản có vai trò 'admin'.",
                        "- Luồng sự kiện chính:",
                        "  1. Quản trị viên truy cập trang 'Thống kê hệ thống' (/admin/stats).",
                        "  2. Giao diện gửi yêu cầu GET tới /api/v1/admin/stats kèm Access Token của Admin.",
                        "  3. Backend kiểm tra quyền (Role ADMIN), thực thi các truy vấn tổng hợp trên CSDL và trả về duy nhất 5 chỉ số tổng hợp: tổng người dùng, số đăng ký mới (hôm nay, 7 ngày, 30 ngày tính theo 0h00 UTC+7) và số người dùng đang online (hoạt động trong 5 phút gần nhất).",
                        "  4. Giao diện hiển thị 4 thẻ chỉ số tổng quan sạch sẽ. Tuyệt đối không hiển thị danh sách hoạt động chi tiết, không hiển thị thông tin cá nhân (email, tên), và không cho phép Admin truy cập hay thao túng chiến lược của bất kỳ người dùng nào (tuân thủ PoLP).",
                        "- Hậu điều kiện: Quản trị viên nắm bắt được tình trạng tăng trưởng và quy mô tải của hệ thống mà không vi phạm tính bảo mật và riêng tư của người dùng."
                    ]
                }
            ]
        },
        {
            "id": "3.7",
            "title": "3.7. THIẾT KẾ CƠ SỞ DỮ LIỆU VÀ LƯỢC ĐỒ LƯU TRỮ",
            "subsections": [
                {
                    "id": "3.7.1",
                    "title": "3.7.1. Lược đồ CSDL quan hệ PostgreSQL 16",
                    "paragraphs": [
                        "Để lưu trữ dữ liệu có cấu trúc phục vụ quản lý danh mục và lịch sử thực nghiệm, hệ thống thiết kế cơ sở dữ liệu quan hệ PostgreSQL 16 với 5 bảng cốt lõi:",
                        "1. Bảng stocks: Lưu trữ danh mục mã cổ phiếu, gồm các trường: symbol (VARCHAR(10), Primary Key), company_name (VARCHAR(255)), sector (VARCHAR(100)), exchange (VARCHAR(10), mặc định 'HOSE'), is_vn30 (BOOLEAN).",
                        "2. Bảng daily_ohlcv: Lưu trữ dữ liệu nến ngày lịch sử, gồm: id (BIGSERIAL, Primary Key), symbol (VARCHAR(10), Foreign Key tới stocks), trade_date (DATE), open_price (NUMERIC(12,2)), high_price (NUMERIC(12,2)), low_price (NUMERIC(12,2)), close_price (NUMERIC(12,2)), volume (BIGINT). Tạo chỉ mục kép (Index): CREATE UNIQUE INDEX idx_stock_date ON daily_ohlcv(symbol, trade_date).",
                        "3. Bảng technical_features: Lưu trữ 13 đặc trưng kỹ thuật tương đối đã tính toán: id (BIGSERIAL, Primary Key), symbol (VARCHAR(10)), trade_date (DATE), open_close_ratio, high_close_ratio, low_close_ratio, hl_ratio, sma_20_dev, sma_50_dev, sma_200_dev, cv_50, cv_200, vol_ratio, rsi_14, return_1d, vnindex_return_1d (đều có kiểu NUMERIC(10,6)).",
                        "4. Bảng model_predictions: Lưu vết các dự báo AI theo từng phiên: id (BIGSERIAL), symbol (VARCHAR(10)), trade_date (DATE), model_name (VARCHAR(50)), horizon (INT), prob_down (NUMERIC(6,4)), prob_hold (NUMERIC(6,4)), prob_up (NUMERIC(6,4)), confidence (NUMERIC(6,4)), recommendation (VARCHAR(20)).",
                        "5. Bảng backtest_experiments: Lưu vết kết quả các lần chạy kiểm thử chiến lược: id (UUID, Primary Key), strategy_name (VARCHAR(100)), symbols (TEXT[]), start_date (DATE), end_date (DATE), initial_capital (NUMERIC(15,2)), ending_equity (NUMERIC(15,2)), roi_pct (NUMERIC(8,4)), sharpe_ratio (NUMERIC(8,4)), sortino_ratio (NUMERIC(8,4)), max_drawdown_pct (NUMERIC(8,4)), win_rate_pct (NUMERIC(8,4)), profit_factor (NUMERIC(8,4)), p_value_monte_carlo (NUMERIC(6,4)), status (VARCHAR(20) - 'Active' hoặc 'Draft')."
                    ]
                },
                {
                    "id": "3.7.2",
                    "title": "3.7.2. Lược đồ lưu trữ tệp Apache Parquet phân vùng và Nhật ký Huấn luyện thực chiến",
                    "paragraphs": [
                        "Bên cạnh CSDL quan hệ PostgreSQL, hệ thống ứng dụng kiến trúc lưu trữ lai (Hybrid Storage Architecture):",
                        "- Apache Parquet phân vùng (apps/ml/data/interim/panel/): Toàn bộ chuỗi dữ liệu bảng dạng dài (Long-format Panel) được lưu trữ dưới định dạng Apache Parquet dạng cột với chuẩn nén Snappy. Thư mục được phân vùng tự động theo cột mã cổ phiếu: Symbol=VIC/data.parquet, Symbol=HPG/data.parquet... Cấu trúc này tối ưu hóa tuyệt đối cho các tác vụ nạp dữ liệu ma trận vào PyTorch Tensor và LightGBM Dataset.",
                        "- Cấu trúc tệp nhật ký huấn luyện thực chiến (production_training_info_t3.json): Được tự động sinh ra sau mỗi lần chạy pipeline train_production_model(), ghi nhận đầy đủ siêu dữ liệu (Metadata):",
                        "  + target_market_date: Ngày chốt phiên thị trường thực tế (ví dụ: 2026-10-23).",
                        "  + total_samples: Tổng số mẫu học tích lũy (4.425 mẫu).",
                        "  + train_samples (4.225 mẫu) và val_samples (200 mẫu Validation Buffer).",
                        "  + horizon: Chân trời dự báo (T+3) và threshold: Ngưỡng lọc nhiễu (0.02).",
                        "  + metrics: Chi tiết Accuracy, Macro F1, Weighted F1 và ma trận nhầm lẫn Confusion Matrix của cả hai mô hình LightGBM và LSTM.",
                        "- Cấu trúc lưu trữ chiến thuật cá nhân (SavedStrategyItem): Được cấu trúc theo chuẩn TypeScript Interface, lưu trữ đồng bộ trên LocalStorage trình duyệt và CSDL Backend, bao gồm các trường: id, name, scope, buyConditions (12 điều kiện), sellConditions (12 điều kiện), stopLossPct, takeProfitPct, trailingStopPct, maxHoldingDays, status ('active' | 'draft'), lastBacktestMetrics (ROI, Sharpe, MDD), createdAt và updatedAt."
                    ]
                }
            ]
        }
    ]
}
