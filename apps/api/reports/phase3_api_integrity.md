# Phase 3 — API, phân quyền, lưu trữ và xử lý lỗi

Ngày thực hiện: 14/11/2026. Đây là đợt 3 trong kế hoạch sáu đợt hoàn thiện dự án, không phải pha huấn luyện mô hình trong khung phương pháp luận năm pha của đồ án.

## Kết quả

Đã sửa các lỗi xác thực tái hiện được bằng test, bổ sung phiên refresh lưu trong CSDL, cập nhật chiến lược/danh mục theo chủ sở hữu, chặn dữ liệu đầu vào không hợp lệ, sửa cách xử lý tác vụ đồng bộ và lỗi API. Migration 003_refresh_sessions đã được áp dụng thành công trên PostgreSQL cục bộ đang cấu hình của dự án, từ revision 002_add_last_seen_at_to_users.

Đã kiểm tra qua router ASGI thật và PostgreSQL thật: đăng ký/đăng nhập, lưu và cập nhật preset, chặn người dùng khác sửa preset, dùng đồng thời một refresh token chỉ thành công một lần, logout thu hồi phiên. Hai tài khoản thử và toàn bộ phiên thử đã được xóa; kết quả đối soát ở phase3_postgres_acceptance.json. Đây là kiểm tra tích hợp API–CSDL, chưa phải nghiệm thu qua trình duyệt hoặc Docker.

Không thay model production, scaler, dữ liệu giá gốc, số liệu thực nghiệm Phase 2 hoặc tệp Word. Các thay đổi của hai đợt trước được giữ nguyên; có checkpoint trước đợt này tại /tmp/stocktrend-phase3-checkpoint.

## 1. Xác thực và phiên đăng nhập

### Vấn đề đã tái hiện

- JWT có chữ ký hợp lệ nhưng thiếu exp, iat hoặc type vẫn có thể được chấp nhận. Thiếu exp có thể làm mất giới hạn thời gian của token.
- Hàm băm và kiểm tra mật khẩu cắt UTF-8 còn 72 byte; hai mật khẩu khác đuôi có thể được coi là một mật khẩu.
- Refresh token cũ được dùng lại nhiều lần, không có bản ghi phiên để thu hồi.
- Logout trên web chỉ xóa access token trong bộ nhớ; cookie refresh HttpOnly ở backend vẫn tồn tại.
- Secret nội bộ chỉ gồm dấu cách có thể vượt kiểm tra sau khi trim; chuỗi không ASCII có thể gây lỗi TypeError khi so sánh.

### Thay đổi

- decode_token yêu cầu đủ sub, type, iat và exp. Access endpoint chỉ nhận type access; refresh endpoint chỉ nhận type refresh. Extra claims không được ghi đè các trường bảo mật do hàm tạo token thiết lập.
- Mật khẩu mới dùng định dạng có phiên bản bcrypt-sha256-v1$: SHA-256 của toàn bộ UTF-8, mã hóa base64 rồi băm bcrypt với salt. Dữ liệu lưu không phải SHA-256 thuần. Cách xử lý mật khẩu dài tham khảo hướng dẫn của pyca/bcrypt; định dạng có tiền tố này là định dạng riêng của dự án, không tuyên bố tương thích định dạng Passlib.
- Hash bcrypt cũ vẫn được kiểm tra với mật khẩu tối đa 72 byte và được nâng cấp sau khi đăng nhập thành công. Không chấp nhận mật khẩu dài hơn 72 byte với hash cũ vì không thể xác minh phần đuôi từng bị cắt. Tài khoản cũ thuộc trường hợp đó cần quy trình đặt lại mật khẩu; đợt này chưa bổ sung màn hình/quy trình khôi phục mật khẩu.
- Password tại biên API giới hạn 1.024 ký tự; email/họ tên giới hạn theo cột CSDL. Lỗi 422 không trả lại mật khẩu trong trường input của response.
- Bảng refresh_sessions chỉ lưu SHA-256 của refresh token, user_id và expires_at, không lưu bearer token nguyên văn. Token refresh mới có jti ngẫu nhiên để tránh trùng khi đăng nhập trong cùng một giây.
- Mỗi lần refresh xóa có điều kiện bản ghi token cũ và thêm token mới trong cùng transaction. Hai session CSDL tranh dùng cùng token chỉ có một lần DELETE thành công. Thời hạn tuyệt đối của phiên giữ nguyên khi xoay token, không tự gia hạn thêm bảy ngày mỗi lần.
- POST /api/v1/auth/logout thu hồi refresh token hiện tại và xóa cookie đúng path /api/v1/auth. Cookie có HttpOnly, SameSite=Lax; bật Secure khi ENVIRONMENT=production.
- Refresh/logout dùng cookie từ chối Origin nằm ngoài CORS_ORIGINS. Luồng gửi refresh token trực tiếp trong body vẫn được hỗ trợ; client phải giữ credential đó an toàn.
- Settings từ chối khóa JWT mặc định hoặc khóa ngắn hơn 32 byte ở production. Không tự thay khóa trong .env của người dùng.
- Secret worker phải khác rỗng sau trim và được so sánh dưới dạng byte bằng compare_digest. Không thực hiện retrain trong đợt này.

### Giới hạn cần hiểu đúng

Logout thu hồi phiên refresh hiện tại; access token đã phát hành vẫn có hiệu lực đến exp, mặc định 30 phút. Đây chưa phải cơ chế thu hồi mọi access token ngay lập tức hoặc logout mọi thiết bị. Việc phát hiện refresh token cũ dùng lại chưa thực hiện thu hồi toàn bộ họ token theo mô hình chống replay đầy đủ của OAuth. Không tuyên bố hệ thống đạt chứng nhận bảo mật hoặc tuân thủ đầy đủ OAuth BCP.

Refresh token được phát hành trước migration không có trong bảng phiên mới; người dùng sẽ cần đăng nhập lại khi làm mới phiên. Không lưu token hoặc mật khẩu thử vào báo cáo.

## 2. Lưu trữ và phân quyền dữ liệu cá nhân

- Bổ sung PUT /api/v1/user/watchlists/{watchlist_id} và PUT /api/v1/user/presets/{preset_id}. Payload dùng schema tạo mới tương ứng; PUT thay thế cấu hình, không phải partial PATCH.
- Truy vấn cập nhật luôn ràng buộc đồng thời id và user_id từ token đã xác thực. Người khác, kể cả admin, không được sửa dữ liệu cá nhân qua hai endpoint này; nhận 404 như trường hợp không tồn tại. Không lấy user_id từ body để đổi chủ sở hữu.
- Danh sách watchlist, preset và backtest history có limit mặc định 100, tối đa 500 và offset không âm; vẫn trả mảng như hợp đồng trước. Client có trên 100 bản ghi cần phân trang.
- Giới hạn tên watchlist/preset theo cột String(100), mã theo 20 ký tự, số mã trong watchlist 100, mô tả preset 4.000 ký tự, equity curve 5.000 điểm và mỗi payload JSON lồng nhau tối đa 512.000 byte.
- Cấu hình JSON và equity curve từ chối NaN/Infinity trước khi ghi CSDL. Backtest history kiểm tra ngày kết thúc không trước ngày bắt đầu, vốn dương và hữu hạn, tỷ lệ thắng trong 0–100.
- max_drawdown lịch sử chấp nhận dấu âm của client cũ trong khoảng -100 đến 100; không tự đổi đơn vị hay sửa bản ghi cũ. Engine mới vẫn trả mức giảm theo quy ước của engine. Không suy đoán 0,65 có nghĩa là 65% để tự đổi dữ liệu người dùng.
- Các thao tác tạo/cập nhật sử dụng commit_or_conflict để rollback khi lỗi ràng buộc, trả 409 với thông báo ổn định thay vì lộ SQL hoặc để session ở trạng thái lỗi. Kiểm tra email đã tồn tại trước khi insert vẫn giữ response 400 như hợp đồng cũ; race tại commit trả 409.
- Xóa phần chuyển đổi ngày dự phòng không còn được dùng trong save_backtest: Pydantic đã kiểm tra và chuyển hai trường đó thành date.

Nhật ký backtest lưu qua API cá nhân hóa vẫn là dữ liệu do client gửi lên; không mặc nhiên là kết quả được backend chứng nhận. Trạng thái Active/Draft có thể lưu trong parameters và cập nhật bền vững, nhưng đợt này chưa đồng bộ toàn bộ strategyStorage của giao diện sang CSDL; phần đó thuộc Phase 4.

## 3. API đồng bộ, dữ liệu và xử lý lỗi

- Các route stocks, prediction và backtest gọi thư viện đồng bộ được khai báo def để FastAPI chạy ở thread pool; các route dùng AsyncSession tiếp tục là async def. Hash/verify bcrypt và đồng bộ lúc khởi động cũng được đẩy khỏi event loop. Đây là sửa cách thực thi, chưa phải benchmark hiệu năng hay worker queue cho tác vụ dài.
- POST /api/stocks/sync yêu cầu tài khoản đang hoạt động. Dự báo công khai vẫn được giữ công khai; endpoint retrain vẫn yêu cầu secret nội bộ.
- Mã chứng khoán được trim, uppercase và kiểm tra chữ/số tối đa 20 ký tự trước khi trở thành đường dẫn cache hoặc yêu cầu tải dữ liệu. Từ chối đường dẫn ../, dấu phân cách thư mục, mã rỗng và mã quá dài bằng 400. Mã sai cú pháp được phân biệt với mã đúng cú pháp nhưng không tìm thấy dữ liệu.
- Batch prediction kiểm tra loại model/phạm vi trước khi lặp, giới hạn danh sách tối đa 100 mã và loại mã trùng. Model không hợp lệ không còn bị nuốt lỗi rồi trả 200 với batch rỗng. Các lỗi riêng lẻ trong batch hợp lệ vẫn được ghi log và bỏ qua theo hợp đồng hiện tại; chưa có bảng lỗi từng mã trong response.
- RetrainRequest kiểm tra horizon, threshold, validation buffer và phạm vi CORE/VN30 trước khi gọi huấn luyện.
- Live prediction kiểm tra cả ngày mới nhất của dữ liệu tải/cache và data_as_of_date của kết quả so với phiên chốt mục tiêu. Khi tải thất bại, cache còn cũ hoặc suy luận chưa tới phiên mục tiêu, API trả 503 thay vì gán is_live_synced=True. Cờ này xác nhận dữ liệu tới phiên chốt, không có nghĩa giá tick tức thời hoặc bắt buộc vừa tải qua mạng.
- Endpoint status đọc metadata từ bundle manifest khi manifest tồn tại; bundle hỏng trả 503, không lấy metadata loose cũ để che lỗi. Vẫn hỗ trợ artifact legacy khi chưa có manifest.
- Public response 5xx không kèm traceback, đường dẫn model hoặc nội dung exception. Lỗi SQLAlchemy trả thông báo 503 an toàn. Lỗi 422 chỉ giữ type, loc, msg, bỏ input và ctx; lỗi 4xx vẫn có thông tin để client sửa yêu cầu. Chi tiết kỹ thuật được ghi log phía server.

Thread pool có giới hạn và retrain vẫn là HTTP request đồng bộ dài; chưa có hàng đợi phân tán/rate limit triển khai nhiều instance. Các giới hạn này cần được đo và xử lý ở đợt Docker/kiểm thử tải, không gọi việc chuyển sang thread pool là đã tối ưu xong mọi tác vụ nặng.

## 4. Cầu nối với web

- logoutUser gọi endpoint logout của backend và luôn xóa access token cục bộ trong finally, kể cả khi mạng lỗi. Nếu backend không liên lạc được thì không thể cam kết đã thu hồi cookie phía server.
- Các lời gọi refresh đồng thời trong cùng môi trường JavaScript dùng chung promise để không tranh dùng cùng một cookie đã xoay.
- Logout chờ các login/refresh đang chạy hoàn tất trước khi gửi lệnh thu hồi cookie cuối cùng. Kết quả refresh trễ không tự đặt lại access token sau khi thế hệ trạng thái xác thực đã đổi.
- Cơ chế chia sẻ promise có phạm vi một môi trường JavaScript; chưa điều phối nhiều tab bằng BroadcastChannel hoặc Web Locks.
- Không thay bố cục, biểu đồ hay màn hình trong đợt này.

## 5. Kiểm thử và bằng chứng

Các test mới được chạy ở trạng thái chưa sửa để tái hiện lỗi, rồi chạy lại sau sửa. Một số test cũ trước đây chấp nhận thiếu type, chấp nhận hai mật khẩu cùng 72 byte đầu và cho phép refresh replay; kỳ vọng đã được đổi sang hành vi an toàn. Payload SQLi được rút ngắn để nằm trong giới hạn độ dài mới, vẫn kiểm tra ký tự SQL không được thực thi.

| Nhóm | Test đạt |
|---|---:|
| apps/ml | 138 |
| apps/api | 212 |
| apps/web | 168 |
| infra | 35 |
| E2E contract reference/mô phỏng | 87 |
| Tổng | 640 |

Đợt này bổ sung 37 test API và ba test web, tăng từ 600 lên 640. Bộ E2E 87 test vẫn là reference/mô phỏng; không đổi tên thành E2E live. Bằng chứng PostgreSQL thật là lần kiểm tra tích hợp riêng bằng scripts/phase3_postgres_acceptance.py, không cộng vào số unit test.

Next.js production build, TypeScript noEmit với noUnusedLocals/noUnusedParameters, Ruff cho các module core/schema/router đã sửa và kiểm tra lỗi import/biến không dùng trên nguồn Python đều đạt. git diff --check không có lỗi whitespace. Các cảnh báo cũ về TestClient/httpx, tình huống ORM/JWT trong test và LightGBM vẫn được ghi nhận; không thay thư viện để che cảnh báo.

Migration được kiểm tra upgrade/downgrade trên SQLite tạm, sinh SQL PostgreSQL và chạy upgrade thật trên PostgreSQL cục bộ. Không downgrade CSDL dự án. Lần probe thật xác nhận đã xóa hết người dùng/phiên thử.

## 6. Bước tiếp theo

Phase 4 hoàn thiện giao diện và cách trình bày kết quả: nối cập nhật preset/watchlist và phân trang vào UI, làm rõ nguồn/ngày dữ liệu, sửa cách trình bày confidence/quỹ đạo và phân biệt dữ liệu thật với số liệu ước lượng/minh họa. Đặc biệt cần rà soát các nhánh tạo dữ liệu chỉ số/market board từ hệ số hoặc giá trị dự phòng; Phase 3 chưa xác minh hay thay thế các dữ liệu đó.

Các giới hạn dữ liệu quyền cổ đông, survivorship bias và kết quả chẩn đoán của Phase 2 vẫn còn hiệu lực. Các bản sửa API không làm các con số tài chính đó tự trở thành số liệu cuối cho đồ án.

## Tài liệu đã đối chiếu

1. FastAPI, Concurrency and async/await: https://fastapi.tiangolo.com/async/
2. PyJWT, Usage Examples và yêu cầu claim: https://pyjwt.readthedocs.io/en/stable/usage.html
3. SQLAlchemy 2.0, Session Basics và rollback: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
4. pyca/bcrypt, giới hạn độ dài mật khẩu và xử lý mật khẩu dài: https://github.com/pyca/bcrypt
5. IETF, RFC 9700, Best Current Practice for OAuth 2.0 Security, 01/2025: https://www.rfc-editor.org/rfc/rfc9700.html
