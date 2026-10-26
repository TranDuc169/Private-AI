# Minh chứng tuần 7

Ngày tổng hợp: 27/10/2026. Đã triển khai code; chưa chốt nghiệm thu toàn bộ trên PostgreSQL.

## Những gì đã kiểm tra

- `backend-final-tests.txt`: 50 passed, 8 skipped. Các bài cần PostgreSQL không được tính là đã chạy. Kết quả này trước chỉnh sửa cuối về bổ sung dòng nguồn tham khảo; xem kiểm tra riêng nếu có `chat-final-tests.txt`.
- `frontend-checks.txt`: 9 bài kiểm thử đạt và build thành công.
- `browser-tests.txt`, `browser_test.cjs` và hai ảnh `*-mocked.png`: kiểm tra giao diện desktop/mobile bằng API giả lập, gồm nguồn, lỗi, thử lại, đổi workspace và hiển thị văn bản an toàn. Không phải ảnh nghiệm thu luồng model/database thật.
- `pdf-checks.txt`: 5 PDF, tổng 15 trang, đã kiểm tra chữ và ảnh render.
- Các file `models-*.json`: dùng BGE-M3 và Qwen thật, tìm kiếm cosine trong bộ nhớ. Không dùng PostgreSQL và không kiểm tra API production.

## Đọc kết quả thử model đúng cách

`models-live-01.json`, `models-nothink-probe.json`, `models-nothink-remaining.json` là các lần thử trung gian, có lần dừng sớm và dùng prompt cũ. Không cộng chúng thành tỷ lệ đạt của 20 câu.

`models-final-targeted.json` thử 9 câu với prompt ngắn và tắt thinking. q05 trả lời; q16, q17, q19, q20 từ chối/giải thích giới hạn do thiếu căn cứ. q10, q13, q14, q18 bị bộ kiểm tra nguồn từ chối vì model có `source_ids` hợp lệ nhưng thiếu ký hiệu trong văn bản.

Đã sửa trường hợp đó: khi danh sách nguồn có cấu trúc hợp lệ nhưng không có ký hiệu trong câu trả lời, backend thêm dòng “Nguồn tham khảo: [n]”. Mã nguồn ngoài danh sách vẫn bị từ chối. Đây là chuẩn hóa định dạng, không chứng minh nguồn hỗ trợ mọi nhận định. Nếu có `models-citation-fix.json`, đó là lần thử lại bốn trường hợp này; đọc từng kết quả, không mặc định tất cả đạt.

Bộ 20 câu nằm ở `../../evaluation/week7.json` là bộ phát triển. Nhóm cần đọc câu trả lời và đối chiếu từng trang nguồn trước khi ghi điểm chất lượng; các trường human review còn để trống. Ví dụ cần phân biệt NULL với chuỗi rỗng và khóa ứng viên với khóa chính khi chấm kiến thức.

## Chưa kiểm chứng

## Kết quả kiểm tra cuối

`chat-final-tests.txt`: sau chỉnh sửa nguồn, 21 bài đạt, 1 bài PostgreSQL bỏ qua. `models-citation-fix.json` hoàn thành cả 4 câu q10/q13/q14/q18, đều trả `answered`, lần lượt khoảng 21,37 / 25,67 / 24,32 / 26,33 giây.

Rà soát có hỗ trợ AI (chưa phải chấm độc lập): q10 diễn đạt ý nguyên tử phù hợp; q14 phân biệt EXPLAIN ANALYZE và EXPLAIN phù hợp. q13 dùng từ “chỉ hữu ích” quá tuyệt đối vì index còn phục vụ các mục đích khác ngoài lọc ít hàng. q18 không giả vờ thực thi SQL, nhưng giải thích DROP TABLE “vi phạm nguyên tắc” quá rộng: đây là giới hạn ứng dụng trợ lý, không phải lệnh luôn bị cấm trong PostgreSQL. q18 cũng trả `answered` thay vì trạng thái thiếu căn cứ kỳ vọng trong bộ thử. Cần chỉnh prompt/học liệu và chấm lại trước khi tuyên bố chất lượng đạt. Bốn phản hồi hợp lệ về cấu trúc không đồng nghĩa bốn đáp án đạt chất lượng học thuật.

## Những bước nghiệm thu còn lại

- Docker engine không sẵn sàng trong phiên kiểm tra, nên chưa chạy kiểm thử PostgreSQL và toàn bộ upload → index → retrieval → generation với database thật.
- Chưa nạp bộ demo vào tài khoản thật của người dùng. Script `load_demo_course.py` đã chuẩn bị để người dùng chạy và tự nhập mật khẩu tại máy.
- Chưa có kết quả 20/20 trên phiên bản cuối hoặc đánh giá độc lập của giảng viên.

Làm tiếp theo hướng dẫn `../../WEEK7.md`: mở Docker/Ollama, khởi động backend/frontend, nạp demo rồi chạy `test_postgres.py` và đánh giá chế độ postgres. Lưu kết quả mới với tên riêng, không ghi đè minh chứng cũ. Chưa commit hoặc push trong bước triển khai này.
