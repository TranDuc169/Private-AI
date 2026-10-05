# Minh chứng tuần 4 — 05/10/2026

Các lần chạy do trợ lý thực hiện trực tiếp trên code tuần 4, nền commit 3949bbd. Minh chứng tuần 2–3 không thay đổi. Chưa có xác nhận nghiệm thu tuần 4 của người dùng/Khánh; chưa tạo tag week-04.

| Kiểm tra | Minh chứng |
|---|---|
| Backend SQLite/mock | backend-tests-01/02/03.txt: lưu các lần chạy khi bổ sung test; bản 03: 19 pass, 2 skip cần PostgreSQL |
| PostgreSQL + migration | postgres-tests-01/02.txt: schema test riêng; bản 02: 18 pass, gồm DB lỗi và xử lý đồng thời |
| Frontend API | frontend-tests-01.txt: 7 test pass, gồm FormData không ghi đè multipart boundary |
| Frontend build | frontend-build-01.txt: build thành công với configLoader runner |
| Browser Edge headless | browser-tests-01.txt: upload PDF thật 2 trang, xem chữ từng trang, PDF không chữ báo lỗi, chuyển workspace xóa preview, tài khoản khác không thấy tài liệu; không lỗi JS/tràn ngang mobile |
| Database local | database-before.txt và database-counts-after.txt: cùng 2 users, 1 workspace, 0 documents/conversations/messages; không mất bản ghi |
| Migration local | database-after.txt: revision 0002_pdf_documents, đủ 6 bảng; migration-upgrade.txt có thể trống vì Alembic không cấu hình logging |
| Schema đối chiếu | alembic-check.txt: No new upgrade operations detected |

Ảnh: 01-pdf-text.png, 02-scan-error.png, 03-mobile-documents.png. Đã xem trực tiếp ảnh desktop văn bản và mobile. PDF trong test được tạo bằng code trong tests/test_documents.py; không lấy tài liệu riêng của người dùng làm dữ liệu thử. Browser chạy server riêng cổng 8014/5174, schema PostgreSQL và kho file tạm; không chạm workspace/tài liệu người dùng.

Môi trường kiểm thử: Python 3.12.14 tại .venv-week3 ngoài repo (tái sử dụng môi trường thử), pypdf và python-multipart theo python-packages.txt; không cài vào .venv người dùng. Còn cảnh báo Starlette/httpx deprecation và Alembic path_separator; không làm thất bại test.

Các bài thử kiểm tra quyền đọc/process/upload theo workspace, filename traversal, file trùng tên, file quá lớn (có và không Content-Length), PDF hỏng/mã hóa/không chữ/quá số trang, giới hạn ký tự, timeout, retry, mất file gốc và dọn file khi DB commit lỗi. Migration test riêng có bản ghi legacy documents để chứng minh giữ tài khoản/workspace/tài liệu cũ và đánh dấu đúng tài liệu thiếu file; database local thực tế chưa có tài liệu cũ.

Không đánh giá chất lượng OCR hoặc RAG; hai chức năng đó chưa triển khai. Nguồn mô tả và lệnh chạy lại: ../../WEEK4.md.
