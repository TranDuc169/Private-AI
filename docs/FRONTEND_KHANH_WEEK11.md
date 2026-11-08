# Bàn giao frontend Khánh — phạm vi tuần 1–11

Đối chiếu báo cáo 12 tuần người dùng cung cấp (5 trang, mục phân công Khánh), tiếp tục từ nhánh `frontend-khanh` đã có trên GitHub tại `97d781a`. Không viết lại lịch sử tuần trước, không thay backend/migration/API, không merge vào `main`.

## Giao diện và dữ liệu

React + Vite, giao diện sáng với sidebar xanh đậm, bố cục desktop/mobile. Một ô chat chung nhận câu hỏi, tóm tắt, roadmap và quiz; các thẻ gợi ý chỉ điền câu hỏi, người dùng tự gửi. Không có bộ chọn tác vụ hoặc phản hồi AI giả trong ứng dụng.

- Tài khoản: đăng ký/đăng nhập JSON đúng API, Bearer JWT giữ trong bộ nhớ. Reload yêu cầu đăng nhập lại; sau đó chọn workspace và mở lịch sử để tiếp tục. Đăng xuất/hết hạn xóa phiên và dữ liệu riêng.
- Workspace: chọn/tạo/đổi tên/xóa workspace trống. Thu gọn phần quản lý để nội dung học được ưu tiên trên mobile.
- Chat: giữ `conversation_id`/`revision`, loading, timeout, dừng chờ, thử lại, lỗi xung đột. Nêu rõ model chưa đọc lượt trước. Không gửi `mode` hoặc cấu trúc kế hoạch tự dựng.
- Tài liệu: upload PDF, trích văn bản, index, trạng thái từng bước, retry, văn bản phân trang, đoạn nguồn, xóa có xác nhận. Không coi trích xuất thành công là đã sẵn sàng hỏi đáp.
- Nguồn/tóm tắt: giữ ID trích dẫn, trang, bản chụp và mở đoạn hiện tại qua API có JWT. Hiển thị giới hạn/phạm vi tóm tắt, không coi cosine là xác suất đúng. React hiển thị văn bản thuần, không thực thi HTML từ tài liệu/model.
- Lịch sử: tìm theo tiêu đề, sắp theo thời gian mới nhất, mở lại hội thoại đã lưu. Đổi workspace hủy request và remount màn hình theo ID.
- Roadmap: bước học có mục tiêu/hoạt động/tiên quyết/lịch/nguồn, xác nhận bản nháp, checklist dùng revision từ server, thanh tiến độ và liên kết về kế hoạch.
- Quiz: chỉ gửi lựa chọn, không gửi điểm/đáp án chuẩn. Đủ lựa chọn mới nộp; chỉ hiển thị giải thích/kết quả server sau nộp. Giữ trạng thái draft và kết quả đã lưu.
- Tiến độ: API hội thoại → chi tiết → kế hoạch/quiz hiện tại. Chỉ tính bước tồn tại trong spec của kế hoạch đã xác nhận, phân biệt tự đánh dấu với kết quả quiz. Chọn tối đa **50 hội thoại mới nhất theo created_at**, 4 request mỗi loại mỗi batch (tối đa 8 khi đọc đồng thời plans/quizzes), thông báo thiếu một phần và thử lại. Số hội thoại đã lưu là tổng danh sách API.

Không thêm/đổi API. Dashboard tổng hợp toàn bộ workspace lớn cần thống nhất endpoint/phân trang với Đức trong công việc tiếp theo; hiện UI công khai giới hạn 50 hội thoại.

## Đối chiếu công việc theo tuần

| Tuần | Phần frontend bàn giao/giữ lại | Kiểm chứng trong lần làm này |
| --- | --- | --- |
| 1 | Bố cục, điều hướng, prototype được triển khai bằng UI thật | Ảnh desktop/mobile, không sửa minh chứng cũ |
| 2 | React gọi FastAPI, trạng thái kết nối DB | `/health` thật, frontend unit và build |
| 3 | JWT và CRUD workspace | Browser đăng ký, đăng nhập, tạo/chuyển workspace, đăng xuất; backend quyền có bộ test PostgreSQL |
| 4 | PDF, trạng thái xử lý, xem văn bản, xóa | Upload/process bằng HTTP thật, browser xem/xóa PDF |
| 5 | Index/retry, trang/đoạn/trạng thái vector | Giữ luồng hiện có; test PostgreSQL kiểm tra pipeline với model giả lập; chưa chạy BGE-M3 thật |
| 6 | Hiển thị nguồn/trang và điểm đúng nghĩa | Giữ source card; unit/backend và browser fixture nguồn |
| 7 | Chat API thật, chờ/lỗi/thử lại | Chat không có tài liệu và persistence trên API thật; chưa xác nhận sinh câu trả lời Qwen thật |
| 8 | Nguồn, lịch sử/reload, tóm tắt, cách ly workspace | Browser thật lịch sử/reload/chuyển workspace; fixture nguồn hiện tại/404; test backend cho tóm tắt |
| 9 | Roadmap/checklist/nguồn/tiến độ từng bước | Browser fixture xác nhận revision, checklist, mở lại; test PostgreSQL dùng model giả lập |
| 10 | Quiz trong chat, nộp và kết quả/giải thích | Browser fixture kiểm body chỉ có answers, chờ đủ lựa chọn, mở lại kết quả; test PostgreSQL quyền/chấm |
| 11 | Ghép học–quiz–tiến độ, desktop/mobile, trạng thái trống/lỗi | 3 browser tests + 14 unit tests; chưa có khảo sát người học |

Đây là đối chiếu chức năng và kiểm thử hiện tại, không khẳng định cá nhân đã thực hiện từng tuần trong lịch sử. **Số sinh viên dùng thử thực tế trong lần làm này: 0.** Không tạo phản hồi khảo sát hoặc kết quả model giả.

## Chạy và kiểm tra lại

Theo `HUONG_DAN_CHAY.md`: PostgreSQL/pgvector, migration `alembic upgrade head`, backend một worker ở 8000, frontend ở 5173. Dùng Python 3.12, Node >=22.12.

```bash
cd frontend
npm ci
npm test
npm run build
npm run dev
```

Ở terminal khác, chạy browser tests với backend và frontend đang hoạt động, **chỉ dùng DB phát triển/thử nghiệm**. Bộ test thật tạo tài khoản/workspace/hội thoại kiểm thử có email `khanh-e2e-…@example.com`; PDF được xóa qua UI. Không chạy vào dữ liệu production.

```bash
cd frontend
# Nếu chưa có browser Playwright: npx playwright install chromium
npm run test:e2e
# Trong cloud hiện tại dùng Chromium đã cài:
CHROMIUM_PATH=/usr/bin/chromium npm run test:e2e
```

Có thể đặt `E2E_BASE_URL`, `E2E_API_URL` theo máy kiểm thử; `VITE_API_BASE_URL` phải trỏ cùng backend trước khi khởi động Vite. Log/ảnh browser mặc định ở `/tmp/private-ai-browser-results`. Không commit token hoặc `.env`.

```bash
cd backend
.venv/bin/python -m alembic check
.venv/bin/python -m pytest -q
.venv/bin/python test_postgres.py
```

`backend/check_db.py` hiện vẫn assert migration tuần 5 (`0003`) trong khi head là `0006_quizzes`; không dùng script cũ để kết luận schema mới sai hoặc downgrade DB. Không sửa backend trong PR frontend.

## Minh chứng và việc cần làm tiếp

Xem [kết quả và ảnh](evidence/week11/frontend-khanh/README.md). API/model thật chưa kiểm chứng đầy đủ: môi trường không có Ollama và mạng chặn `registry.ollama.ai` (CONNECT 403). Cần chạy lại trên máy có `bge-m3:latest` và `qwen3:4b-instruct-2507-q4_K_M` với PDF đã index để nghiệm thu trả lời/tóm tắt/roadmap/quiz đầu cuối. Không coi fixtures UI hoặc test model giả lập là bằng chứng chất lượng AI.

Kịch bản nghiệm thu với Đức: đăng nhập → chọn workspace → upload/index PDF → hỏi JOIN và mở nguồn → yêu cầu tóm tắt transaction, xem phạm vi → tạo roadmap đủ mục tiêu/mức nền/số buổi/phút → xác nhận/đánh dấu → Quiz SQL JOIN → nộp → xem tiến độ → reload/đăng nhập/mở lại → chuyển workspace/tài khoản khác kiểm tra cách ly. Thử 401/409/503, mất mạng, nguồn đã xóa; ghi lỗi thực tế. Mời 3–5 sinh viên nếu có thể và ghi phản hồi thật, không suy ra thành thạo từ checklist.
