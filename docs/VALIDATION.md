# Biên bản kiểm tra

Ngày: 02/10/2026. Không đánh dấu đạt nghiệm thu end-to-end khi chưa chạy đủ dịch vụ.

| Kiểm tra | Kết quả thực tế |
|---|---|
| PDF phân công | Đọc văn bản 7 trang |
| PDF báo cáo tuần 1 | Đọc văn bản 11 trang; xem ảnh chat prototype |
| GitHub repository | Trình duyệt hiển thị repository public, rỗng |
| API client: 200 đúng contract | PASS bằng Node REPL, mock fetch |
| API client: 503 DB down | PASS bằng Node REPL, mock fetch |
| API client: HTML thay JSON | PASS: từ chối phản hồi |
| API client: JSON thiếu field | PASS: từ chối phản hồi |
| API client: JSON null | PASS: báo sai contract |
| API client: HTTP 500 | PASS: báo lỗi HTTP |
| API client: lỗi mạng | PASS: truyền lỗi để UI hiển thị |
| React production build / tương tác UI | Chưa chạy: chưa có Node/npm CLI và dependencies |
| pytest backend | Chưa chạy: chưa có Python/dependencies |
| PostgreSQL + migration + alembic check | Chưa chạy: chưa có PostgreSQL/Docker |
| BGE-M3 / Qwen3 | Chưa chạy, không nằm trong mã kết nối tuần 2 này |

Đã chạy 7 tình huống API client trên bản source cuối bằng Node REPL (mock fetch; không phải kết nối backend). Đã thêm test source cho backend và frontend cùng script `backend/check_db.py` kiểm tra DB thật. Lệnh và kết quả kỳ vọng ở README. Những test chưa thực thi không được tính là PASS.

Trong môi trường thực hiện không tìm thấy Python, Node/npm, Git, Docker trên PATH. Thử tải công cụ qua mạng bị lỗi kết nối TLS; không tự thay đổi thiết lập bảo mật hệ thống. Các file nguồn không phụ thuộc đường dẫn máy tạo và có thể chạy trên máy đã cài công cụ theo README.
