# Minh chứng tuần 10 — 27/10/2026

## Kết quả đã chạy

- Backend tổng quát (SQLite/model giả): 97 passed, 8 skipped, 17.19s ở lượt đầu; skipped là những bài cần PostgreSQL.
- PostgreSQL thật trong schema tạm: 106 passed, 35.53s, gồm migration giữ dữ liệu cũ và kiểm tra metadata. Sau chỉnh bộ chọn nguồn và JSON model, chạy lại toàn bộ nhóm quiz cuối: **21 passed, 10.68s** trên PostgreSQL.
- Frontend API client: **9 passed**. Build cuối: **51 modules**, thành công trong 1.29s.
- Chrome UI dùng API giả: PASS chọn/nộp/giải thích, reload từ lịch sử, khóa draft, mobile không tràn ngang, đổi workspace bỏ kết quả đến muộn. Ảnh 01/02/03 là ảnh mock, không gọi là minh chứng model thật. Đã xem ảnh desktop/mobile để kiểm tra bố cục.
- `live-05.json`: PostgreSQL + PDF thật + BGE-M3 thật; 5 bộ quiz demo tạo được, chấm ở server, reload và mở nguồn đạt. Bài thử luôn chọn A nên điểm 1/2 hoặc 0/2 là kết quả cố ý, không phải lỗi chấm. Public data unchanged = true.
- Cũng ở live-05: Qwen thật sinh 3 câu SQL JOIN trong **66.434 giây**. JSON và trích dẫn qua kiểm tra; nộp draft bị chặn 409. Đối chiếu nội dung: câu 1 và 3 phù hợp phiếu; câu 2 có lựa chọn C/D đều có thể được hiểu đúng, giải thích khái quát WHERE quá mức. **Không duyệt bài này để chấm**, xem QUIZ_BANK_REVIEW.md.
- Sau khi các thử nghiệm tách biệt kết thúc, chủ động áp dụng migration database ứng dụng: **0003_document_vectors → 0006_quizzes**. `local-migration.json` ghi số hàng/hash của các cột cũ trước/sau; mọi giá trị cũ giữ nguyên. File này không chứa nội dung tài khoản/tài liệu.
- Không commit/push/tag. Không sửa minh chứng tuần cũ.

## Những lỗi đã ghi nhận, không che lần thử thất bại

- live-01: bộ quiz không khớp vì xuống dòng PDF; sửa so khớp khoảng trắng.
- live-02: 5 bộ demo đạt; model sinh lựa chọn sai (chép câu hỏi), còn có câu lệch chủ đề. Draft không được chấm. Thêm validator và chọn nguồn có tên khớp chủ đề.
- live-03: bộ chọn nguồn tóm tắt chỉ lấy 8 đoạn làm thiếu ngẫu nhiên đoạn ngân hàng khi nhiều trang cùng có từ SQL. Tách bộ chọn nguồn quiz: quét tối đa 3.000 đoạn đúng workspace trước khi chọn căn cứ. Thêm test 20 đoạn nhiễu.
- live-04: bộ demo đạt, Qwen bị validator từ chối HTTP 502; không lưu quiz lỗi. Đổi hợp đồng sinh nội dung sang q1/q2/q3 và lựa chọn A/B/C/D bắt buộc.
- live-05: sinh/lưu draft thành công nhưng còn lỗi ngữ nghĩa câu 2; JSON đúng không đủ để duyệt. Bộ demo cố định là bộ dùng chấm hiện tại.

Các test có cảnh báo deprecation Starlette/httpx và Alembic path_separator; không phải lỗi kiểm thử. Chưa có giao diện duyệt dành cho giảng viên hoặc thử nghiệm với sinh viên thật. Đánh giá chỉ áp dụng cho bộ demo nhỏ.
