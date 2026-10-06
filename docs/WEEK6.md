# Tuần 6 — Tìm đoạn liên quan trong tài liệu

## Đã thay đổi gì và vì sao?

Tuần 5 biến các đoạn PDF thành vector và lưu vào PostgreSQL. Tuần 6 biến **câu hỏi** thành vector bằng cùng BGE-M3 rồi so sánh với các vector đã lưu. Các vector gần nhau thường biểu diễn nội dung gần nghĩa.

| File | Thay đổi và tác dụng |
|---|---|
| `backend/app/retrieval.py` | API `POST /workspaces/{id}/retrieve`: xác thực quyền, tạo vector câu hỏi, tìm các đoạn gần nghĩa bằng cosine và trả nguồn. |
| `backend/app/schemas.py` | Quy định câu hỏi 1–2.000 ký tự, Top-K là số nguyên 1–10; định dạng kết quả rõ ràng. |
| `backend/app/main.py` | Đăng ký API mới vào FastAPI. |
| `frontend/src/Chat.jsx` | Một ô chat để gửi câu hỏi, hiển thị chờ/lỗi/thử lại, nguồn PDF và trang; có dừng chờ. |
| `frontend/src/App.jsx`, `styles.css`, `Documents.jsx` | Nối màn hình chat mới và cập nhật giao diện/trạng thái tuần 6. |
| `backend/tests/test_retrieval.py` | Kiểm tra quyền, thứ tự kết quả, cách ly workspace, tài liệu bị xóa và lỗi Ollama. |
| `backend/test_postgres.py` | Thêm kiểm thử retrieval vào bộ kiểm thử PostgreSQL thật. |
| `backend/evaluate_retrieval.py`, `docs/evaluation/week6.json` | Bộ 7 câu hỏi mẫu và công cụ đánh giá với BGE-M3/pgvector thật. |

**Top-K = 5** nghĩa là lấy tối đa 5 đoạn gần nghĩa nhất **trong workspace đang chọn**. SQL lọc workspace, chủ sở hữu, trạng thái sẵn sàng và model trước khi xếp hạng/lấy Top-K. Không tìm toàn bộ dữ liệu rồi mới bỏ tài liệu của người khác.

Mỗi kết quả có tên file, số trang, văn bản, vị trí ký tự và điểm cosine. Điểm này không phải xác suất câu trả lời đúng. Chưa đặt ngưỡng loại kết quả, nên câu ngoài nội dung tài liệu vẫn có thể trả các đoạn gần nhất.

Chưa gọi Qwen, chưa sinh câu trả lời RAG, chưa lưu các lượt tìm kiếm vào lịch sử database. Màn hình giữ tối đa 10 lượt; chuyển trang/workspace hoặc tải lại sẽ mất các lượt này. Dừng chờ chỉ hủy yêu cầu ở trình duyệt, không đảm bảo dừng công việc đang chạy ở server.

## Chạy trong VS Code (terminal CMD)

Mở đúng thư mục dự án bằng **File → Open Folder**. Chọn Terminal → New Terminal; chọn Command Prompt nếu muốn dùng nguyên các lệnh dưới. Giữ Docker Desktop và Ollama đang chạy. Tuần 6 không thêm thư viện hoặc migration; tiếp tục dùng database pgvector đã chạy tuần 5.

**Terminal 1 — tại thư mục gốc dự án:**

```cmd
docker compose up -d --wait db
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

- `docker compose ... db`: bật dịch vụ database đã khai báo trong compose.yaml; `-d` chạy nền; `--wait` chờ database sẵn sàng.
- `cd backend`: chuyển vào thư mục mã backend để đọc đúng cấu hình `.env`.
- `.venv\Scripts\python.exe`: dùng Python và thư viện riêng của dự án.
- `-m uvicorn`: chạy máy chủ FastAPI; `app.main:create_app --factory` gọi hàm tạo ứng dụng; `--reload` tự nạp lại khi sửa mã; host/port tạo địa chỉ `http://127.0.0.1:8000`.
- Nếu backend cũ đang chạy trong terminal, nhấn Ctrl+C ở terminal đó rồi chạy lại; không mở thêm server cùng cổng.

**Terminal 2 — mở mới tại thư mục gốc:**

```cmd
cd frontend
npm.cmd run dev
```

`cd frontend` chuyển tới giao diện. `npm.cmd run dev` chạy Vite theo script trong package.json. Mở địa chỉ Vite in ra (thường là `http://127.0.0.1:5173`). Giữ hai terminal mở khi dùng web.

## Tự kiểm tra bằng giao diện

1. Đăng nhập và chọn workspace có PDF đã báo **Sẵn sàng tìm kiếm**. Nếu chưa có, upload PDF có chữ rồi tạo vector trong Tài liệu.
2. Mở Chat chung, nhập câu hỏi về một thông tin có thật trong PDF. Nhấn Enter hoặc Tìm đoạn.
3. Kiểm tra kết quả có đúng tên file, trang và đoạn chứa thông tin. Mở Thông tin truy xuất để xem điểm và vị trí ký tự.
4. Chuyển sang workspace trống rồi hỏi lại: phải báo chưa có đoạn sẵn sàng, không hiện nguồn của workspace trước.
5. Chọn workspace có vector, thoát Ollama rồi gửi câu hỏi: phải báo lỗi; mở Ollama và thử lại. Workspace trống không gọi Ollama nên không dùng để kiểm tra trường hợp này.

## Lệnh kiểm thử và ý nghĩa

Mở terminal thứ ba, từ thư mục gốc chạy:

```cmd
cd backend
.venv\Scripts\python.exe test_postgres.py
.venv\Scripts\python.exe evaluate_retrieval.py
```

Lệnh đầu chạy kiểm thử với PostgreSQL/pgvector, gồm kiểm tra không lẫn dữ liệu giữa người dùng/workspace. Lệnh thứ hai gọi BGE-M3 thật, tạo dữ liệu mẫu trong schema riêng, tìm nguồn và in JSON đánh giá; cần Ollama hoạt động. Công cụ dọn schema riêng sau khi chạy và đối chiếu dữ liệu public trước/sau. Không sửa tài liệu thật để làm mẫu kiểm thử.

`hit_at_1` là tỷ lệ câu có nguồn đúng ở vị trí đầu; `hit_at_3` là tỷ lệ nguồn đúng trong ba kết quả đầu; `mrr_at_3` thưởng điểm cao hơn khi nguồn đúng đứng gần đầu. Chỉ 6 câu có nguồn được tính điểm; câu thứ 7 ngoài tài liệu dùng quan sát giới hạn. Đây là bộ mẫu nhỏ, chưa chứng minh chất lượng trên mọi PDF.

Trong terminal frontend:

```cmd
npm.cmd test
npm.cmd run build
```

`test` kiểm tra logic tự động. `build` kiểm tra mã frontend có thể đóng gói; không khởi động website. Minh chứng thực tế được lưu riêng tại [evidence/week6](evidence/week6/README.md), không ghi đè các tuần trước.

## Lưu Git sau khi bạn kiểm tra xong

Tại thư mục gốc:

```cmd
git status
git diff --stat
git add backend frontend docs README.md
git diff --cached --stat
git commit -m "feat: add workspace-scoped retrieval for week 6"
git push origin main
```

`status` xem file thay đổi; `diff --stat` xem phạm vi. `add` chọn thay đổi cho lần lưu; `diff --cached` kiểm tra phần đã chọn. `commit` tạo mốc trên máy; `push` gửi commit lên GitHub. Chỉ push `main` khi đó đúng là nhánh đang dùng. Không dùng force-push hoặc sửa lịch sử. Chưa cần gắn tag week-06 trước khi nghiệm thu.
