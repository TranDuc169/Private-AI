# Private AI Knowledge Platform — Tuần 2

Bộ khung React → FastAPI → PostgreSQL cho Đức và Khánh. Đây là mã khởi đầu mới: repository `https://github.com/TranDuc169/Private-AI` hiển thị **This repository is empty** khi kiểm tra ngày 02/10/2026. Chưa có source HTML/CSS/JavaScript để chuyển đổi; bố cục và màu giao diện tham chiếu ảnh chat trong báo cáo tuần 1.

**Trạng thái cập nhật 03/10/2026:** người dùng đã chạy thành công React → FastAPI → PostgreSQL, báo kiểm thử/build đạt và push GitHub thành công. Kiểm tra trực tiếp repository local xác nhận commit `fcfbca1`, `main` khớp bản ghi `origin/main`, và 4 test frontend chạy lại đạt. Chưa xác minh lại GitHub trực tuyến hoặc chạy lại đầy đủ backend/build trong môi trường công cụ do giới hạn quyền. Xem [VALIDATION](docs/VALIDATION.md). Còn thử riêng BGE-M3/Qwen3, lưu minh chứng đầy đủ và bàn giao cho Khánh để chốt tuần 2.

## Đã có trong bộ mã

- React + Vite + Tailwind, sidebar, routing Chat/Tài liệu/Lịch sử, trạng thái chưa chọn workspace.
- Một ô chat chung, chưa kích hoạt gửi; không có bộ chọn tác vụ hay câu trả lời AI giả.
- API client gọi `GET /health`: loading, thành công, DB lỗi, mạng lỗi, timeout và thử lại.
- FastAPI truy vấn PostgreSQL bằng `SELECT 1`; DB lỗi trả HTTP 503.
- SQLAlchemy 2, cấu hình `.env`, session factory và Alembic migration đầu tiên.
- Năm bảng nền tảng; documents và conversations gắn workspace, messages gắn conversation.

Đăng nhập/JWT, CRUD workspace, upload/parse PDF, pgvector, BGE-M3, Qwen3, retrieval, citation, AI tasks và API lịch sử **chưa triển khai**. Có bảng trong DB không có nghĩa là đã có chức năng. Quyền sở hữu và cách ly truy cập cần triển khai, kiểm thử từ tuần 3. Việc chạy thử model ghi trong PDF chưa thực hiện trong gói này.

## 1. Chuẩn bị

Cài Node.js 22 LTS (từ 22.12), Python 3.12, Docker Desktop với Docker Compose. Git cần khi đưa code lên GitHub. Sau khi cài, mở lại PowerShell rồi kiểm tra:

```powershell
node --version
npm.cmd --version
py -3.12 --version
docker compose version
git --version
```

Nguồn cài chính thức: [Node.js](https://nodejs.org/en/download), [Python](https://www.python.org/downloads/windows/), [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/), [Git](https://git-scm.com/downloads/win).

Mở PowerShell tại thư mục chứa README này. Ví dụ vị trí bàn giao:

```powershell
cd 'C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2'
```

Các lệnh sao chép `.env` dưới đây chỉ chạy lần đầu; không ghi đè nếu bạn đã cấu hình riêng. Mật khẩu mẫu chỉ dành cho DB local. Nếu đổi tài khoản, mật khẩu hoặc cổng ở `.env` gốc thì cập nhật `DATABASE_URL` tương ứng trong `backend/.env`; ký tự đặc biệt trong URL phải được URL-encode. Không đặt bí mật trong biến `VITE_*` vì chúng xuất hiện ở trình duyệt.

## 2. Khởi động PostgreSQL

Ở thư mục gốc:

```powershell
Copy-Item .env.example .env
docker compose up -d --wait db
docker compose ps
```

Kỳ vọng service `db` healthy. Dữ liệu lưu trong Docker volume. Gói này dùng PostgreSQL 16 thường; extension pgvector và bảng chunks sẽ thêm bằng migration ở giai đoạn embedding.

## 3. Khởi động backend — Đức

Mở terminal thứ hai từ thư mục gốc:

```powershell
cd backend
Copy-Item .env.example .env
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe check_db.py
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Không cần kích hoạt virtualenv hoặc đổi PowerShell execution policy. `check_db.py` phải in `SELECT 1: 1`, migration `0001_initial`, đủ 5 bảng và dòng PASS. Migration tạo cấu trúc bảng, không tạo tài khoản hoặc dữ liệu mẫu. Không dùng `create_all()` khi khởi động API.

Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). API: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

## 4. Khởi động frontend — Khánh

Mở terminal thứ ba từ thư mục gốc:

```powershell
cd frontend
Copy-Item .env.example .env
npm.cmd install
npm.cmd run dev
```

Mở [http://127.0.0.1:5173](http://127.0.0.1:5173). Giao diện tự gọi `/health`; khi DB hoạt động, dòng trạng thái ghi **Đã kết nối FastAPI và truy vấn PostgreSQL thành công**. Chuyển Chat/Tài liệu/Lịch sử để kiểm tra routing. Ô chat bị khóa có chủ đích vì chưa có API RAG.

Đã có `frontend/package-lock.json`; dùng `npm.cmd ci` cho các lần cài sau. `package.json` đã cho phép script cài đặt của `esbuild@0.25.12`. Python hiện dùng khoảng phiên bản dependency; chưa có lockfile Python, nhóm cần ghi phiên bản thực tế khi thu minh chứng.

## 5. Kiểm tra và nghiệm thu

Tại thư mục gốc, terminal khác với các server đang chạy:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Kỳ vọng HTTP 200, `status=ok`, `database=up`. DevTools → Network phải thấy request đến cổng 8000, không phải dữ liệu mẫu từ frontend. `/health` chỉ chứng minh API truy vấn được DB; cần `check_db.py` để xác minh migration.

Kiểm tra backend tại `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe check_db.py
```

`pytest` kiểm tra contract, lỗi DB và CORS bằng mock; hai lệnh sau kiểm tra PostgreSQL thật và sự khớp schema/model. Không dùng kết quả mock thay cho minh chứng DB thật.

Kiểm tra frontend tại `frontend/`:

```powershell
npm.cmd test
npm.cmd run build
```

Thử bản build: dừng Vite dev bằng Ctrl+C rồi `npm.cmd run preview`; vẫn dùng cổng 5173 đã khai báo CORS. Vite preview chỉ dùng kiểm tra local.

Thử tình huống lỗi tại thư mục gốc:

```powershell
docker compose stop db
```

Nhấn **Kiểm tra lại**: UI phải báo FastAPI chạy nhưng PostgreSQL chưa kết nối được; `/health` trả 503. Sau đó phục hồi:

```powershell
docker compose start db
```

Chờ DB sẵn sàng, nhấn kiểm tra lại: trạng thái thành công. Dừng backend bằng Ctrl+C rồi thử lại: UI báo lỗi gọi API. Khởi động lại backend bằng lệnh ở bước 3. Chụp ba trạng thái làm minh chứng; không tự ghi số liệu hoặc đánh dấu PASS khi chưa chạy.

## 6. Giải thích ngắn

React hiển thị giao diện; `src/api.js` tập trung lệnh HTTP để sau này thêm API dễ hơn. FastAPI nhận request rồi dùng engine SQLAlchemy kết nối PostgreSQL. Model mô tả bảng; Alembic ghi lại từng thay đổi bảng để hai máy có cùng schema. `.env` giữ cấu hình riêng của mỗi máy, `.env.example` là mẫu chia sẻ.

Tài liệu và hội thoại đều có `workspace_id` bắt buộc. Message kế thừa phạm vi workspace thông qua conversation. Đây mới là nền tảng dữ liệu: tuần 3 cần xác thực user, kiểm tra ownership và lọc query; frontend không được tự coi workspace ID là quyền truy cập.

Xem [hiện trạng](docs/STATUS.md), [API contract](docs/API.md), [schema và ERD](docs/SCHEMA.md), [biên bản kiểm tra](docs/VALIDATION.md).

## 7. Git và bàn giao cho Khánh

Người dùng đã xác nhận push lần đầu. Commit local kiểm tra ngày 03/10/2026 là `fcfbca1`. Các cập nhật tài liệu sau đó chưa commit/push.

Khánh mở CMD tại thư mục muốn lưu dự án:

```cmd
git clone https://github.com/TranDuc169/Private-AI.git
cd Private-AI
```

Tiếp tục cấu hình/chạy theo các bước trên (các khối PowerShell cần dùng PowerShell). Chỉ kiểm tra frontend thì thực hiện bước 4; chưa bật backend sẽ có thông báo không gọi được API. Để kiểm tra tích hợp, cần chạy cả DB/backend/frontend. Ghi lại commit, phiên bản công cụ và kết quả chạy. Chưa có xác nhận Khánh đã thực hiện.

### Tham khảo: khởi tạo lần đầu (đã thực hiện)

Sau khi cài Git, đứng ở thư mục gốc, xem lại file trước khi commit:

```powershell
git init -b main
git remote add origin https://github.com/TranDuc169/Private-AI.git
git add .
git status
git diff --cached --stat
git commit -m "Add week 2 React FastAPI PostgreSQL skeleton"
git push -u origin main
```

Đăng nhập GitHub bằng công cụ Git trên máy khi được yêu cầu; không đặt token trong code. Nếu repository đã có commit mới thì clone và ghép thay đổi thay vì force-push. Gói này không chứa `.env` thật hoặc node_modules.

## Xử lý lỗi thường gặp

| Triệu chứng | Kiểm tra |
|---|---|
| Không tìm thấy `node`, `py`, `docker` | Cài công cụ, mở lại terminal; bật Docker Desktop |
| DB không healthy | `docker compose logs db`; kiểm tra cổng 5432 đã bị chiếm chưa |
| HTTP 503 | Đối chiếu `backend/.env` với `.env` gốc và trạng thái DB |
| Đổi mật khẩu `.env` nhưng DB vẫn từ chối | PostgreSQL volume đã khởi tạo giữ mật khẩu cũ; cập nhật credential trong DB hoặc dùng cấu hình cũ, không xóa volume tùy tiện |
| CORS hoặc gọi nhầm API | Kiểm tra `VITE_API_BASE_URL`, `CORS_ORIGINS`; khởi động lại server sau khi sửa `.env` |
| Cổng 5173 bị chiếm | Dừng tiến trình đang dùng cổng; Vite dùng strictPort để không tự chuyển cổng lệch CORS |
| Thiếu bảng | Chạy `alembic upgrade head` trong đúng backend và DB |

Tham khảo triển khai: [Vite](https://vite.dev/guide/), [Tailwind với Vite](https://tailwindcss.com/docs/installation/using-vite), [Alembic autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html).
