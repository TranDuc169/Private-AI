# Minh chứng tuần 5 — 05/10/2026

Code được phát triển tiếp từ commit 45601dc. Không sửa minh chứng tuần 2–4 hoặc các tag cũ. Chưa tạo tag week-05 và chưa push thay đổi tuần 5.

## Cập nhật: đã sửa lỗi test và nghiệm thu PostgreSQL thật

Người dùng đã cập nhật PostgreSQL với pgvector 0.8.7 và migration 0003_document_vectors. Log người dùng phát hiện hai lỗi trong harness kiểm thử: thư mục pytest-of-Admin bị từ chối quyền và search_path có public khiến kiểm tra tồn tại bảng/version table nhìn sang schema ứng dụng.

Đã sửa: conftest.py cấp thư mục tạm duy nhất cho mỗi lần chạy và tự dọn; fixture/smoke tạo bảng với checkfirst=False trong schema UUID mới rồi xác minh đủ bảng tại chính schema đó; migration test chỉ định rõ schema của alembic_version. Không sửa migration đã áp dụng hoặc cơ chế lưu dữ liệu production.

- backend-tests-temp-fix.txt: 28 pass, 3 skip PostgreSQL; chạy không cần --basetemp thủ công.
- postgres-tests-isolation-fix-02.txt: 28 pass trên PostgreSQL/pgvector, bao gồm migration giữ tài liệu/văn bản tuần 4, vector 1.024 chiều, cosine và cascade.
- smoke-pgvector-real-02.txt: BGE-M3 thật tạo 2 vector 1.024 chiều, lưu kiểu vector thật và xóa sạch tài liệu thử; PASS.
- public-isolation-audit.txt: so sánh hash toàn bộ nội dung của 7 bảng ứng dụng và alembic_version trước/sau từng lệnh; không thay đổi.
- test-data-repair.txt: trước khi sửa, test cũ đã để lại 2 tài khoản thử, 2 workspace thử, 2 metadata tài liệu giả và 1 trang giả trong public. Đã xác minh chính xác ID, tên, nội dung và dấu hiệu credential của test; sao lưu vào backups/ (ignored, không lên Git), chỉ xóa các bản ghi này. Tất cả bản ghi khác được đối chiếu nguyên vẹn trước/sau dọn.

Các file -01 là lần xác minh đầu; -02 là lần chạy kèm kiểm tra public không thay đổi. Minh chứng trước sửa bên dưới được giữ làm lịch sử; giới hạn chưa kiểm chứng PostgreSQL dưới đây đã được giải quyết. Chưa tạo tag/chưa push. Ảnh UI cũ vẫn là lần chạy SQLite, không diễn giải lại thành ảnh PostgreSQL.

## Lần kiểm tra ban đầu

| Hạng mục | Kết quả và file |
|---|---|
| Backend SQLite/mock | backend-tests.txt: 28 pass, 3 skip yêu cầu PostgreSQL. Gồm lỗi Ollama sau một lô, DB commit lỗi không lưu nửa bộ vector, retry không trùng, metadata trang/offset/Unicode, chuẩn hóa/kiểm tra vector, quyền khác owner, lượt xử lý quá hạn và chống lượt cũ ghi đè, xóa cascade và khôi phục file nếu DB lỗi. |
| Frontend | frontend-tests.txt: 9 pass; trạng thái đọc chữ không bị báo nhầm thành ready để tìm kiếm. |
| Build | frontend-build.txt: Vite build thành công với configLoader runner. |
| SQL migration | migration-offline.sql: Alembic sinh được SQL từ 0002 đến 0003. Đây là kiểm tra biên dịch migration, KHÔNG phải đã chạy trên PostgreSQL. |
| BGE-M3 thật + UI | browser-live-bge.txt: Edge + FastAPI + Ollama thật; PDF thử 2 trang tạo 2 vector 1.024 chiều, upload/process/index mất 10,531 giây. Dùng database SQLite tạm, KHÔNG phải pgvector. Chi tiết đoạn/trang hoạt động; hủy xóa giữ tài liệu, xác nhận xóa dọn danh sách và chi tiết. Không lỗi JS hoặc tràn ngang 390 px. |

Ảnh 01-chat-indexed.png, 02-chunk-details.png, 03-mobile-details.png được chụp từ lần chạy trên. Đã xem trực tiếp ảnh chi tiết desktop/mobile. Dòng health cũ trên UI nói PostgreSQL nhưng server kiểm thử dùng SQLite thay thế; ảnh này chỉ chứng minh luồng UI/BGE, không chứng minh kết nối pgvector.

Môi trường: Python 3.12 từ .venv-week3 ngoài repo; Node/Vite hiện có; model bge-m3:latest trên Ollama local. PDF thử sinh bằng code, không dùng tài liệu riêng của người dùng. Không thay đổi backend/.venv của người dùng.

## Giới hạn ở lần kiểm tra ban đầu — đã giải quyết ở cập nhật trên

PostgreSQL local đang ở migration 0002_pdf_documents, chưa có extension vector trong pg_available_extensions. Docker CLI đã cài bị Windows từ chối truy cập; thử CLI độc lập từ download.docker.com cũng bị từ chối truy cập Docker engine qua named pipe. Không đổi quyền máy, không thay volume hoặc thực hiện migration trên database người dùng.

Hai lệnh test_postgres.py và smoke_week5.py đã được thử, đều dừng có chủ đích ở kiểm tra thiếu extension. Không ghi là pass. Ba test PostgreSQL bị skip trong lần pytest SQLite: khóa process, migration giữ dữ liệu/đối chiếu schema và kiểu vector/cosine thật.

Sau khi người dùng cập nhật Docker image, cài requirements và chạy Alembic theo [WEEK5](../../WEEK5.md), cần chạy:

```cmd
.venv\Scripts\python.exe check_db.py
.venv\Scripts\python.exe test_postgres.py
.venv\Scripts\python.exe smoke_week5.py
.venv\Scripts\python.exe -m alembic check
```

Lưu kết quả mới bằng tên mới tại thư mục này. Chỉ chốt tuần 5 khi pgvector thật, migration và UI trên backend PostgreSQL đều đạt. Chưa có RAG/tìm kiếm/Qwen trong lần triển khai này.
