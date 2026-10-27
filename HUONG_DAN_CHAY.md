# Mở lại dự án và chạy — dành cho người mới

Tài liệu dành cho máy Windows của bạn đã cài môi trường và chạy dự án trước đây. Không cần cài lại Python, Node, Docker hoặc tải model mỗi lần mở máy. Các lệnh dưới đây dùng **CMD (Command Prompt)**, không dùng PowerShell.

## 1. Mở đúng thư mục trong VS Code

Nhấn Windows + E để mở File Explorer. Dán đường dẫn sau vào thanh địa chỉ rồi Enter:

```text
C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2
```

Đây là thư mục gốc, chứa `backend`, `frontend`, `compose.yaml` và file hướng dẫn này. Tên thư mục vẫn là week2 nhưng code đã phát triển đến tuần 9.

Mở VS Code → File → Open Folder → chọn thư mục trên. Nhấn Ctrl+P rồi gõ `HUONG_DAN_CHAY.md` để tìm nhanh file này. Nhấn Ctrl+Shift+V để xem bản trình bày dễ đọc.

Trong VS Code, chọn Terminal → New Terminal. Nhấn mũi tên cạnh dấu + của khu vực Terminal → chọn **Command Prompt**. Nếu terminal đang ghi `PS ...>`, đó là PowerShell; hãy mở Command Prompt mới. CMD thường có dòng chờ dạng `C:\Users\Admin>`. Chỉ chép các lệnh trong khung, không chép dòng chờ đó.

Bạn sẽ dùng ba terminal: **1 — dịch vụ/kiểm tra**, **2 — backend**, **3 — frontend**. Mỗi terminal có thư mục hiện tại riêng. Các khung lệnh bên dưới dùng đường dẫn đầy đủ để tránh vào nhầm thư mục.

## 2. Bật database và AI

Mở **Docker Desktop** từ Start, đợi engine khởi động. Mở **Ollama** từ Start; ứng dụng có thể chạy ở khay hệ thống mà không hiện cửa sổ lớn.

Trong terminal 1, chạy từng dòng:

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2"
docker compose up -d --wait db
ollama list
```

| Lệnh | Tác dụng |
|---|---|
| `cd /d "..."` | Chuyển tới thư mục dự án; `/d` cho phép đổi cả ổ đĩa. Dấu ngoặc kép bảo vệ đường dẫn có khoảng trắng. |
| `docker compose up -d --wait db` | Đọc `compose.yaml`, bật dịch vụ PostgreSQL tên `db`. `-d` chạy nền; `--wait` đợi database sẵn sàng. Dữ liệu cũ nằm trong volume nên không bị xóa khi khởi động lại. |
| `ollama list` | Kiểm tra Ollama và liệt kê model đã tải. Chưa tạo câu trả lời ở bước này. |

Database cần báo Healthy hoặc running/healthy. Danh sách model cần có `bge-m3:latest` và `qwen3:4b-instruct-2507-q4_K_M`.

**Chỉ nếu thiếu model**, tải model còn thiếu:

```cmd
ollama pull bge-m3
ollama pull qwen3:4b-instruct-2507-q4_K_M
```

`pull` tải dữ liệu model từ mạng và có thể mất nhiều phút. Không cần vào cuộc trò chuyện bằng `ollama run`: backend sẽ tự gọi model.

## 3. Bật backend — terminal 2

Mở terminal CMD mới, chạy:

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\backend"
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Giải thích lệnh dài:

- `.venv\Scripts\python.exe`: dùng Python và thư viện riêng của backend; không cần chạy lệnh activate trước.
- `-m uvicorn`: dùng Python chạy chương trình Uvicorn, chương trình phục vụ API FastAPI.
- `app.main:create_app`: tìm hàm `create_app` trong file `backend/app/main.py`.
- `--factory`: gọi hàm đó để tạo ứng dụng.
- `--reload`: tự nạp lại backend khi bạn lưu thay đổi code, tiện lúc phát triển.
- `--host 127.0.0.1`: chỉ phục vụ trên máy này. `--port 8000`: API dùng cổng 8000.

Nếu vừa cập nhật code tuần 8/9, chạy migration theo mục 10 trước khi bật backend. Chờ dòng `Application startup complete`. **Giữ terminal này mở**. Không xuất hiện lại dòng để nhập lệnh là bình thường: server đang chạy và chờ yêu cầu.

Mở trình duyệt: http://127.0.0.1:8000/health

Kết quả mong đợi:

```json
{"status":"ok","database":"up"}
```

Nghĩa là FastAPI truy vấn được PostgreSQL. Kết quả này chưa kiểm tra BGE-M3, Qwen hay chất lượng trả lời. http://127.0.0.1:8000/docs là trang xem/thử API; giao diện người dùng nằm ở bước sau.

## 4. Bật frontend — terminal 3

Mở thêm terminal CMD mới, chạy:

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\frontend"
npm.cmd run dev -- --port 5173 --strictPort
```

`npm.cmd run dev` chạy script `dev` trong `frontend/package.json`, tức Vite phục vụ giao diện React. Dấu `--` chuyển các tham số phía sau cho Vite. `--port 5173` chọn cổng giao diện; `--strictPort` yêu cầu báo lỗi nếu cổng bận thay vì âm thầm chuyển cổng, giúp tránh lỗi CORS do sai cổng.

Khi có dòng `Local: http://127.0.0.1:5173/`, mở địa chỉ đó. **Giữ terminal 3 mở**. Đây là trang bạn dùng để đăng nhập, chọn workspace, tải tài liệu và hỏi đáp.

Không cần `npm install` mỗi lần mở máy. Chỉ cài lại thư viện khi chưa có `node_modules` hoặc khi thay đổi dependency.

## 5. Dùng thử trên web

1. Đăng nhập tài khoản đã tạo. Nếu chưa có thì đăng ký. Khởi động lại trình duyệt/backend có thể cần đăng nhập lại; điều đó không có nghĩa tài khoản đã mất.
2. Chọn workspace chứa tài liệu của bạn.
3. Vào Tài liệu, kiểm tra PDF đã xử lý và index sẵn sàng. Upload thành công mới chỉ là nhận file; cần trích chữ và tạo vector để tìm kiếm được.
4. Vào Chat, hỏi: `LEFT JOIN khác INNER JOIN thế nào?` (workspace phải có tài liệu về JOIN).
5. Đợi câu trả lời rồi mở nguồn để đối chiếu tên PDF, số trang và đoạn trích.
6. Thử câu không có trong tài liệu như `Lịch thi môn CSDL của trường tôi ngày nào?`. Hệ thống cần thừa nhận thiếu căn cứ; nếu bịa thì ghi lại để sửa.

Qwen chạy trên máy nên có thể cần hàng chục giây hoặc lâu hơn. Nếu có timeout, đọc thông báo và thử câu ngắn hơn. Không bấm Gửi liên tục: bản demo chỉ xử lý một pipeline chat đồng thời trong mỗi process backend.

### Nếu chưa có bộ PDF demo CSDL

Giữ backend/frontend chạy. Dùng lại terminal 1:

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\backend"
.venv\Scripts\python.exe load_demo_course.py
```

Script hỏi email/mật khẩu tài khoản đã đăng ký trên web. Khi gõ mật khẩu, CMD không hiện ký tự là bình thường. Script đăng nhập qua API, tạo **workspace mới**, tải 5 PDF, trích chữ và tạo vector. Chờ đủ 5 dòng `READY`, sau đó tải lại web, đăng nhập nếu cần và chọn workspace `CSDL - Demo ...`.

**Chỉ cần nạp khi cần bộ demo mới.** Mỗi lần chạy script tạo thêm một workspace. Nếu lỗi giữa chừng, dữ liệu đã tạo được giữ lại; kiểm tra và xử lý tiếp trên web để tránh tạo nhiều bản trùng.

## 6. Hiểu ứng dụng đang hoạt động thế nào

| Thành phần | Nơi chạy | Vai trò |
|---|---|---|
| React + Vite | Cổng 5173 | Vẽ giao diện, nhận thao tác của bạn, gửi yêu cầu đến backend. |
| FastAPI | Cổng 8000 | Kiểm tra đăng nhập/quyền workspace, điều phối xử lý PDF, tìm nguồn và gọi AI. |
| PostgreSQL + pgvector | Docker, mặc định cổng 5432 | Lưu tài khoản, workspace, thông tin tài liệu, đoạn chữ và vector phục vụ tìm kiếm. |
| Ollama | Mặc định cổng 11434 | Chạy BGE-M3 và Qwen tại máy. |

**Khi thêm tài liệu:** PDF → backend lưu file → trích chữ từng trang → chia thành các đoạn nhỏ → BGE-M3 biến từng đoạn thành vector (dãy số biểu diễn nội dung) → PostgreSQL lưu đoạn, vector và thông tin trang. File PDF nằm trong vùng lưu trữ backend; database lưu metadata và dữ liệu đã xử lý.

**Khi hỏi:** React gửi câu hỏi và token đăng nhập → FastAPI kiểm tra quyền workspace → BGE-M3 biến câu hỏi thành vector → pgvector chọn tối đa 5 đoạn gần nghĩa trong workspace được phép → Qwen đọc các đoạn và viết câu trả lời → backend kiểm tra định dạng/mã nguồn → React hiện câu trả lời và nguồn.

Đó là RAG: tìm tài liệu trước, đưa nội dung tìm được cho model trả lời. Không phải huấn luyện lại Qwen mỗi khi upload PDF. BGE-M3 tìm nội dung; Qwen viết câu trả lời. Có nguồn trích dẫn vẫn cần đối chiếu, vì model có thể diễn đạt sai hoặc quá rộng.

Ở phiên bản hiện tại, mỗi câu hỏi được xử lý độc lập; các lượt trước không gửi làm ngữ cảnh. Các câu hỏi và câu trả lời hoàn tất được lưu lâu dài theo workspace; vào Lịch sử để mở lại. Reload cần đăng nhập lại vì token chỉ giữ trong bộ nhớ, nhưng hội thoại vẫn còn trong database. Ứng dụng giải thích SQL dưới dạng văn bản, không thực thi SQL mà người dùng nhập.

## 7. Tắt đúng cách và mở lại hôm sau

- Terminal frontend: nhấn Ctrl+C (nếu CMD hỏi `Terminate batch job`, gõ Y rồi Enter).
- Terminal backend: nhấn Ctrl+C, chờ server dừng.
- Muốn dừng database, ở terminal 1 chạy:

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2"
docker compose stop db
```

`stop db` dừng dịch vụ và giữ dữ liệu. Không dùng `docker compose down -v` để tắt hằng ngày: `-v` có thể xóa volume database của dự án.

Hôm sau chỉ cần: **mở Docker/Ollama → bước 2 → bước 3 → bước 4 → đăng nhập web**. Không nạp lại demo, không tạo lại `.env` hoặc chạy lại `git init`. Git/GitHub lưu và chia sẻ mã nguồn; push không phải bước khởi động ứng dụng.

## 8. Lỗi thường gặp

| Hiện tượng | Kiểm tra và xử lý |
|---|---|
| Docker báo pipe/engine không tồn tại | Mở Docker Desktop và đợi engine chạy rồi thử lại bước 2. |
| `/health` báo database down | Chạy `docker compose ps` tại thư mục gốc; kiểm tra db healthy. Nếu vẫn lỗi, kiểm tra cấu hình backend/database, không xóa dữ liệu để thử. |
| Trình duyệt không vào được `/health` | Xem terminal backend còn chạy không; đọc lỗi cuối trong terminal. |
| Backend báo cổng 8000 bận | Có thể server cũ còn chạy. Thử `/health`; nếu cần khởi động lại, Ctrl+C ở terminal server cũ trước. |
| Vite báo cổng 5173 bận | Kiểm tra giao diện cũ tại 5173 hoặc dừng terminal frontend cũ. Không vội đổi cổng vì backend đang cho phép origin 5173. |
| Giao diện báo không gọi được API | Kiểm tra `/health`, dùng địa chỉ frontend 127.0.0.1:5173, kiểm tra `frontend/.env` nếu có cấu hình API khác. |
| Không gọi được model | Mở Ollama, chạy `ollama list`, kiểm tra đúng hai tên model ở bước 2. |
| 401/hết phiên | Đăng nhập lại; token mặc định có hạn 30 phút. |
| Chat báo không có tài liệu | Chọn đúng workspace và kiểm tra tài liệu đã index sẵn sàng. |
| Không tìm thấy Python hoặc Vite | Kiểm tra đúng thư mục và file `.venv\Scripts\python.exe`/`node_modules`. Đây là lỗi môi trường, không nên cài lại toàn bộ ngay. |
| Lỗi thiếu `.env`/database_url/jwt_secret | Kiểm tra file `backend/.env` và `.env` tại gốc còn tồn tại. Không gửi mật khẩu hay JWT secret lên GitHub hoặc ảnh lỗi công khai. |

## 9. Kiểm thử khi vừa sửa code (không cần chạy mỗi lần mở máy)

Ở terminal 1, khi database và Ollama đã bật:

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\backend"
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe test_postgres.py
```

Lệnh đầu kiểm tra logic, thường giả lập model; các bài cần PostgreSQL có thể bị skip. Lệnh thứ hai chạy các bài database trong schema thử nghiệm riêng, rồi dọn schema. `passed` là đạt, `failed` là lỗi cần đọc, `skipped` là chưa chạy — không được tính là đạt. Hai lệnh này chưa chứng minh chất lượng câu trả lời model thật.

Kiểm tra frontend:

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\frontend"
npm.cmd test
npm.cmd run build
```

`test` chạy kiểm thử API client; `build` kiểm tra việc đóng gói giao diện. Build đạt không có nghĩa model trả lời đúng.

Tuần 8 có migration mới để lưu lịch sử; xem mục 10. Sau khi nâng cấp thành công không cần chạy migration mỗi lần mở máy. Hướng dẫn đánh giá 20 câu với model/database thật và chi tiết code nằm trong [docs/WEEK7.md](docs/WEEK7.md); kết quả đã kiểm tra nằm trong [docs/evidence/week7/README.md](docs/evidence/week7/README.md).


## 10. Cập nhật database tuần 8/9 — làm một lần khi có migration mới

Giữ Docker đang chạy. Nếu backend đang chạy, Ctrl+C ở terminal backend trước. Chạy trong CMD:

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\backend"
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m alembic current
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

`alembic upgrade head` bổ sung các cột để lưu thứ tự tin nhắn và bản chụp nguồn, giữ các bản ghi cũ. `head` nghĩa là migration mới nhất. `alembic current` xem phiên bản database: cần hiện `0005_study_plans (head)`. Chỉ chạy tiếp server khi migration thành công. Chạy lại upgrade khi đã ở head không thêm cột lần nữa.

Bật frontend như mục 4. Gửi một câu hỏi, vào Lịch sử để mở lại; reload trang, đăng nhập và chọn đúng workspace rồi mở Lịch sử lần nữa. Thử nhập `Tóm tắt chủ đề transaction` trong cùng ô chat. Mở nguồn để xem bản trích đã lưu và đoạn nguồn hiện tại.

Tóm tắt hỗ trợ 5 chủ đề CSDL theo từ khóa, tối đa 8 đoạn trải trên các trang; giao diện nêu phạm vi và số tài liệu chưa sẵn sàng. Nhập yêu cầu chung như `Tóm tắt giúp tôi` sẽ được hỏi rõ chủ đề. Model chưa đọc các lượt trước, nên câu tiếp theo cần ghi đủ chủ đề, ví dụ `Tóm tắt transaction` thay vì chỉ `transaction`.

Chi tiết các thay đổi và bài thử tuần 8: [docs/WEEK8.md](docs/WEEK8.md).


## 11. Chạy thử roadmap và checklist tuần 9

Sau khi chạy migration ở mục 10 và bật backend/frontend, chọn workspace có đủ bộ PDF CSDL đã index. Nhập:

> Lập roadmap SQL JOIN; nền tảng: mới bắt đầu; 4 buổi; 45 phút/buổi.

Đọc thẻ bản nháp và nguồn từng bước → bấm Xác nhận kế hoạch này → đánh dấu một bước → reload, đăng nhập lại, chọn workspace và mở Lịch sử. Tiến độ phải còn. Nếu muốn thay thời gian/mục tiêu, gửi yêu cầu mới để tạo bản nháp khác.

Lệnh `alembic upgrade head` tự chạy migration còn thiếu của cả tuần 8 và tuần 9 theo thứ tự. Tuần 9 tạo bảng kế hoạch và bảng checklist, không xóa tài khoản/tài liệu cũ. Không cần cài thêm thư viện hay tải model khác.

Giải thích file, thuật toán, lệnh kiểm thử và giới hạn: [docs/WEEK9.md](docs/WEEK9.md).
