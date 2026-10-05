# Tuần 5 — chia đoạn và tạo vector

## Hiểu mục đích trước khi chạy lệnh

Tuần 4 đọc PDF thành chữ. Tuần 5 chuẩn bị dữ liệu để tuần sau tìm đoạn liên quan đến câu hỏi:

**PDF → văn bản từng trang → đoạn nhỏ (chunk) → BGE-M3 → vector → PostgreSQL/pgvector.**

- **Chunk** là một đoạn văn bản nhỏ. Ví dụ trang dài 2.500 ký tự tạo các đoạn `[0,1200)`, `[1000,2200)`, `[2000,2500)`. Mỗi cặp cạnh nhau chồng 200 ký tự để giữ ngữ cảnh. Đây là cách cắt theo ký tự, chưa phải bộ tách theo token hoặc ý nghĩa câu.
- **Embedding** biến nội dung một đoạn thành danh sách 1.024 số. BGE-M3 làm việc này; nó không viết câu trả lời. Các số được chuẩn hóa về vector độ dài 1 và kiểm tra đủ số chiều, không NaN/Infinity/zero trước khi lưu.
- **pgvector** bổ sung kiểu dữ liệu vector cho PostgreSQL. Cài thư viện Python `pgvector` chưa đủ: server PostgreSQL cũng cần extension `vector`.
- **Metadata** giúp biết đoạn đến từ đâu: document ID, thứ tự đoạn, số trang, vị trí ký tự, tên model và ngày tạo. Workspace/tên file được lấy qua tài liệu cha, tránh lưu lặp rồi lệch dữ liệu.
- **Sẵn sàng tìm kiếm** chỉ có nghĩa tài liệu đã lưu đủ vector. Tuần 5 chưa có API tìm kiếm, Qwen trả lời, citation, OCR hoặc lịch sử chat AI.

## Tôi đã thay đổi gì

| File | Thay đổi và lý do |
|---|---|
| compose.yaml | Dùng pgvector/pgvector:0.8.7-pg16-trixie, vẫn PostgreSQL major 16 và volume postgres_data cũ. |
| backend/alembic/versions/0003_document_vectors.py | Bật extension vector, thêm trạng thái index và bảng document_chunks. Không xóa tài khoản/PDF/văn bản tuần trước. |
| backend/app/models.py | Model bảng chunks: nội dung, trang, khoảng ký tự, vector(1024), model; document_id + chunk_index unique; xóa document thì cascade xóa chunks. |
| backend/app/embedding.py | Cắt từng trang thành đoạn 1.200 ký tự, overlap 200; không trộn trang; gọi /api/embed theo lô 8, truncate=false, kiểm tra và chuẩn hóa kết quả. |
| backend/app/indexing.py | API tạo vector, xem đoạn, xóa tài liệu. Công việc có mã riêng và thời hạn để tránh hai lượt xử lý ghi đè nhau. |
| backend/app/schemas.py | Trả thêm trạng thái index, lỗi, số đoạn, tên model và thời gian. API chi tiết đoạn không gửi 1.024 số lên UI. |
| backend/app/config.py, backend/.env.example | Thêm địa chỉ Ollama, model BGE-M3, timeout/lô/giới hạn đoạn. Có mặc định nên không chép đè .env. |
| backend/requirements.txt | Thêm pgvector và httpx dùng cho backend. |
| frontend/src/PdfUpload.jsx | Sau upload và đọc chữ, tự gọi bước tạo vector; dùng chung ở Chat và Tài liệu. |
| frontend/src/Documents.jsx | Phân biệt trạng thái, tự hỏi API mỗi 3 giây khi đang index; thử lại, xem chi tiết từng đoạn, xóa với xác nhận. |
| frontend/src/pdfStatus.js | Chỉ báo sẵn sàng khi index_status=ready. Đọc chữ xong nhưng chưa index không báo sẵn sàng. |
| backend/tests/test_indexing.py | Kiểm tra cắt đoạn, metadata/quyền, đồng thời, rollback, retry, phục hồi lượt quá hạn, xóa file/pages/chunks; có bài riêng cho kiểu vector thật. |
| backend/smoke_week5.py | Nghiệm thu BGE-M3 thật + pgvector thật trong schema và thư mục tạm; tự dọn, không dùng tài liệu riêng của bạn. |

Mã cũ `status=ready` vẫn có nghĩa **đã trích xuất chữ** để không làm mất dữ liệu tuần 4. Trường mới `index_status` là `pending`, `processing`, `ready`, `failed`. PDF cũ sau migration có index_status=pending: vào Tài liệu bấm **Tạo vector / thử lại**, không cần upload lại.

## Chạy trên máy bạn — CMD trong VS Code

Mở thư mục dự án cũ. Dừng backend đang chạy bằng Ctrl+C trước khi nâng cấp thư viện/database; giữ Docker Desktop mở. Tên thư mục vẫn private-ai-week2.

### 1. Sao lưu và cập nhật PostgreSQL

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2"
if not exist backups mkdir backups
docker compose exec -T db pg_dump -U private_ai -d private_ai -Fc -f /tmp/before-week5.dump
docker compose cp db:/tmp/before-week5.dump backups/before-week5.dump
docker compose pull db
docker compose up -d --wait db
```

- `cd /d`: vào đúng thư mục chứa compose.yaml.
- `mkdir`: tạo nơi lưu backup; backups được bỏ qua trong Git vì có dữ liệu riêng tư.
- `pg_dump`: sao lưu database đang chạy; `-U` là user, `-d` là database, `-Fc` là định dạng backup PostgreSQL. Lệnh dùng tên mặc định private_ai; nếu bạn đã đổi chúng trong .env thì dùng tên tương ứng. Nếu backup lỗi, dừng ở đây để xử lý.
- `docker compose cp`: chép backup từ container ra máy. Giữ thêm thư mục backend/storage nếu muốn sao lưu cả PDF gốc. Không ghi đè bản backup cần giữ khi chạy lại; đổi tên theo ngày.
- `pull db`: tải image có pgvector đã khai báo trong compose.yaml.
- `up -d --wait db`: chạy container mới, đợi database khỏe; tái sử dụng volume cũ. **Không dùng `docker compose down -v`: tùy chọn -v xóa volume dữ liệu.**

### 2. Cài thư viện và nâng cấp bảng

```cmd
cd backend
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe check_db.py
```

- Python trong `.venv` đảm bảo dùng môi trường dự án.
- `pip install -r`: cài danh sách thư viện, gồm pgvector và httpx mới.
- `alembic upgrade head`: chạy migration còn thiếu, không tạo lại toàn bộ DB. Migration mới là `0003_document_vectors`. Lần này cần quyền tạo extension; tài khoản database local từ Docker có quyền đó.
- `check_db.py`: kiểm tra revision, extension và đủ 7 bảng. Nếu báo extension vector không tồn tại, container chưa dùng image mới; không sửa migration để bỏ qua lỗi.

Giữ nguyên backend/.env. Giá trị mặc định mới: Ollama http://127.0.0.1:11434, model bge-m3:latest, lô 8, timeout 120 giây/lần gọi, tối đa 3.000 đoạn.

### 3. Mở Ollama và kiểm tra model

```cmd
ollama list
```

Lệnh liệt kê model trên máy, không chạy Qwen. Nếu chưa thấy bge-m3, chạy `ollama pull bge-m3`. BGE-M3 đã có trên máy theo lần kiểm tra của trợ lý.

### 4. Kiểm thử và chạy backend

Trong CMD đang ở backend:

```cmd
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe test_postgres.py
.venv\Scripts\python.exe smoke_week5.py
.venv\Scripts\python.exe -m alembic check
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

- `pytest`: test nhanh bằng SQLite và mô phỏng Ollama; không chứng minh pgvector thật. Các test đòi PostgreSQL sẽ skip ở lệnh này.
- `test_postgres.py`: test PostgreSQL trong schema tạm, gồm migration/quyền/khóa/vector và xóa dây chuyền; Ollama được mô phỏng để test ổn định.
- `smoke_week5.py`: PDF thử → BGE-M3 thật → cột vector thật. Kiểm tra 2 đoạn, 1.024 chiều, chuẩn hóa và xóa sạch. Kỳ vọng dòng PASS. Cần Ollama đang chạy; không dùng dữ liệu người dùng.
- `alembic check`: đối chiếu model với DB; kỳ vọng không có thay đổi schema còn thiếu.
- `uvicorn`: chạy API; `--reload` tải lại code khi sửa. Giữ terminal mở.

### 5. Chạy frontend ở terminal khác

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\frontend"
npm.cmd run dev
```

Không thêm thư viện frontend nên không cần npm install lại. Mở http://127.0.0.1:5173. Nếu Vite báo lỗi quyền nạp config, chạy `npm.cmd run dev -- --configLoader runner`. Có thể chạy `npm.cmd test` để test và `npm.cmd run build` để đóng gói.

## Tự kiểm tra kết quả trên giao diện

1. Đăng nhập, chọn workspace, đính kèm một PDF có chữ; bấm **Tải lên và xử lý**.
2. Thấy lần lượt đang upload, đọc chữ và tạo vector. Cuối cùng **Tài liệu sẵn sàng tìm kiếm**.
3. Mở Tài liệu → **Chi tiết các đoạn**. Xem đoạn, số trang, vị trí ký tự, model, 1.024 chiều. Chuyển đoạn để so với PDF gốc.
4. Tài liệu tuần 4: bấm **Tạo vector / thử lại**. Chưa có vector thì phải hiện chưa sẵn sàng.
5. Tắt Ollama rồi thử tài liệu nhỏ khác: giữ nguyên PDF/chữ, báo lỗi tạo vector. Mở Ollama, bấm thử lại để thành công; không upload lại.
6. Đổi workspace hoặc tài khoản: không thấy tài liệu/chi tiết của workspace khác.
7. Với PDF thử: bấm Xóa → Hủy để giữ; bấm Xóa → Xác nhận để dọn PDF, các trang, đoạn và vector.

## Cách xử lý lỗi và giới hạn hiện tại

- Việc index chạy trong request, chưa có hàng đợi nền bền vững. Trạng thái processing được lưu trước nên tab khác có thể theo dõi.
- Mỗi công việc có giới hạn 10 phút và mã riêng. Server tắt giữa chừng thì trạng thái processing có thể còn; sau 15 phút bấm thử lại. Lượt cũ không được ghi đè lượt mới. Đây là lease để phục hồi, không phải tự động chạy lại.
- Vector được chuẩn bị theo lô nhưng chỉ lưu tất cả cùng trạng thái ready trong một transaction. Nếu một lô hoặc DB lỗi, không công bố bộ vector dở dang. Không có tiến độ % giả.
- Bấm tạo vector lại với tài liệu đã ready trả kết quả cũ; chưa có chức năng đổi model/reindex tài liệu ready. Model/vector dimension hiện cố định cho BGE-M3 1.024 chiều.
- Cắt theo ký tự có thể ngắt câu/từ và không bảo toàn bảng/cột. Có thể cải thiện bộ tách ở bước đánh giá RAG. Chưa thêm HNSW hoặc tìm kiếm; tuần sau mới cần truy vấn tương đồng lọc workspace.
- Xóa tài liệu dùng file tạm `.pdf.deleting` để phục hồi khi DB commit lỗi. Nếu máy tắt đúng giữa thao tác, có thể còn file tạm cần kiểm tra; chưa có tác vụ tự dọn file mồ côi. Không phục vụ storage bằng URL public.
- Chưa có giới hạn đồng thời toàn hệ thống hoặc hàng đợi GPU; đây vẫn là ứng dụng local cho đồ án.

## Minh chứng và Git

Minh chứng mới chỉ lưu `docs/evidence/week5/`; giữ nguyên week2/week3/week4 và các tag cũ. Không force-push hoặc viết lại lịch sử. Không đưa `.env`, PDF, database thử hoặc backups lên Git. Xem README trong thư mục minh chứng để biết kiểm tra nào đã chạy và mục nào còn chờ.

Nguồn kỹ thuật: [Ollama /api/embed](https://docs.ollama.com/api/embed), [BGE-M3 model card](https://huggingface.co/BAAI/bge-m3), [pgvector và Docker images](https://github.com/pgvector/pgvector#docker).


## Sửa lỗi kiểm thử trên Windows và cô lập schema

Nếu log cũ có `PermissionError ... pytest-of-Admin`, pytest chưa tạo được nơi lưu PDF thử. `backend/conftest.py` hiện tạo thư mục tạm riêng cho từng lần chạy và dọn sau khi xong. Không cần chạy CMD bằng Administrator, xóa Temp chung hoặc đổi quyền Windows.

Lỗi `legacy@example.com already exists` và smoke đăng ký thất bại đến từ harness cũ nhìn thấy bảng public qua search_path. Đã sửa việc tạo bảng test và chỉ định schema riêng cho alembic_version. Bản sửa xác minh các bảng thật sự tồn tại trong schema thử trước khi gửi request. Không giải quyết bằng đổi email ngẫu nhiên để che lỗi.

Sau bản sửa chỉ cần chạy lại `python test_postgres.py` và `python smoke_week5.py` bằng Python .venv như các lệnh trên. Không cần cài thêm thư viện hoặc nâng cấp migration. Trợ lý đã chạy đạt trên PostgreSQL/pgvector local và kiểm tra các bảng ứng dụng không thay đổi sau mỗi lần chạy.
