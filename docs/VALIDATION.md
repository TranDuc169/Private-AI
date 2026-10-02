# Biên bản kiểm tra — cập nhật 03/10/2026

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
| BGE-M3 / Qwen3 | Chưa chạy, không nằm trong mã kết nối tuần 2 này |

Đã chạy 7 tình huống API client trên bản source cuối bằng Node REPL (mock fetch; không phải kết nối backend). Đã thêm test source cho backend và frontend cùng script `backend/check_db.py` kiểm tra DB thật. Lệnh và kết quả kỳ vọng ở README. Những test chưa thực thi không được tính là PASS.

## Kiểm tra lại bằng công cụ ngày 03/10

Output thực tế lưu ở [evidence/2026-10-03-checks.txt](evidence/2026-10-03-checks.txt).

- Node/npm và Git đã có. Working tree sạch trước khi cập nhật tài liệu; commit local `fcfbca1`.
- `npm test`: đạt 4 test, dùng mock fetch.
- `npm run build`: esbuild báo Access is denied khi đọc thư mục cha trong môi trường công cụ; không hoàn tất build ở lần này.
- `.venv` không tạo được tiến trình từ Python312 đã cài trong hồ sơ Admin; vì pytest chưa chạy được nên không chạy tiếp Alembic/check_db.
- HTTP tới 127.0.0.1:8000 bị từ chối kết nối tại thời điểm kiểm tra lại.
- `git ls-remote` không chạy được vì Git trong môi trường công cụ thiếu helper remote-https.

Các hạn chế trên không phủ nhận kết quả chạy thành công trước đó trên CMD của người dùng. Không ghi những bước chưa xác minh trực tiếp thành PASS của trợ lý.

## Minh chứng còn cần lưu để chốt tuần 2

1. Ảnh kết nối xanh và /health trong cùng lần chạy; output pytest, alembic check, check_db.py, npm test và npm run build kèm ngày/commit.
2. BGE-M3: một câu đầu vào, shape vector, thời gian encode; tách thời gian tải model khỏi suy luận.
3. Qwen3 qua Ollama: tag model, câu hỏi/câu trả lời, thời gian; ghi CPU, RAM, GPU/VRAM và phiên bản công cụ. Chưa tải/chạy model trong lần cập nhật này.
4. Khánh: commit đã clone và kết quả làm theo README.

Không lưu .env, token hoặc mật khẩu vào minh chứng. Chạy thử model không đồng nghĩa hoàn thành RAG.
