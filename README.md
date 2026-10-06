# Private AI Knowledge Platform — Tuần 6

**Tuần 6:** đã có tìm đoạn theo câu hỏi trong workspace bằng BGE-M3/pgvector và hiển thị nguồn trong Chat chung. Chưa sinh câu trả lời AI. Xem [hướng dẫn chạy và giải thích từng lệnh](docs/WEEK6.md), [minh chứng](docs/evidence/week6/README.md). Không cần migration mới sau tuần 5.

**Mốc tuần 5 — [hướng dẫn tuần 5](docs/WEEK5.md)**: chia đoạn theo trang, BGE-M3, lưu pgvector, trạng thái xử lý, chi tiết đoạn và xóa tài liệu. Cần image PostgreSQL có pgvector và migration `0003_document_vectors`. [Minh chứng và giới hạn kiểm chứng](docs/evidence/week5/README.md). Các hướng dẫn thiết lập cũ ở dưới giữ bối cảnh lịch sử.

Bộ khung React → FastAPI → PostgreSQL cho Đức và Khánh. Đây là mã khởi đầu mới: repository `https://github.com/TranDuc169/Private-AI` hiển thị **This repository is empty** khi kiểm tra ngày 02/10/2026. Chưa có source HTML/CSS/JavaScript để chuyển đổi; bố cục và màu giao diện tham chiếu ảnh chat trong báo cáo tuần 1.

**Trạng thái cập nhật 04/10/2026:** người dùng đã chạy thành công React → FastAPI → PostgreSQL, báo kiểm thử/build đạt và push GitHub thành công. Kiểm tra trực tiếp repository local xác nhận commit `fcfbca1`, `main` khớp bản ghi `origin/main`, và 4 test frontend chạy lại đạt. Chưa xác minh lại GitHub trực tuyến hoặc chạy lại đầy đủ backend/build trong môi trường công cụ do giới hạn quyền. Xem [VALIDATION](docs/VALIDATION.md). Đã thử riêng Qwen3 4B Instruct và BGE-M3 thành công theo output người dùng; đã lưu JSON, thời gian và hướng dẫn chạy lại trong [MODEL_SMOKE_TEST](docs/MODEL_SMOKE_TEST.md). Đã có log kiểm thử/build/migration và ảnh trong docs/evidence/week2 tại commit 3007e3a. Còn chờ Khánh xác nhận chạy thử.

## Đã có trong bộ mã

- React + Vite + Tailwind, sidebar, routing Chat/Tài liệu/Lịch sử, trạng thái chưa chọn workspace.
- Một ô chat chung, gửi câu hỏi để tìm đoạn tài liệu; không có bộ chọn tác vụ hay câu trả lời AI giả.
- API client gọi `GET /health`: loading, thành công, DB lỗi, mạng lỗi, timeout và thử lại.
- FastAPI truy vấn PostgreSQL bằng `SELECT 1`; DB lỗi trả HTTP 503.
- SQLAlchemy 2, cấu hình `.env`, session factory và Alembic migration đầu tiên.
- Năm bảng nền tảng; documents và conversations gắn workspace, messages gắn conversation.

Tuần 3 có đăng ký/đăng nhập JWT, workspace CRUD, danh sách tài liệu/hội thoại theo workspace và kiểm tra quyền ở backend. Tuần 4 có upload và đọc PDF. Tuần 5 đã viết phần BGE-M3/pgvector và quản lý các đoạn; trạng thái kiểm chứng thực tế nằm trong minh chứng tuần 5. Tuần 6 đã có truy xuất nguồn theo câu hỏi, tên PDF và số trang. Sinh câu trả lời RAG bằng LLM và mở nội dung hội thoại chưa triển khai.

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
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up -d --wait db
docker compose ps
```

Kỳ vọng service `db` healthy. Dữ liệu lưu trong Docker volume. Tuần 5 dùng PostgreSQL 16 có pgvector; khi nâng cấp từ tuần 4, làm theo docs/WEEK5.md trước.

## 3. Khởi động backend — Đức

Mở terminal thứ hai từ thư mục gốc:

```powershell
cd backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe setup_auth.py
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe check_db.py
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Không cần kích hoạt virtualenv hoặc đổi PowerShell execution policy. `check_db.py` phải in `SELECT 1: 1`, migration `0003_document_vectors`, đủ 7 bảng và phiên bản pgvector và dòng PASS. Migration tạo cấu trúc bảng, không tạo tài khoản hoặc dữ liệu mẫu. Không dùng `create_all()` khi khởi động API.

Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). API: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

## 4. Khởi động frontend — Khánh

Mở terminal thứ ba từ thư mục gốc:

```powershell
cd frontend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
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

Tài liệu và hội thoại đều có `workspace_id` bắt buộc. Message kế thừa phạm vi workspace thông qua conversation. Backend tuần 3 xác thực user, kiểm tra ownership và lọc query trước khi trả danh sách; frontend không được tự coi workspace ID là quyền truy cập.

Xem [hiện trạng](docs/STATUS.md), [API contract](docs/API.md), [schema và ERD](docs/SCHEMA.md), [biên bản kiểm tra](docs/VALIDATION.md).

## 7. Git và bàn giao cho Khánh

Người dùng đã xác nhận push lần đầu. Commit local kiểm tra ngày 03/10/2026 là `fcfbca1`. Commit ec4fcc7 đã lưu lần cập nhật tài liệu trước. Dùng git log -1 --oneline để xem commit hiện tại; dùng git status -sb để kiểm tra trạng thái đồng bộ.

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

## Minh chứng theo tuần

Xem [quy ước thư mục và tag](docs/evidence/README.md). Giữ nguyên tag week-02; minh chứng tuần 3 lưu riêng trong docs/evidence/week3, không ghi đè tuần 2.
