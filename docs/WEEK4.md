# Tuần 4 — upload PDF và trích xuất văn bản

## Mục tiêu và luồng hoạt động

Tuần 3 biết người dùng là ai và workspace thuộc về ai. Tuần 4 thêm tài liệu thật vào workspace đó:

1. Bạn chọn PDF trên giao diện. Lúc này file vẫn chỉ ở máy trình duyệt, chưa upload.
2. Bấm Tải lên và trích xuất: React gửi file bằng multipart/form-data tới FastAPI.
3. Backend kiểm tra quyền sở hữu workspace, đuôi .pdf, dấu hiệu nội dung %PDF- và dung lượng.
4. Backend lưu file bằng tên UUID riêng, thêm bản ghi documents với trạng thái uploaded.
5. React gọi API process. Backend đọc PDF bằng pypdf trong tiến trình riêng có thời hạn; lưu văn bản cùng số trang vào document_pages.
6. Thành công: ready. Không đọc được: failed kèm lý do. Giao diện cho xem từng trang hoặc thử lại.

Upload và process là hai request riêng. Trong khi process chạy, giao diện hiển thị Đang trích xuất. Database giữ trạng thái cũ đến khi giao dịch hoàn tất, không lưu trạng thái processing dễ bị mắc kẹt khi server tắt. Nếu mất kết nối/đổi workspace giữa chừng, bấm Làm mới danh sách để kiểm tra file đã lưu; thử trích xuất lại nếu vẫn uploaded/failed. Không mặc định upload lại vì sẽ tạo bản sao.

## Từng thay đổi trong code

Bổ sung giao diện: nút **+ Đính kèm PDF** nằm ngay trong khung chat. Trang **Tài liệu** vẫn là nơi xem danh sách, đọc văn bản từng trang và thử trích xuất lại. Cả hai nơi dùng chung `frontend/src/PdfUpload.jsx`, nên cùng cách chọn/kéo thả và gọi API; không tạo hai luồng lưu file khác nhau. `frontend/src/pdfStatus.js` quyết định thông báo theo kết quả thật từ backend.

- Chọn hoặc kéo thả PDF chỉ chọn file trên máy. Bấm **Tải lên và trích xuất** mới gửi file. **Bỏ chọn** không xóa tài liệu đã lưu.
- Trong khi chạy, giao diện lần lượt báo đang tải lên và đang đọc văn bản.
- Màu xanh: đã lưu và đọc được chữ. Màu vàng: đã lưu nhưng đọc chữ thất bại hoặc chưa xác nhận được kết quả đọc. Màu đỏ: bị từ chối tải lên hoặc mất kết nối; thông báo nêu rõ trường hợp nào.
- Mất kết nối không chứng minh file chưa được lưu. Kiểm tra danh sách trước khi tải lại để tránh tạo bản sao.
- Đổi workspace xóa lựa chọn file và thông báo cũ. File đã lưu vẫn thuộc workspace ban đầu. Chưa chọn workspace thì nút đính kèm bị khóa.
- Nút gửi chat AI vẫn bị khóa: đọc PDF thành công chưa có nghĩa đã có RAG.

Bản bổ sung này chỉ sửa frontend, không thêm thư viện hoặc migration. Nếu Vite đang chạy, giao diện tự cập nhật; nếu chưa, mở CMD tại thư mục frontend và chạy `npm.cmd run dev`. Lệnh này khởi động máy chủ giao diện để bạn kiểm tra trên trình duyệt. Khi tải lại trang, đăng nhập lại vì token hiện chỉ giữ trong bộ nhớ.

| File | Vai trò |
|---|---|
| backend/app/models.py | Thêm dung lượng, trạng thái, số trang, lý do lỗi của Document; thêm DocumentPage lưu chữ theo trang. |
| backend/alembic/versions/0002_pdf_documents.py | Migration nâng cấp DB từ tuần 3, giữ các bảng và bản ghi cũ. Tài liệu cũ chỉ có tên mà chưa có file được ghi failed với lời nhắc tải lại. |
| backend/app/documents.py | Nhận file, lưu file, kiểm tra owner và document thuộc đúng workspace, gọi tiến trình đọc, trả metadata hoặc văn bản phân trang. |
| backend/app/pdf_worker.py | Dùng pypdf đọc chữ theo trang; không gọi LLM, không truy cập DB. Tách tiến trình để có thể dừng khi quá 30 giây. |
| backend/app/upload_limit.py | Chặn tổng body upload quá lớn, kể cả khi client không gửi Content-Length. |
| backend/app/config.py và .env.example | Giới hạn mặc định: 20 MiB/file, 200 trang, 2 triệu ký tự, 30 giây đọc PDF. Thư mục lưu mặc định backend/storage. |
| backend/app/schemas.py | Cho API trả size_bytes/status/page_count/error_message và dữ liệu từng trang. Không trả đường dẫn file trên máy chủ. |
| backend/app/main.py | Gắn các route PDF và middleware giới hạn upload vào ứng dụng. |
| backend/requirements.txt | Thêm python-multipart để nhận file và pypdf để đọc PDF. |
| backend/check_db.py | Xác minh revision 0002_pdf_documents và đủ 6 bảng, gồm document_pages. |
| frontend/src/api.js | Gửi FormData nguyên dạng; để trình duyệt tự đặt Content-Type/boundary. JSON cho API đăng nhập/workspace vẫn giữ cách cũ. |
| frontend/src/Documents.jsx | Form upload, danh sách trạng thái, xử lý lại và xem từng trang. Hủy nhận kết quả request cũ khi đổi workspace/đăng xuất. |
| frontend/src/App.jsx và styles.css | Dùng trang tài liệu mới, bố cục danh sách/khung đọc phù hợp desktop/mobile. Chat vẫn chỉ một ô và chưa bật gửi. |
| .gitignore | Bỏ qua backend/storage: PDF riêng tư không lên GitHub. |
| backend/tests/test_documents.py | Test PDF thật tạo bằng code, file hỏng, mã hóa, không có chữ, giới hạn, xử lý lại, quyền giữa hai tài khoản và dọn file khi DB lỗi. |
| backend/tests/test_pdf_migration.py | Chạy migration thật trên PostgreSQL tạm và kiểm tra dữ liệu cũ còn nguyên, schema khớp model. |

### File gốc và database lưu khác nhau thế nào?

- File gốc: backend/storage/<workspace UUID>/<document UUID>.pdf. Tên do backend tạo nên hai file cùng tên không ghi đè nhau. Không dùng tên file người dùng gửi làm đường dẫn.
- Bảng documents: thông tin file, workspace, trạng thái và lỗi. Bảng document_pages: từng trang và văn bản đã đọc.
- File không được công bố dưới URL static. Chỉ người sở hữu workspace mới gọi được API đọc metadata/văn bản. Đoán đúng document ID nhưng dùng workspace khác vẫn bị từ chối.
- Khi sao lưu cần giữ cả PostgreSQL và thư mục storage. Clone GitHub không tải theo các PDF đã upload trên máy người khác.

### Trạng thái có nghĩa gì?

| Trạng thái | Nghĩa | Việc bạn có thể làm |
|---|---|---|
| uploaded | Đã lưu file, chưa có kết quả trích xuất | Bấm Thử trích xuất |
| ready | Đã đọc được văn bản | Bấm Xem văn bản, chuyển trang |
| failed | Không trích xuất được | Đọc lý do; thử lại nếu lỗi tạm thời, chọn file khác nếu file hỏng/mã hóa/scan |

Ready không có nghĩa đã embedding, tìm kiếm hoặc RAG. pypdf không làm OCR; ảnh scan và văn bản dạng ảnh cần bước khác sau này. PDF nhiều cột/bảng có thể cho thứ tự chữ khác bản gốc. Với PDF vừa có chữ vừa có ảnh, chỉ chữ đọc được được lưu, không nhận dạng chữ trong ảnh; trang trắng hiển thị thông báo không có chữ.

## Chạy trong VS Code bằng CMD

Mở cùng thư mục dự án, không tạo bản sao tuần 4. Mở Docker Desktop. Nếu backend/frontend cũ còn chạy, Ctrl+C tại đúng terminal để dừng trước khi khởi động lại. Ctrl+C không xóa dữ liệu.

### Terminal 1: database

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2"
docker compose up -d --wait db
```

cd /d chuyển vào đúng thư mục và ổ đĩa. docker compose đọc compose.yaml; up khởi động db, -d chạy nền, --wait đợi healthy. Tên thư mục private-ai-week2 vẫn giữ nguyên dù code đã sang tuần 4.

### Terminal 2: cài thư viện, nâng cấp DB, chạy backend

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\backend"
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe check_db.py
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

- .venv\Scripts\python.exe dùng Python của dự án. -m pip install -r requirements-dev.txt cài thư viện theo danh sách, bao gồm hai thư viện PDF mới.
- -m alembic upgrade head chạy các migration chưa có đến bản mới nhất. Trợ lý đã nâng cấp DB local khi triển khai; chạy lại là an toàn, không tạo lại bảng. Trên máy Khánh, lệnh này thực hiện nâng cấp còn thiếu.
- check_db.py kiểm tra kết nối và cấu trúc. Kỳ vọng Migration: 0002_pdf_documents, đủ 6 bảng và PASS.
- uvicorn chạy backend; --factory gọi create_app; --reload nạp lại khi sửa code; host chỉ máy local, cổng 8000. Giữ terminal mở.

Giữ nguyên backend/.env từ tuần 3. Không chép đè .env bằng file mẫu vì có cấu hình DB và khóa JWT riêng. Các cài đặt PDF mới có giá trị mặc định nên không bắt buộc sửa .env.

### Terminal 3: frontend

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\frontend"
npm.cmd run dev
```

Tuần 4 không thêm thư viện frontend, nên máy đã cài tuần 3 không cần npm ci lại. Máy mới cần npm.cmd ci để cài theo package-lock.json. npm.cmd run dev chạy Vite; mở http://127.0.0.1:5173. Nếu gặp lỗi quyền nạp config, dùng npm.cmd run dev -- --configLoader runner.

## Kiểm tra bằng thao tác thật

1. Đăng nhập tài khoản tuần 3, chọn hoặc tạo workspace A.
2. Chọn Tài liệu, chọn PDF có chữ (thử bôi đen/copy được chữ trong trình đọc PDF), bấm Tải lên và trích xuất.
3. Kỳ vọng Đã trích xuất, có số trang; bấm Xem văn bản và chuyển trang để so với PDF gốc.
4. Chuyển workspace B: file và phần xem trước của A không xuất hiện. Trở lại A: tài liệu vẫn còn.
5. Thử PDF mã hóa hoặc scan không có lớp chữ: hiển thị lý do lỗi, không báo thành công giả.
6. Đăng nhập tài khoản B: không thấy workspace/tài liệu của tài khoản A.

Khi thử lại PDF ready, API trả kết quả cũ, không tạo thêm trang. File trùng tên upload lại được coi là tài liệu mới; chưa có dedup. Workspace có tài liệu vẫn không xóa được (409); tuần này chưa có chức năng xóa tài liệu/file hoặc tải bản gốc về.

## Chạy kiểm thử tự động

Ở backend, terminal riêng:

```cmd
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe test_postgres.py
.venv\Scripts\python.exe -m alembic check
```

pytest chạy test SQLite tạm và mock; hai test cần PostgreSQL sẽ skip khi chưa có TEST_DATABASE_URL. test_postgres.py tự đọc cấu hình DB và chạy kiểm thử PostgreSQL trong schema tạm riêng, gồm kiểm tra khóa xử lý đồng thời và migration; không ghi tài khoản thử vào bảng ứng dụng. alembic check xác nhận model khớp DB, không tạo migration.

Ở frontend: npm.cmd test kiểm tra API client, npm.cmd run build đóng gói giao diện. Trong môi trường công cụ, build dùng thêm -- --configLoader runner vì lỗi quyền thư mục khi nạp config mặc định.

Lưu minh chứng mới vào docs/evidence/week4 bằng tên mới mỗi lần. Không ghi đè week2/week3. Chưa tạo tag week-04 cho đến khi người dùng chạy nghiệm thu. Không dùng reset --hard, rebase lịch sử đã chia sẻ hoặc push --force.

## Giới hạn và bước sau

Trích xuất hiện chạy đồng bộ trong một request có giới hạn thời gian; chưa có hàng đợi worker bền vững. Khóa hàng PostgreSQL ngăn hai request cùng xử lý một tài liệu. Nếu tiến trình dừng trước commit, trạng thái cũ được giữ để thử lại. PDF được đọc ở subprocess có timeout nhưng chưa có giới hạn RAM cứng hoặc sandbox hệ điều hành; đây vẫn là ứng dụng local, chưa sẵn sàng nhận file công khai trên Internet. Khi triển khai ngoài local cần bổ sung quota, giới hạn concurrency và cô lập parser.

Tuần tiếp theo mới chia văn bản thành chunks, tạo embedding bằng BGE-M3 và lưu vector. Không gọi Qwen/Ollama hoặc chạy RAG trong luồng tuần 4.

Nguồn triển khai: [FastAPI file uploads](https://fastapi.tiangolo.com/tutorial/request-files/), [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html).
