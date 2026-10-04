# Tuần 3 — tài khoản và workspace

Hướng dẫn ngày 05/10/2026. Tiếp tục cùng repository; tên thư mục private-ai-week2 vẫn giữ để các đường dẫn cũ dùng được. Minh chứng mới nằm trong docs/evidence/week3. Không đổi tag week-02, không sửa lịch sử Git.

## 1. Từng thay đổi có ý nghĩa gì?

| File | Thay đổi và lý do |
|---|---|
| backend/app/schemas.py | Kiểm tra email, mật khẩu 8–128 ký tự, tên workspace 1–200 ký tự; từ chối trường ngoài hợp đồng như owner_id do trình duyệt tự gửi. Schema trả về không có password_hash. |
| backend/app/security.py | Argon2 băm mật khẩu. JWT ký HS256 chứa ID người dùng, hạn dùng, issuer/audience; API kiểm tra chữ ký và tài khoản còn tồn tại. Session SQLAlchemy được đóng sau mỗi request. |
| backend/app/routes.py | Đăng ký, đăng nhập, xem tài khoản; tạo/liệt kê/xem/đổi tên/xóa workspace; danh sách tài liệu/hội thoại theo workspace. Chủ sở hữu lấy từ JWT. Người khác truy cập ID sẽ nhận 404, giống ID không tồn tại. |
| backend/app/config.py | Thêm JWT_SECRET tối thiểu 32 ký tự và hạn token 30 phút; thiếu khóa thì từ chối khởi động. |
| backend/setup_auth.py | Tạo khóa ngẫu nhiên trong backend/.env, không in khóa ra màn hình và không thay khóa đã có. File .env vẫn bị Git bỏ qua. |
| backend/app/main.py | Gắn các API mới, cho phép CORS với Authorization và POST/PATCH/DELETE từ hai địa chỉ frontend local đã có. |
| backend/requirements.txt | Thêm PyJWT, pwdlib với Argon2 và email-validator; dùng thư viện thay vì tự viết thuật toán bảo mật. |
| frontend/src/api.js | Dùng chung hàm gửi JSON và Bearer token; giữ mã lỗi 401 để giao diện yêu cầu đăng nhập lại. |
| frontend/src/Account.jsx | Form đăng ký/đăng nhập, chọn/tạo/đổi tên/xóa workspace, đọc danh sách theo workspace. Xóa cần xác nhận trên giao diện. |
| frontend/src/App.jsx | Giữ token trong bộ nhớ, xóa workspace khi đăng xuất/hết hạn; không lưu token ở localStorage. Chuyển workspace tháo danh sách cũ và hủy request cũ. Giữ một ô chat chung, chưa bật RAG. |
| frontend/src/styles.css | Kiểu dáng form, nhãn, trạng thái lỗi, hỗ trợ màn hình hẹp theo bố cục hiện có. |
| backend/tests/test_auth_workspaces.py | Dùng hai tài khoản kiểm tra cách ly dữ liệu; kiểm tra token giả/hết hạn, email trùng, xóa workspace có dữ liệu. |
| backend/test_postgres.py | Chạy cùng test trên PostgreSQL bằng schema tạm có tên duy nhất; dọn schema tạm sau test, không dùng bảng ứng dụng. |
| frontend/src/api.test.js | Kiểm tra Authorization, JSON, lỗi 401/422 và phản hồi xóa 204 ngoài các test health cũ. |

Không cần migration mới: users.email/password_hash, workspaces.owner_id/name và liên kết tài liệu/hội thoại đã có trong 0001_initial. Alembic vẫn quản lý schema, không dùng create_all khi khởi động ứng dụng. create_all chỉ xuất hiện trong test cho cơ sở dữ liệu/schema tạm.

## 2. Chạy trên máy bạn — CMD

Nếu backend tuần 2 vẫn đang chạy, chọn đúng cửa sổ đó và nhấn Ctrl+C. Lệnh này dừng server trong cửa sổ, không xóa dữ liệu. Mở Docker Desktop trước khi làm bước A.

### A. Cửa sổ CMD thứ nhất: PostgreSQL

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2"
docker compose up -d --wait db
```

- cd /d chuyển vào dự án và chuyển ổ đĩa nếu cần. Nếu clone ở chỗ khác thì thay đường dẫn.
- docker compose up đọc compose.yaml; db là dịch vụ PostgreSQL; -d chạy nền; --wait đợi healthy. Volume dữ liệu cũ được giữ.

### B. Cửa sổ CMD thứ hai: backend

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\backend"
if not exist .env copy .env.example .env
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe setup_auth.py
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

- cd /d chọn thư mục backend, nơi chứa các lệnh Python và cấu hình Alembic.
- if not exist chỉ tạo .env nếu chưa có, không ghi đè cấu hình DB bạn đã dùng.
- .venv\Scripts\python.exe chọn đúng môi trường Python của dự án, không cần activate. pip install -r đọc danh sách và cài thư viện mới cùng công cụ kiểm thử. Nếu máy mới chưa có .venv, chạy py -3.12 -m venv .venv trước.
- setup_auth.py tạo khóa JWT một lần. Trợ lý đã tạo khóa trong .env local khi triển khai; chạy lại sẽ giữ nguyên. Trên máy Khánh, script tạo khóa riêng. Không gửi khóa hoặc .env lên GitHub.
- alembic upgrade head đưa DB tới migration mới nhất; tuần này không có migration mới nên DB tuần 2 đã đúng sẽ không thay bảng.
- uvicorn chạy FastAPI. --factory gọi hàm create_app để tạo ứng dụng; --reload tự nạp lại khi sửa code; --host 127.0.0.1 chỉ nghe trên máy bạn; --port 8000 là cổng API. Giữ cửa sổ này mở.

### C. Cửa sổ CMD thứ ba: frontend

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\frontend"
npm.cmd ci
npm.cmd run dev
```

- cd /d chọn frontend.
- npm.cmd ci cài đúng phiên bản trong package-lock.json; không nâng cấp dependency. Tuần này không thêm thư viện frontend.
- npm.cmd run dev chạy Vite. Giữ terminal mở, truy cập http://127.0.0.1:5173.

Nếu Vite báo Cannot read directory / Access is denied khi nạp config như môi trường công cụ, dùng npm.cmd run dev -- --configLoader runner. Phần -- chuyển cờ tiếp cho Vite; runner đổi cách nạp cấu hình, không sửa code ứng dụng.

## 3. Tự kiểm tra giao diện

1. Đăng ký tài khoản A bằng email dạng alice@example.com và mật khẩu thử dài ít nhất 8 ký tự. Thành công sẽ tự đăng nhập.
2. Tạo workspace Môn học A. Đổi tên rồi chọn mục Tài liệu và Lịch sử. Hiện danh sách trống là đúng: chưa có upload hoặc chat AI.
3. Tạo workspace Môn học B; chuyển giữa hai workspace. Tên trang thay theo workspace, không giữ danh sách cũ khi tải workspace mới.
4. Đăng xuất; đăng ký tài khoản B bằng email khác. B không nhìn thấy workspace của A. Đăng nhập lại A để xác nhận dữ liệu vẫn còn.
5. Thử mật khẩu sai và email đăng ký trùng: giao diện phải báo lỗi. Tải lại trang sẽ yêu cầu đăng nhập lại vì token chỉ nằm trong bộ nhớ.
6. Xóa workspace trống bằng nút Xác nhận xóa. API từ chối xóa workspace có tài liệu/hội thoại để tránh mất dữ liệu ngoài ý muốn.

Để xem API, mở http://127.0.0.1:8000/docs. Login nhận JSON email/password, không dùng form OAuth2. Sau login có thể dùng nút Authorize nhập access_token để thử endpoint có khóa. Không đưa token vào ảnh minh chứng.

## 4. Lệnh kiểm thử và lưu kết quả

Ở backend, trong CMD khác với server:

```cmd
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe test_postgres.py
.venv\Scripts\python.exe -m alembic check
.venv\Scripts\python.exe check_db.py
```

- pytest chạy kiểm thử tự động: auth/workspace dùng SQLite tạm với khóa ngoại bật; health dùng mock. Không chạm dữ liệu thật.
- test_postgres.py chạy các kiểm thử auth/workspace trên PostgreSQL đang cấu hình; tạo rồi dọn schema test_week3_* riêng. User DB cần quyền tạo schema (tài khoản local hiện tại có). Không dùng lệnh này trên DB production.
- alembic check đối chiếu model với DB; No new upgrade operations detected nghĩa là không có thay đổi schema bị quên migration.
- check_db.py truy vấn DB thật và xác minh migration cùng năm bảng.

Ở frontend:

```cmd
npm.cmd test
npm.cmd run build
```

- npm.cmd test chạy kiểm thử API client bằng mock fetch.
- npm.cmd run build đóng gói React vào dist, giúp phát hiện lỗi biên dịch. Nếu gặp lỗi quyền nạp config, dùng npm.cmd run build -- --configLoader runner.

Khi lưu output lần chạy mới, chọn tên chưa tồn tại trong docs/evidence/week3, ví dụ backend-tests-duc-01.txt. Trong CMD, > chuyển output vào file, 2>&1 gộp cả lỗi; ví dụ tại backend: .venv\Scripts\python.exe -m pytest -q > ..\docs\evidence\week3\backend-tests-duc-01.txt 2>&1. Không dùng lại tên file cũ vì > sẽ ghi đè. Ghi git rev-parse HEAD để biết bản code được kiểm tra.

## 5. Giới hạn hiện tại

Đăng xuất xóa token khỏi trình duyệt, chưa thu hồi token ở server: token bị sao chép trước đó vẫn có hiệu lực tối đa 30 phút. Chưa có refresh token, khôi phục mật khẩu, xác minh email, giới hạn thử đăng nhập hoặc phân quyền Admin. Đây là bản chạy local; triển khai Internet cần HTTPS và bổ sung các kiểm soát này. Chưa triển khai upload/parse PDF, pgvector, RAG, gửi chat hoặc mở nội dung lịch sử.

## 6. Xem thay đổi và đưa lên GitHub

Ở thư mục gốc repository, sau khi commit triển khai đã được tạo:

```cmd
git status -sb
git show --stat HEAD
git push origin main
```

- git status -sb cho biết nhánh đang dùng và file còn thay đổi; ahead 1 nghĩa là có một commit local chưa push.
- git show --stat HEAD hiển thị tóm tắt các file trong commit mới nhất để bạn xem trước.
- git push origin main gửi commit mới của main lên GitHub tên origin. Đây là push thường, không sửa lịch sử. Nếu remote có commit mới, dừng và đọc thông báo; không dùng --force.

Sau khi người dùng báo chạy thử OK, mốc week-03 được dùng để chốt code và minh chứng hiện có; chưa có xác nhận của Khánh. Tag week-02 vẫn chỉ đúng snapshot đã chốt, không di chuyển sang code tuần 3.

Tham khảo cách dùng thư viện: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
