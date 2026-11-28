# Minh chứng backend tuần 12

Kết quả chạy ngày 27/11/2026; tổng hợp ngày 28/11/2026. Bản nền 43abb2c,
nhánh backend-week12 có thay đổi chưa commit khi chạy; xem git_dirty và runner_sha256
trong JSON. Không gán kết quả này cho một commit release chưa được tạo.

- [backend-unit.log](backend-unit.log): 107 passed, 8 skipped, 1 warning; lượt
  SQLite/logic, các bài PostgreSQL không chạy trong lượt này.
- [backend-postgres.log](backend-postgres.log): 118 passed, 5 warnings; đã gồm
  ba bài test công cụ tổng hợp mới. PostgreSQL thật, model giả lập trong tests.
- [release-tools.log](release-tools.log): 4 passed trong lượt kiểm tra cuối;
  gồm ba bài tổng hợp và một bài bảo đảm ZIP loại cấu hình/dữ liệu riêng.
  Đây là lượt riêng, không cộng số bài vào 118 để báo thành một lượt PostgreSQL mới.
- [final-01.json](final-01.json): 40 câu chạy với model thật và API qua TestClient,
  upload/parse/index/retrieve/chat trong PostgreSQL schema tạm, không phải browser test.
- [summary.json](final-01-review/summary.json): chỉ số tự động.
- [review.csv](final-01-review/review.csv): câu hỏi, tham chiếu, phản hồi và nguồn;
  điểm nội dung, điểm nguồn, người rà và nhận xét để trống.

Không dùng 40 HTTP 200 hay 30/30 retrieval hit làm tỷ lệ đúng nội dung. Phân tích
ba trường hợp nhãn lệch và giới hạn trong [WEEK12.md](../../WEEK12.md).
`public_data_unchanged` chỉ so sánh 8 bảng trong public_snapshot của harness,
không bao gồm bốn bảng plan/quiz. Không có user study, video hoặc kết quả Docker build
trong bộ evidence này. Hai model có tên/digest và phiên bản Ollama được lưu trong JSON.
