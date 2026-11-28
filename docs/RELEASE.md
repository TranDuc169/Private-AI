# Bàn giao backend tuần 12

Gói này chứa FastAPI, migration, học liệu demo, bộ đánh giá và kết quả tuần 12.
Frontend Khánh ở repository chính; không kèm trong ZIP backend. Các lệnh bên dưới
chạy tại thư mục gốc sau khi giải nén. Không chuyển `.env`, database hoặc PDF riêng
của tài khoản vào Git/ZIP. Migration hiện tại: `0006_quizzes`, không có migration mới.

## 1. Chạy native trên Windows

Yêu cầu: Python 3.12, Docker Desktop đang chạy PostgreSQL/pgvector, Ollama.
Đây là cách chạy đã được dùng để kiểm thử tuần 12. `requirements.lock.txt` cố định
các phiên bản của môi trường đã thử; chưa khẳng định kiểm chứng Linux container.

Trên máy mới, từ thư mục gốc:

```powershell
Copy-Item .env.example .env
# Mở .env, đặt POSTGRES_PASSWORD; không dùng mật khẩu mẫu khi chia sẻ máy.
docker compose up -d --wait db
cd backend
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
Copy-Item .env.example .env
```

Sửa `backend/.env`: DATABASE_URL phải khớp user/password/port/database trong `.env`
gốc. Nếu mật khẩu có ký tự đặc biệt, URL-encode phần mật khẩu. Có thể dùng chuỗi
hex ngẫu nhiên để tránh lỗi URL. Sau đó tạo JWT secret và nâng schema:

```powershell
.venv\Scripts\python.exe setup_auth.py
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe check_db.py
ollama pull bge-m3:latest
ollama pull qwen3:4b-instruct-2507-q4_K_M
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8001 --workers 1
```

Nếu đã có `.env` và dữ liệu thì giữ nguyên; không chạy lại lệnh Copy-Item đè file.
Chỉ chạy migration sau khi đã sao lưu. `check_db.py` đọc schema, không sửa dữ liệu.
`/health` chỉ kiểm tra PostgreSQL, không chứng minh model sẵn sàng.
Kiểm tra Ollama bằng `ollama list`, bảo đảm tên hai model đúng như trên.
Không chạy nhiều worker: giới hạn pipeline hiện tại chỉ có hiệu lực trong một process.

Frontend: đặt `VITE_API_BASE_URL=http://127.0.0.1:8001`; CORS_ORIGINS trong backend
phải chứa origin thực tế, ví dụ `["http://127.0.0.1:5174","http://localhost:5174"]`.
Không đặt secret hoặc URL kết nối database vào frontend.

## 2. Kiểm thử và đánh giá

Trong thư mục backend:

```powershell
.venv\Scripts\python.exe -m pip install -c requirements.lock.txt -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.venv\Scripts\python.exe test_postgres.py
```

Lệnh PostgreSQL dùng schema tạm, kiểm tra quyền, migration và nghiệp vụ; model được
giả lập trong các bài test. Không chạy trên database production hoặc đồng thời với
thao tác người dùng. Bộ đánh giá thật cũng dùng schema tạm và thư mục PDF tạm:

```powershell
.venv\Scripts\python.exe evaluate_rag.py --mode postgres --dataset ../docs/evaluation/final-v1.json --final-eval --limit 40 --output ../docs/evidence/week12/final-02.json
.venv\Scripts\python.exe summarize_evaluation.py ../docs/evidence/week12/final-02.json --dataset ../docs/evaluation/final-v1.json --output-dir ../docs/evidence/week12/final-02-review
```

`final-01.json` là lần đã chạy; không ghi đè. Chỉ chạy lại có chủ đích, giữ cả hai
lượt và nêu lý do. Bộ cuối đã dùng ngày 27/11/2026, không còn là bộ chưa quan sát
để tinh chỉnh prompt. File lock giữ nguyên trạng thái lúc đóng băng; lịch thực thi
ghi trong evidence. Không sửa hash/corpus/câu hỏi để làm đẹp kết quả.

`review.csv` chứa đủ 40 câu, câu trả lời và nguồn. Người rà chấm nội dung và nguồn
riêng theo 0 = sai/không hỗ trợ, 1 = một phần, 2 = đúng/đủ hỗ trợ; ghi tên và nhận xét.
Không thay ô trống bằng 0 trước khi đọc. HTTP/status/Top-K không phải điểm nội dung.
Trung vị/p95 đo cả retrieval và chat, tính trên các lần thử có thời gian kể cả lỗi;
p95 dùng nearest rank. Câu không chạy vẫn nằm trong mẫu số bộ đánh giá.

## 3. Cấu hình Docker release riêng

Đã kiểm tra cú pháp Compose. Chưa build/chạy image trong phiên này vì sandbox
không truy cập được Docker named pipe; không coi là container đã nghiệm thu.
Native PostgreSQL và model thật đã chạy, xem evidence. Docker release dùng project
`private-ai-release`, volume riêng, DB cổng 55432 và API 8002, không dùng volume cũ.

```powershell
Copy-Item .env.release.example .env.release
# Tạo HAI chuỗi khác nhau; điền RELEASE_DB_PASSWORD và RELEASE_JWT_SECRET:
py -3.12 -c "import secrets; print(secrets.token_hex(32))"
docker compose --env-file .env.release -f compose.release.yaml build backend
docker compose --env-file .env.release -f compose.release.yaml up -d --wait db
docker compose --env-file .env.release -f compose.release.yaml run --rm backend alembic upgrade head
docker compose --env-file .env.release -f compose.release.yaml up -d --wait backend
docker compose --env-file .env.release -f compose.release.yaml exec backend python check_db.py
```

Mở http://127.0.0.1:8002/health. Image chạy user không phải root, một worker và lưu
PDF trên volume riêng. Ollama ở máy host được truy cập qua `host.docker.internal`.
Cần kiểm tra host Ollama có nhận kết nối từ container trong cấu hình mạng thực tế;
nếu không, dùng cách native trên cùng máy. Không tự mở Ollama ra mạng công cộng.

## 4. Sao lưu và phục hồi

Dừng backend trước khi sao lưu để DB và file PDF cùng thời điểm. Với native, dừng
uvicorn bằng Ctrl+C, sao lưu thư mục `backend/storage`, giữ riêng cấu hình `.env`.
Dùng `pg_dump -Fc` của PostgreSQL 16 để sao lưu database; truyền mật khẩu qua cơ
chế xác thực của PostgreSQL, không đưa mật khẩu vào lịch sử lệnh.
Phục hồi thử vào database mới bằng `pg_restore`, cùng bản storage và cùng mã nguồn;
đổi DATABASE_URL/STORAGE_DIR sang bản phục hồi, chạy check_db, mở lại tài liệu và
hội thoại để xác nhận. Không phục hồi đè database đang dùng. Chưa diễn tập restore
trong tuần này nên không ghi thành phép thử đạt. Không dùng `docker compose down -v`
để tắt ứng dụng; lệnh đó xóa volume.

## 5. Tạo ZIP nguồn

```powershell
cd backend
.venv\Scripts\python.exe package_release.py --output ../../Private-AI-backend-week12.zip
```

ZIP chỉ lấy danh sách mã nguồn/học liệu/evidence đã định, kèm SHA256 từng file trong
RELEASE_MANIFEST.json. Không kèm `.env`, `.venv`, storage, database hay token.
ZIP là gói nguồn, không phải installer hoặc image Docker đã kiểm chứng.
