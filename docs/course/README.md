# Bộ PDF demo môn Cơ sở dữ liệu

Đây là **5 phiếu học tập ngắn được biên soạn có hỗ trợ AI**, mỗi phiếu gồm 2 trang kiến thức và 1 trang ghi nguồn/quyền sử dụng. Không phải bản dịch chính thức hoặc giáo trình đầy đủ; cần nhóm/giảng viên rà soát trước khi dùng như tài liệu giảng dạy. Chủ đề được ghi trong PDF và manifest, chưa có trường chủ đề mới trong database.

| PDF | Chủ đề | Nguồn tham khảo |
|---|---|---|
| `pdfs/01-quan-he-rang-buoc.pdf` | Khóa chính, UNIQUE, FK, CHECK | PostgreSQL 16: Constraints |
| `pdfs/02-sql-join.pdf` | INNER/LEFT JOIN, ON/WHERE/HAVING | PostgreSQL 16: Table Expressions |
| `pdfs/03-erd-chuan-hoa.pdf` | ERD, nhiều-nhiều, 1NF–3NF | Database Design, 2nd Edition, chương 8 và 12 |
| `pdfs/04-transaction.pdf` | BEGIN, COMMIT, ROLLBACK, SAVEPOINT | PostgreSQL 16: Transactions |
| `pdfs/05-index-explain.pdf` | Index, EXPLAIN/ANALYZE | PostgreSQL 16: Indexes Introduction, Using EXPLAIN |

Nguồn, tác giả, phiên bản, ngày tra cứu và SHA-256 của từng file nằm trong `manifest.json`. Văn bản chỉnh sửa nằm ở `corpus.json`. Ví dụ sinh viên/môn học do dự án tự soạn; không dùng tài liệu riêng tư.

PostgreSQL cho phép sử dụng/sửa/phân phối phần mềm và tài liệu theo [PostgreSQL License](https://www.postgresql.org/about/licence/); thông báo giấy phép được giữ ở trang cuối các phiếu tương ứng. Tài liệu Database Design của Adrienne Watt và Nelson Eng (2014) dùng [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); phiếu 03 ghi rõ tác giả, link, thay đổi và cùng giấy phép. Không hàm ý các tác giả bảo trợ dự án.

Nội dung minh họa một số tình huống cơ bản, không bao phủ toàn bộ môn học. Đặc biệt chuẩn hóa phải xác định khóa ứng viên/phụ thuộc hàm; không chỉ nhìn vài hàng dữ liệu để kết luận. PostgreSQL có các chi tiết khác hệ quản trị khác.

## Nạp vào tài khoản của bạn

Mở backend, Docker và Ollama trước. Tại `backend`, chạy:

```cmd
.venv\Scripts\python.exe load_demo_course.py
```

Nhập email/mật khẩu đã đăng ký trên web. Mật khẩu không hiện khi gõ, không ghi vào file/log. Script dùng API đăng nhập, tạo **workspace mới**, upload → trích văn bản → tạo vector cho 5 PDF. Không ghi thẳng vào database hoặc ghi đè workspace cũ. Nếu lỗi giữa chừng, các file đã tạo vẫn còn để bạn xem/thử lại trên web. Chạy lại script sẽ tạo workspace mới, vì vậy không chạy lặp chỉ để refresh giao diện.

Bạn cũng có thể tạo workspace trên web và upload lần lượt 5 PDF bằng nút Đính kèm PDF. Cách này không cần nhập thông tin đăng nhập vào script.

## Tạo lại PDF khi sửa học liệu (không cần để chạy ứng dụng)

`build_pdfs.py` dùng ReportLab và font Unicode. Nếu môi trường authoring có ReportLab:

```cmd
python docs\course\build_pdfs.py
```

Trên Windows mặc định dùng Arial. Máy khác đặt `COURSE_FONT` tới font TrueType hỗ trợ tiếng Việt. Script tạo lại 5 PDF và manifest SHA-256; kiểm tra trực quan và trích chữ sau khi tạo. Khi thay học liệu phải đánh giá lại, không sửa đè minh chứng cũ.
