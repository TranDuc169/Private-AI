# Minh chứng tuần 3 — 05/10/2026

Nguồn: trợ lý chạy trực tiếp trên bản thay đổi tuần 3, nền commit cf2d49e. Không phải kết quả tuần 2. Các log giữ output thật, kể cả cảnh báo và lần build mặc định bị lỗi quyền.

| Kiểm tra | Kết quả | File |
|---|---|---|
| Backend pytest | 10 pass; SQLite tạm có FK cho auth/workspace, mock health; cảnh báo Starlette và quyền ghi pytest cache | backend-tests.txt |
| Auth/workspace PostgreSQL | 7 pass, schema test_week3_* riêng được dọn sau mỗi test; cảnh báo Starlette/httpx deprecation | backend-postgres-tests.txt |
| Database local | SELECT 1, đủ 5 bảng, revision 0001_initial | database-check.txt |
| Alembic | Không có thay đổi schema | alembic-check.txt |
| Frontend Node test | 6 pass, mock fetch | frontend-tests.txt |
| Build mặc định | Không hoàn tất do quyền đọc thư mục cha của công cụ | frontend-build.txt |
| Build --configLoader runner | PASS Vite production build | frontend-build-runner.txt |
| Browser Edge headless | PASS đăng ký/đăng nhập, CRUD/chọn workspace, hai tài khoản cách ly, danh sách trống, logout, reload, mobile không tràn ngang; không có JS pageerror | browser-tests.txt |

Ảnh: 01-workspace.png, 02-second-account.png, 03-mobile-login.png. Đã xem trực tiếp ảnh desktop workspace và mobile login để kiểm tra bố cục. Trình duyệt chạy frontend thật cùng FastAPI thật, dùng schema PostgreSQL tạm riêng cho dữ liệu thử. Test API còn kiểm tra đổi ID sang workspace người khác, token giả/hết hạn và danh sách tài liệu/hội thoại có dữ liệu riêng từng workspace; không chỉ kiểm tra trạng thái trống trên UI.

Môi trường: Python 3.12.14 trong .venv-week3 riêng ngoài repo, phiên bản Python packages trong python-packages.txt; Vite 6.4.3. Không thay .venv Python 3.12 của người dùng. Đã bổ sung JWT_SECRET ngẫu nhiên vào backend/.env local bằng setup_auth.py; khóa không nằm trong log/repo. File requirements mô tả khoảng phiên bản; python-packages.txt ghi phiên bản lần kiểm tra này, không phải lockfile đa nền tảng.

Người dùng đã báo “test oke rồi”; phạm vi xác nhận và giới hạn ghi trong [user-confirmation-2026-10-05.md](user-confirmation-2026-10-05.md). Chưa có xác nhận của Khánh. Mốc week-03 chốt code và minh chứng hiện có. Không thay minh chứng week2 hay tag week-02. Các hạn chế triển khai hiện tại được ghi trong ../../WEEK3.md.
