# Biên bản kiểm tra — cập nhật 05/10/2026

## Tuần 3

Trợ lý chạy trực tiếp: 10 backend test đạt (SQLite tạm và health mock), 7 auth/workspace test đạt trên PostgreSQL với schema riêng, 6 frontend test đạt; build với configLoader runner đạt. Alembic check và check_db.py đạt trên DB local. Kiểm tra trình duyệt thật với hai tài khoản trên schema PostgreSQL tạm đạt; có ảnh desktop/mobile. Log và giới hạn cụ thể ở [week3/README.md](evidence/week3/README.md). Chưa có xác nhận nghiệm thu của người dùng hoặc Khánh cho tuần 3. Phần dưới là lịch sử tuần 2.

Phân biệt kiểm tra trực tiếp, ảnh trong cuộc trò chuyện và xác nhận bằng lời. Không coi test mock là minh chứng DB thật.

| Kiểm tra | Kết quả thực tế |
|---|---|
| PDF phân công | Đọc văn bản 7 trang |
| PDF báo cáo tuần 1 | Đọc văn bản 11 trang; xem ảnh chat prototype |
| GitHub repository | Ban đầu rỗng; người dùng đã xác nhận push. Local HEAD và origin/main cùng commit `fcfbca11ea726a8cf9b2a2055a55bf94ccb9f2bd`; chưa xác minh lại remote trực tuyến |
| API client: 200 đúng contract | PASS bằng Node REPL, mock fetch |
| API client: 503 DB down | PASS bằng Node REPL, mock fetch |
| API client: HTML thay JSON | PASS: từ chối phản hồi |
| API client: JSON thiếu field | PASS: từ chối phản hồi |
| API client: JSON null | PASS: báo sai contract |
| API client: HTTP 500 | PASS: báo lỗi HTTP |
| API client: lỗi mạng | PASS: truyền lỗi để UI hiển thị |
| React production build / tương tác UI | Ảnh cho thấy giao diện đã chạy. Người dùng báo build đạt; lần chạy lại bằng công cụ bị chặn quyền đọc thư mục cha |
| Frontend npm test | Trợ lý chạy trực tiếp ngày 03/10: 4 test PASS, 0 fail |
| pytest backend | Người dùng báo đạt; công cụ chưa chạy lại được Python312 trong hồ sơ Admin |
| PostgreSQL + migration + alembic check | Ảnh PostgreSQL Healthy, /health ok/up; người dùng báo check_db.py và alembic check đạt; chưa có output đầy đủ lưu trong repo |
| React → FastAPI → PostgreSQL | Người dùng xác nhận thành công sau khi chạy lại backend |
| Khánh chạy thử | Chưa có xác nhận |
| Qwen3 4B Instruct | PASS chạy độc lập theo JSON người dùng gửi: 3 câu tiếng Việt, 87 token, stop; tổng 9,664 s |
| BGE-M3 | PASS chạy độc lập theo JSON người dùng gửi: 1 vector 1024 chiều; tổng 5,236 s; trợ lý kiểm tra JSON và phần tử hữu hạn |

Đã chạy 7 tình huống API client trên bản source cuối bằng Node REPL (mock fetch; không phải kết nối backend). Đã thêm test source cho backend và frontend cùng script `backend/check_db.py` kiểm tra DB thật. Lệnh và kết quả kỳ vọng ở README. Những test chưa thực thi không được tính là PASS.

## Kiểm tra lại bằng công cụ ngày 03/10

Output thực tế lưu ở [evidence/week2/2026-10-03-checks.txt](evidence/week2/2026-10-03-checks.txt).

- Node/npm và Git đã có. Working tree sạch trước khi cập nhật tài liệu; commit local `fcfbca1`.
- `npm test`: đạt 4 test, dùng mock fetch.
- `npm run build`: esbuild báo Access is denied khi đọc thư mục cha trong môi trường công cụ; không hoàn tất build ở lần này.
- `.venv` không tạo được tiến trình từ Python312 đã cài trong hồ sơ Admin; vì pytest chưa chạy được nên không chạy tiếp Alembic/check_db.
- HTTP tới 127.0.0.1:8000 bị từ chối kết nối tại thời điểm kiểm tra lại.
- `git ls-remote` không chạy được vì Git trong môi trường công cụ thiếu helper remote-https.

Các hạn chế trên không phủ nhận kết quả chạy thành công trước đó trên CMD của người dùng. Không ghi những bước chưa xác minh trực tiếp thành PASS của trợ lý.

## Minh chứng còn cần lưu để chốt tuần 2

1. Ảnh kết nối xanh và /health trong cùng lần chạy; output pytest, alembic check, check_db.py, npm test và npm run build kèm ngày/commit.
2. Đã lưu minh chứng BGE-M3 và Qwen3 tại [MODEL_SMOKE_TEST.md](MODEL_SMOKE_TEST.md), gồm request, phản hồi JSON, kích thước vector, thời gian tổng/nạp model và cấu hình máy đã biết. Chưa xác minh VRAM/tỷ lệ CPU-GPU; BGE không trả riêng thời gian encode.
3. Kết quả model là smoke test từ output người dùng, chưa đánh giá chất lượng RAG. Không tính lần thử Thinking bị cắt token là PASS.
4. Khánh: commit đã clone và kết quả làm theo README.

Không lưu .env, token hoặc mật khẩu vào minh chứng. Chạy thử model không đồng nghĩa hoàn thành RAG.

## Minh chứng bổ sung đã có trong commit 3007e3a

Đọc các file trong [week2](evidence/week2/): backend 3 test pass (1 cảnh báo deprecation), frontend 4 test pass, Vite build thành công, Alembic không phát hiện thay đổi schema, check_db PASS đủ 5 bảng, Docker healthy, health JSON ok/up. Đây là output đã lưu trong repo, không phải chạy lại ở lần cập nhật tài liệu này. commit.txt ghi revision được kiểm tra là 834e89f. Có ba file ảnh minh chứng; lần này chưa kiểm tra lại nội dung ảnh. Các mục thiếu output ở phần lịch sử trên mô tả thời điểm trước khi bổ sung.

Tag week-02 đã có tại 3007e3a và được giữ nguyên. Xem [quy ước các tuần](evidence/README.md). Còn chờ Khánh xác nhận chạy thử.
