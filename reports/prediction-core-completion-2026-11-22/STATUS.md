# Hoàn thiện ba mục tiêu trọng yếu — 22/11/2026

Mục tiêu mới: kiểm chứng worker → SSI → training → publication → serving trên bản sao; thống nhất runtime với artifact; đánh giá ngoài mẫu và xác minh tích hợp cuối. Không commit/push, không chặn/sửa giá theo heuristic; hạn chế SSI được chấp nhận và công bố.

## Đã thực hiện

- Ghi baseline source HEAD/trạng thái Git, phiên bản package, hash và sao chép 12 artifact gốc tại baseline.json và serving-artifact-copy/. Không ghi đè production.
- Chốt 30.450 dòng đặc trưng từ snapshot SSI đã lưu, hash đầu vào tại baseline.json, phục vụ so sánh cùng scaler/model giữa các runtime.
- Runtime host 1.7.2 đã suy luận trên toàn bộ bộ đầu vào; output npz/json đã lưu. Docker 1.9.1 đang chờ lệnh điều khiển container hoàn tất; chưa có kết quả so sánh, không đánh dấu đạt.
- Khóa scikit-learn==1.7.2 trong shared ML package và cập nhật hai uv.lock; nguyên nhân lệch trước đó là resolver chọn phiên bản khác cho Python <3.11 và >=3.11. Regression infra runtime contract đạt.
- Metadata training nay ghi runtime_versions cho artifact tương lai. Test fitting/publish trên thư mục tạm đạt; không retrain production.
- Đánh giá 3 fold cố định đang chạy trong quality/ với snapshot SSI gốc, không promote artifact hoặc tuning theo test. Hạn chế điều chỉnh giá vẫn được giữ trong báo cáo cuối.

## Còn phải làm

- Hoàn tất so sánh 1.7.2/1.9.1, build và kiểm tra runtime thống nhất trong Docker, kèm rollback.
- End-to-end worker thật gọi API cô lập, đồng bộ SSI, training và phục vụ generation mới; kiểm tra lỗi trên bản sao và quyết định cấu hình writer/worker vận hành.
- Chốt chất lượng, baseline và giới hạn theo kết quả chạy thực tế và hash/version tương ứng.
- Một lượt giao diện đăng nhập trên Docker mục tiêu cuối cùng, chọn mã/đổi model/trajectory/lịch sử/lỗi; không rà lại UI nhỏ.

Docker API ứng dụng vẫn healthy trong lượt kiểm tra, nhưng các lệnh điều khiển container đang treo dù /_ping của engine phản hồi. Lệnh Docker Desktop restart đã được gọi để phục hồi control plane, chưa xác nhận hoàn tất. Không restart các phép thử đang chạy chỉ vì chưa nhận được output.


## Cập nhật sau phép đo

- Docker Desktop restart đã hoàn tất; API/DB trở lại healthy. Lượt cp/exec trước đó đã kết thúc lỗi trong lúc restart; đã chuẩn bị sandbox mới rồi chạy lại sau khi xác nhận terminal, không chạy lại do timeout quan sát đơn thuần.
- compatibility-full-comparison.json: 30.450 hàng scaler/LGB và 30 cửa sổ LSTM; scaler maxdiff0, LGB maxdiff1.11e-16, LSTM maxdiff5.96e-8 giữa host và Docker; không đổi nhãn ở các mẫu đã thử. Đây không phải bảo đảm cho artifact bất kỳ.
- Image candidate infra-vn_stock_api:core-runtime-172 đã build và chạy offline trên bản sao artifact, network=none. Chưa thay image production hoặc promote model.
- Metadata/runtime contract tests đạt. Còn xác minh unit/runtime trong candidate, luồng worker tích hợp và E2E đăng nhập cuối trước khi triển khai.
- quality/ đã hoàn tất ba fold40 epoch tối đa, early stopping; mỗi model1.800 mẫu, không trùng model/symbol/date giữa fold. Accuracy LGB47,50%, LSTM44,83%, baseline58,39%; macro-F1 tương ứng0,3995/0,3656/0,2458. QUALITY.md chốt phạm vi và giới hạn; quality-artifact-provenance.json lưu hash/version từng fold.
- production-artifact-check.json: toàn bộ12 artifact baseline không đổi; các model fold chỉ nằm trong reports.


## Worker tích hợp và giao diện — cập nhật tiến trình

- worker-source-failure.json: worker thật nhận lỗi SSI được gây trong sandbox, exit1, 12 file model không đổi.
- Phát hiện/sửa lỗi CORE bị truyền None và pipeline mở rộng thành VN30; retrain-scope-before.txt tái hiện, retrain-scope-after.txt 48 test đạt. Scope CORE nay truyền đúng chuỗi CORE.
- worker-integration.json: CORE chạy thành công, 5 mã; generation mới 9e8735ae2f4a4937a785491fb1319b79, API reload hai model từ legacy cache sang cùng bundle; có SSI thật, sandbox không mount production.
- worker-vn30-integration.json: VN30 thành công với30 mã,226,919 giây; generation mới2da17faa147b4b1e9ac59c8313f5eae1; API trả đúng generation và runtime1.7.2 cho VIC/HPG ×2 model. Chưa promote bundle này hoặc cập nhật image production.
- Giao diện bản sao localhost3002 dùng API Docker sandbox8003: đã đăng nhập tài khoản giả core-audit@example.test; đã quan sát VIC/LightGBM và VIC/LSTM có ngày20/11, xác suất và kịch bản23→25/11 cùng lịch sử. Lần xem LSTM mới top status còn ghi Chưa tải được dù dữ liệu dự báo có; cần kiểm tra nguyên nhân endpoint trạng thái trong lượt tích hợp cuối, chưa đánh dấu toàn bộ UI đạt. Chưa kiểm tra hết HPG/hai model, lỗi/phục hồi, screenshot và console ở image đích cuối.
- Docker sandbox/source-copy được chuẩn bị bởi prepare_training_sandbox.py và prediction_training_sandbox.py; worker actual bởi run_training_worker_integration.py. API boot hạ quyềnUID1001 sau khi chuẩn bị thư mục riêng; không có host mount data/model.
- Còn cấu hình/triển khai runtime chuẩn và writer/worker vận hành, kiểm chứng fault artifact trên bản sao và E2E cuối. Không commit/push.

## Kiểm tra trạng thái sau phiên đăng nhập dài

- Log container sandbox v2 xác nhận GET /api/v1/predict/status trả401 trong khi endpoint dự báo công khai trả200; không phải bundle thiếu metadata. Access token hết hạn sau phiên mở lâu, status fetch trước đây chỉ log lỗi và UI suy diễn thành chưa từng cập nhật.
- AIPredictionTab nay phân biệt đang tải/lỗi/dữ liệu thành công, báo rõ401 cần tải lại trang để khôi phục phiên, có thử lại, không hiển thị “Chưa có lần cập nhật nào” khi request thất bại. Effect phụ thuộc userId và lần thử lại; không dùng ngày dự báo thay cho trạng thái server.
- AIPredictionTab.status.test.tsx: 1 test đạt, bao phủ lỗi401 → không gán thông tin cập nhật giả → retry thành công. git diff --check đạt. Chưa xác minh thay đổi này trong trình duyệt hoặc bản web sandbox (bản sao frontend chưa cập nhật file mới).

## Cấu hình writer vận hành

- Cả hai Compose nay có vn_stock_training_api nội bộ, không mở host port, dùng cùng image với inference qua VN_STOCK_API_IMAGE. Inference vẫn mount data/models read-only; writer có mount ghi và worker gọi writer thay vì inference. Writer dùng UID/GID cấu hình ML_WRITER_UID/GID, không chown thư mục thật.
- training_api_entrypoint.py kiểm tra worker secret và quyền tạo file tạm thật trên models/raw/interim/processed trước khi mở API; tắt startup sync để tránh chạy song song ngoài job. Writer chờ inference healthy/migration hoàn tất.
- 6 test infra liên quan đạt; docker compose --env-file .env -f infra/docker-compose.yml config --quiet đạt; git diff --check đạt.
- Chưa khởi chạy writer hoặc thay image production. Tiếp theo cần backup image đang chạy + hash source/artifact, chọn UID/GID phù hợp, thử entrypoint trên bản sao qua Docker, rồi triển khai và xác minh health/API/UI. Không dùng bundle huấn luyện sandbox thay production.

## Artifact fault và chuẩn bị triển khai

- artifact-fault-integration.json: làm hỏng scaler chỉ trong sandbox v2, cả LightGBM/LSTM giữ nguyên generation và xác suất cache, báo degraded_cached_generation; khôi phục bytes gốc xong cả hai healthy. Không đụng artifact thật.
- Đã tag image đang phục vụ thành rollback-core-20261122; DEPLOYMENT.md ghi imageID, project Compose thực, điều kiện UID/GID, lệnh triển khai và rollback. Chưa thực thi triển khai.
- Phép thử writer preflight trong container riêng với bind thư mục tạm và UID501:20 đang chạy qua exec session78258; docker run PID66895 còn sống, Docker ps chưa thấy container mới. Đây là chờ thao tác Docker create/run, chưa kết luận quyền ghi lỗi hay khởi chạy lại. Cần poll cùng handle trước mọi retry. API/DB và sandbox đang chạy bình thường.

## Kiểm chứng quyền writer và hồi quy

- Docker exec --user501:20 trong sandbox v2 chạy entrypoint verify_training_storage trên thư mục riêng /tmp/core-writer-uid-probe đạt. Chưa chứng minh quyền bind mount thật.
- Lệnh Docker run preflight session78258/PID66895 đã được hủy có chủ đích (exit143) sau khi log Docker cho thấy pending mount/share và không có container tạo. Báo cáo writer-preflight-docker.json ghi thất bại/hủy, không ghi đạt.
- Lần thử thay thế dùng thư mục bản sao dưới reports, container name vn-stock-core-writer-preflight-20261122, session35472 đang chờ; chưa có container xuất hiện khi kiểm tra. Poll cùng handle trước khi retry; không restart Docker chỉ vì timeout.
- Hồi quy mới: API audit/services + worker + writer56passed; AIPredictionTab ba file5passed; TypeScript noEmit và ESLint hai file thay đổi đạt.
- Đã cập nhật component trạng thái vào bản sao frontend sandbox3002 để kiểm tra trình duyệt lần tới. Chưa reload UI hoặc xác minh thông báo mới trong trình duyệt.

## E2E đăng nhập sandbox tiếp tục

- UI localhost3002 đã hiển thị lỗi401 rõ ràng. Reload qua giao diện khôi phục phiên thành công; trạng thái trả ngày20/11 và retrain12:57 22/11, không còn thông báo lỗi.
- Chọn HPG từ search thật: LightGBM data20/11, giá20.450đ, UP25,3/HOLD43,9/DOWN30,8%, T+1/2/3 lần lượt20.440/20.430/20.420 ngày23/24/25; lịch sử thêm đúng HPG LightGBM.
- Đổi HPG LSTM: loading không giữ kết quả model trước; data20/11 giá20.450đ, UP30,8/HOLD39,4/DOWN29,9%, ba điểm minh họa20.450 ngày23/24/25; lịch sử thêm HPG LSTM. Đóng model-info dialog thành công. Screenshot quan sát viewport hẹp có trạng thái/nhãn khớp; chưa lưu artifact screenshot do hạn chế xuất đã ghi trước đây.
- Đây là UI bản sao + API Docker sandbox, chưa phải xác minh deployment cuối. Tab giữ HPG LSTM cho lần sau. Còn lỗi/phục hồi UI và xem trực quan vùng chart, console ở phiên/image cuối.

## Chẩn đoán Docker control plane và hồi quy cấu hình

- Control container không mount ccf20dea... tạo thành công. docker start -a bị kẹt ở attach/wait trước khi gửi start; docker start không attach chạy được và inspect xác nhận exited0. Session74573 còn chờ attach/wait dù container đã terminal. Chưa rm vì dòng lệnh nối tiếp đang đợi.
- Hai request tạo container bind mount (session35472 và89393) còn chờ, log init.log có POST containers/create nhưng không có completion/container; không chỉ riêng thư mục tạm. Đây là lỗi control plane Docker/bind mount, chưa kết luận quyền writer.
- Docker Desktop restart đã gọi một lần, session51805/PID69276 đang sống; docker desktop status=stopping lúc kiểm tra. Không khởi chạy thêm restart hoặc lặp preflight trước khi trạng thái terminal. Production và sandbox sẽ cần health/reload sau restart, không mất filesystem/container volumes.
- Đã bổ sung biến image/UID/GID và SSI runtime vào .env.example, không chứa thông tin bí mật. Hai bộ test Docker cấu hình lần đầu phát hiện SSI chưa được ghi trong example (20pass1fail); đã bổ sung và chạy lại21passed.
- Deployment vẫn chưa thực hiện; artifact fault/quality/runtime evidence đã hoàn tất như trên. Tiếp tục poll51805,35472,89393,74573 trước retry; giữ tab sandbox HPG LSTM cho E2E cuối.

## Runtime/worker đã triển khai

- Restart Desktop51805 kết thúc0, engine running. Các request bind mount trước đó kết thúc lỗiEOF; không chạy trùng. Preflight container mới f3c49ec... tạo/start tách riêng, exited0 với UID501:20 và ghi thư mục bản sao bind mount thành công: writer-preflight-after-restart.json.
- Đã lưu source snapshot predeployment-source.tar.gz và predeployment-config-selection.json (chỉ ba biến không bí mật); .env nay lưu image core-runtime-172 và UID/GID501:20 để các lần Compose tiếp theo nhất quán. Docker Compose root/project stocktrendprediction được dùng đúng stack.
- API đang phục vụ đã chuyển sang image327012725...; vn_stock_api và vn_stock_training_api healthy, sklearn1.7.2; writer UID501:20, không public port, data/models RW; inference vẫn RO. vn_stock_retrain_worker running, URL training_api, lịch Chủ Nhật02:00ICT. deployed-runtime.json lưu state/image/mount/version/log không chứa Env/bí mật.
- deployed-api-smoke.json: VIC/HPG×LightGBM/LSTM thành công, data20/11, xác suất hữu hạn/tổng hợp lệ và trajectory3; serving_status healthy. Vẫn generation legacy78b54b04ae9c3fee và71d398842a1f2650 như gốc; 12artifact hash không đổi. Không ép retrain hoặc promote model sandbox.
- Lưu ý test harness: start sandbox v2 sau Docker restart đã chạy lại bootstrap cũ, copy lại snapshot gốc rồi lỗi vì tài khoản SQLite trùng. Việc này chỉ ảnh hưởng sandbox (generation VN30 thử nghiệm trước đó không còn là current); bằng chứng worker lịch sử trong reports vẫn giữ. Đã sửa bootstrap chỉ copy/trim lần đầu và seed account nếu chưa tồn tại, cập nhật /tmp/bootstrap.py rồi start lại. Không chạy lại training đã kiểm chứng. Cần xác nhận sandbox phục hồi và không dùng nhầm generation cũ cho E2E hiện tại.
- Còn nghiệm thu UI trên backend/runtime đích cuối, lỗi/phục hồi, kiểm tra trực quan chart/console và chốt bàn giao. Không commit/push.

## Web Docker và lỗi/phục hồi UI

- Đã backup image Web rollback-core-20261122, build Web mới core-final-20261122 (web-final-build.log, thành công), Compose root/infra thêm VN_STOCK_WEB_IMAGE; .env lưu candidate Web, example ghi biến. vn_stock_web đã khởi động cổng3000, dùng API8000.
- Thử lỗi chỉ sandbox: stop API8003 rồi đổi VIC LightGBM→LSTM trong UI3002. UI báo Không thể tải dự báo, các xác suất là dấu gạch (không phải0%), có Thử lại; lịch sử vẫn4 bản ghi, không ghi dự báo lỗi. Status cũng báo lỗi riêng.
- Start lại API8003 với bootstrap idempotent, đóng dialog mô hình, bấm Thử lại và Thử tải lại trạng thái: cả hai phục hồi; VIC/LSTM data20/11, giá241900, UP31,7/HOLD26,9/DOWN41,4, đủ trajectory3 ngày23/24/25; nến và ngày căn cứ khớp. Đây là generation legacy sau sandbox reset, không phải bundle VN30 thử nghiệm trước đó.
- Khi sandbox vừa copy lại dữ liệu trước đó, đã quan sát nến18/11 nhưng dự báo20/11; UI chủ động báo ngày chưa khớp và không vẽ kịch bản. Khi dữ liệu cache được cập nhật và tải lại, ngày/nến khớp. Không sửa giá hoặc suy hệ số điều chỉnh.
- Còn kiểm tra logged-in UI3000 + API8000, hình chart/console và chốt bàn giao. Không gửi email xác minh hoặc tạo tài khoản thật bằng công cụ.

## Nghiệm thu trực quan và chờ phiên thật

- Screenshot sandbox VIC/LSTM sau phục hồi xác nhận đường minh hoạ ba điểm đỏ đi từ nến241,9 tới232,11 nằm trong vùng chart; nhãn Minh hoạT+3 và chú giải đúng. coreTab.dev.logs levels:error limit5 trả[]. Đây là kiểm tra sau phục hồi, không phủ định các lỗi kết nối đã gây trước đó.
- Hồi quy Compose/SSI/runtime/writer/Docker sau biến Web:27passed; git diff --check đạt. Web image candidate đã build thành công và đang chạy3000; rollback Web ghi DEPLOYMENT.md.
- Trình duyệt mở UI3000 bị chuyển tới form Đăng nhập, không có phiên tài khoản thật. Tài khoản core-audit chỉ thuộc SQLite sandbox8003, không dùng được trên PostgreSQL production8000. Chưa gửi thông tin đăng nhập giả sang production, không sửa database/user hay tạo phiên giả để vượt kiểm tra.
- Còn chờ người dùng đăng nhập UI3000 trong tab4/browser2 để nghiệm thu cuối VIC/HPG×hai model, giá/ngày/probability/trajectory/history/console với backend đang phục vụ. Tab3 là sandbox3002. Các phần đánh giá/model/runtime/worker đã có bằng chứng; không chạy lại toàn bộ khi tiếp tục.

## Bàn giao trước bước đăng nhập thật

- HANDOFF.md tổng hợp kết quả, giới hạn, lệnh test và phần chưa nghiệm thu, không cộng trùng số test giữa các nhóm.
- handoff-integrity-check.json lúc09:29:49UTC:12artifact production không đổi,18artifact của3fold khớp hash manifest/provenance; cả4dịch vụ API/writer/worker/Web running, hai API healthy. Git HEAD không đổi.
- Chờ người dùng đăng nhập Web3000 trong tab4/browser2, đã requestUserTakeover(authentication) ở lượt trước. Không tự nhập tài khoản sandbox sang production, không truy xuất mật khẩu hoặc chỉnh user/session. Không mở lại browser khi người dùng đang thao tác đăng nhập. Mục tiêu còn active, chưa hoàn tất và chưa đủ điều kiện blocked (vẫn hoàn thiện bàn giao độc lập được).

## Chặn nghiệm thu do chưa đăng nhập

- Kiểm tra UI chỉ đọc mới nhất: tab4/browser2 vẫn ở http://localhost:3000/login, form email/password rỗng. Chưa có phiên đăng nhập thật, đã giữ tab handoff; không nhập hoặc lấy mật khẩu.
- Cùng điều kiện thiếu phiên đã tồn tại từ lượt handoff gốc và hai lượt tiếp theo. Báo cáo, hash/model, service, rollback và các kiểm thử độc lập đã chốt; không còn công việc độc lập cần thiết để tiếp tục trước bước UI thật.
- Đánh dấu mục tiêu blocked do cần người dùng đăng nhập. Đây không phải hoàn tất. Khi người dùng báo đã đăng nhập và tiếp tục mục tiêu: kiểm tra tab4 còn tồn tại trong browser2, nghiệm thu VIC/HPG×hai model/ngày/giá/probabilities/trajectory/history/console, cập nhật ACCEPTANCE/HANDOFF rồi audit hoàn thành. Không chạy lại training, không ép job production và không rà toàn bộ các mã.

## Đã nghiệm thu sau khi người dùng đăng nhập

- Người dùng xác nhận đã đăng nhập và tiếp tục; UI3000/API8000 thực đã kiểm tra VIC/HPG×hai model. final-authenticated-ui.json lưu kết quả hiển thị đối chiếu API mới, ngày20/11, giá241900/20450, trajectory23/24/25; cả4tổ hợp khớp xác suất đã làm tròn.
- Quan sát chuyển mã/model: loading gạch ngang và không giữ kết quả lựa chọn cũ. VIC LightGBM đường đỏ3điểm nằm trong chart tới232,07. HPG toggle scenario tắt/bật, đổi6M thành công. Lịch sử0→4bản ghi; reload vẫn4; replay HPG/LSTM đúng giá/ngày/model và không ghi trùng. Console errors/warnings trả[]. Không gửi email xác minh hoặc truy xuất thông tin bí mật.
- Cập nhật ACCEPTANCE.md/HANDOFF.md: nghiệm thu hoàn tất trong phạm vi3mục tiêu; không diễn giải thành mô hình tốt hơn baseline hoặc chứng nhận toàn bộ audit cũ. final-service-state.json xác nhận Web/worker running, cảhaiAPI healthy. Hash12artifact production vẫn không đổi sau lượt kiểm tra cuối. Chưa ép production retrain; lịch tuần kế tiếp và giới hạn SSI/legacy-quality được công bố rõ.
- Không có thay đổi code sau các lượt test/config27pass, API/worker56pass, frontend5pass, tsc/ESLint đạt. Các nhóm có test chồng lặp, không cộng tổng độc lập. Không commit/push. Bàn giao cuối: HANDOFF.md, QUALITY.md, ACCEPTANCE.md, DEPLOYMENT.md cùng JSON/log được dẫn.
