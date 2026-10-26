# Tuần 7 — Hỏi đáp Cơ sở dữ liệu có nguồn

## Hiểu luồng trước khi chạy

```text
Câu hỏi của bạn
  → BGE-M3 tạo vector câu hỏi
  → pgvector tìm tối đa 5 đoạn trong workspace bạn sở hữu
  → Qwen đọc câu hỏi + các đoạn nguồn
  → backend kiểm tra định dạng, mã nguồn và tài liệu còn hợp lệ
  → giao diện hiển thị câu trả lời và nguồn PDF/trang
```

Tuần 6 dừng ở các đoạn nguồn. Tuần 7 thêm Qwen để viết lời giải thích. Hai model có vai trò khác nhau: BGE-M3 tìm nội dung; Qwen diễn đạt câu trả lời. Cả hai chạy qua Ollama trên máy. Không gửi tài liệu sang dịch vụ AI bên ngoài.

## Tôi đã sửa những file nào?

| File | Vai trò và thay đổi |
|---|---|
| `app/retrieval.py` | Tách hàm tìm nguồn để API cũ và chat dùng chung; giữ lọc workspace/chủ sở hữu trước Top-K. |
| `app/generation.py` | Prompt học CSDL, gọi Ollama `/api/chat`, giới hạn thời gian/độ dài, yêu cầu JSON và kiểm tra mã trích dẫn. |
| `app/chat.py` | API mới `/workspaces/{id}/chat`, kiểm tra quyền, ghép retrieval → Qwen, kiểm tra lại nguồn sau khi model chạy. |
| `app/config.py`, `.env.example` | Cấu hình model Qwen, thời gian chờ và giới hạn token. |
| `app/main.py` | Đăng ký API, đổi tên ứng dụng; giới hạn một pipeline chat đồng thời trong mỗi process. |
| `tests/test_chat.py` | Kiểm thử quyền, dữ liệu đầu vào, model lỗi, nguồn sai/xóa giữa chừng và trạng thái bận. |
| `frontend/src/Chat.jsx` | Gọi API chat thật, hiển thị câu trả lời, nguồn mở rộng, lỗi/thử lại và hủy chờ. |
| `App.jsx`, `Account.jsx`, `Documents.jsx`, `styles.css`, `index.html` | Tên và lời hướng dẫn theo môn CSDL; không hiện số tuần hoặc tên thành viên trên sản phẩm. |
| `docs/course/` | 5 PDF demo, văn bản gốc, danh mục nguồn và giấy phép. |
| `load_demo_course.py` | Nạp PDF vào workspace mới qua tài khoản của bạn. |
| `evaluate_rag.py`, `docs/evaluation/week7.json` | 20 câu hỏi/đáp án tham chiếu; chạy model thật hoặc cả luồng PostgreSQL. |

Các đường dẫn backend trong bảng tính từ thư mục `backend`. Không thay schema, không cần migration mới. Giữ nguyên tài khoản và PDF đã có.

## Chạy bằng CMD trong VS Code

Mở thư mục dự án `private-ai-week2` trong VS Code. Terminal → New Terminal → Command Prompt. Tên thư mục cũ được giữ để các lệnh/đường dẫn trước đây không bị hỏng.

**Bước 1 — bật dịch vụ nền.** Mở Docker Desktop và Ollama. Tại thư mục gốc:

```cmd
docker compose up -d --wait db
ollama list
```

Lệnh đầu bật database đã có; `-d` chạy nền, `--wait` đợi sẵn sàng. Lệnh thứ hai liệt kê model đã tải. Cần `bge-m3:latest` và `qwen3:4b-instruct-2507-q4_K_M`. Nếu thiếu mới tải:

```cmd
ollama pull bge-m3
ollama pull qwen3:4b-instruct-2507-q4_K_M
```

`pull` tải model về máy, không phải lệnh chạy backend. Không thay bằng `qwen3:4b` vì đó là biến thể khác từng sinh suy nghĩ dài.

**Bước 2 — chạy backend.** Trong terminal thứ nhất:

```cmd
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

`cd` chuyển vào backend; `.venv\Scripts\python.exe` dùng thư viện riêng của dự án. Uvicorn phục vụ FastAPI; `--factory` gọi hàm tạo app, `--reload` nạp lại khi lưu mã. Giữ terminal mở. Nếu server cũ đã chạy, Ctrl+C rồi chạy lại. Mở `/health` để kiểm tra database, `/docs` để xem API; `/health` không kiểm tra model.

**Bước 3 — chạy frontend.** Terminal mới tại thư mục gốc:

```cmd
cd frontend
npm.cmd run dev
```

Vite chạy giao diện; mở địa chỉ terminal in ra, thường `http://127.0.0.1:5173`. Không cần npm install hoặc pip install mới cho chức năng ứng dụng tuần 7.

**Bước 4 — nạp học liệu.** Đăng ký/đăng nhập trên web nếu chưa có tài khoản. Terminal thứ ba tại thư mục gốc:

```cmd
cd backend
.venv\Scripts\python.exe load_demo_course.py
```

Script hỏi email và mật khẩu tại máy, tạo workspace mới, tải 5 PDF vào và xử lý. Không lưu mật khẩu. Chờ từng dòng READY; tải lại web, đăng nhập lại và chọn workspace `CSDL - Demo ...`. Script chạy lại sẽ tạo một workspace khác, không dùng nó như lệnh khởi động hằng ngày.

**Bước 5 — thử câu hỏi.** Nhập `LEFT JOIN khác INNER JOIN thế nào?`, bấm Gửi. Đợi model; mở nguồn dưới câu trả lời, đọc đúng trang PDF. Thử câu `Lịch thi Cơ sở dữ liệu của trường tôi ngày nào?`: không có dữ liệu này trong bộ mẫu, câu trả lời cần thừa nhận thiếu căn cứ. Nếu model vẫn bịa, ghi vào lỗi đánh giá, không coi là đạt.

## Kiểm thử và đọc kết quả

Trong backend:

```cmd
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe test_postgres.py
.venv\Scripts\python.exe evaluate_rag.py --mode postgres --output ..\docs\evidence\week7\postgres-live-user-01.json
```

- `pytest`: kiểm tra logic; các bài cần PostgreSQL sẽ skip ở chế độ mặc định. Model được mock trong unit test để kiểm tra lỗi có thể lặp lại.
- `test_postgres.py`: chạy các bài với database thật trong schema tạm, không dùng bảng tài khoản thật làm fixture.
- `evaluate_rag.py --mode postgres`: tạo schema riêng, upload/trích chữ/index 5 PDF qua API trong TestClient, gọi BGE-M3/Qwen thật với 20 câu; lưu câu trả lời, nguồn, thời gian rồi dọn schema. Có thể tốn nhiều phút. Đây không phải lệnh nạp workspace vào tài khoản của bạn.
- `--output`: nơi lưu minh chứng. Nếu file đã có, công cụ từ chối ghi đè; lần sau đổi tên thành `...-02.json`.

Nếu Docker chưa chạy nhưng muốn thử riêng model:

```cmd
.venv\Scripts\python.exe evaluate_rag.py --mode models --output ..\docs\evidence\week7\models-user-01.json
```

Chế độ `models` dùng PDF và BGE/Qwen thật nhưng tính cosine trong bộ nhớ, **không kiểm chứng PostgreSQL hay API production**. Không dùng kết quả này để khẳng định luồng database đã đạt.

Trong frontend, `npm.cmd test` kiểm tra API client, `npm.cmd run build` đóng gói giao diện. Việc build thành công chưa chứng minh câu trả lời học thuật đúng.

## Cách đánh giá câu trả lời

Mở JSON đánh giá, đối chiếu từng `answer` với `reference` và nguồn. Điền nhận xét trong một bản review riêng: đúng kiến thức không, nguồn có thực sự hỗ trợ ý đó không, có bịa khi thiếu tài liệu không. `expected_source_rank` chỉ cho biết tìm đúng trang ở vị trí nào, không chấm chất lượng lời giải thích. Bộ 20 câu này là bộ phát triển, không phải bộ đánh giá độc lập cuối kỳ.

## Giới hạn đang giữ rõ

- Mỗi câu hỏi độc lập; không gửi các lượt trước làm ngữ cảnh. Giao diện giữ tối đa 10 lượt, đổi trang/workspace hoặc reload sẽ mất. Lưu lịch sử là tuần 8.
- Không stream từng chữ; đợi model hoàn tất mới hiển thị. BGE tối đa 120 giây và Qwen tối đa 120 giây mỗi bước; trình duyệt chờ khoảng 250 giây. Dừng chờ không bảo đảm dừng model ở server.
- Một pipeline chat đồng thời mỗi process; yêu cầu khác nhận 429. Đây là giới hạn demo, chưa phải hàng đợi đa người dùng/đa worker.
- Kiểm tra mã trích dẫn tồn tại không chứng minh mọi câu bám nguồn. Prompt hạn chế bịa/injection nhưng không bảo đảm tuyệt đối; cần review bộ thử.
- Nếu model trả danh sách `source_ids` hợp lệ nhưng quên ký hiệu trong câu trả lời, backend bổ sung dòng “Nguồn tham khảo: [n]”. Dòng này cho biết nguồn model chọn, chưa phải kiểm chứng từng nhận định.
- Không có ngưỡng cosine đã hiệu chỉnh, reranker hoặc kiểm chứng ngữ nghĩa tự động.
- Không chạy SQL, không làm roadmap/quiz/checklist, không đánh giá mức thành thạo.

Minh chứng và các phần chưa kiểm chứng: [evidence/week7/README.md](evidence/week7/README.md). Các tuần trước và lịch sử Git được giữ nguyên. Chưa tự commit/push để bạn tiếp tục thực hành.
