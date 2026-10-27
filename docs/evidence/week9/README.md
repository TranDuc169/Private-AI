# Minh chứng tuần 9 — 27/10/2026

## Kết quả thực tế

- Bộ backend đầy đủ trước chỉnh sửa schema Qwen cuối: **76 passed, 8 skipped**, 22,44 giây. Bài PostgreSQL skip không tính là đạt.
- Kiểm tra riêng planner sau sửa schema/chọn nguồn: **25 passed**, 2,75 giây. Gồm đủ 6 mục tiêu × 2 mức nền, lịch không vượt quỹ, đồ thị tiên quyết, thiếu đầu vào/nguồn, quyền đọc/xác nhận/sửa, revision cũ, lưu/reload/bỏ dấu và phản hồi model sai.
- Frontend: **9 bài đạt**, build cuối **50 modules**, 1,02 giây.
- Chrome với API giả lập: draft khóa checkbox, xác nhận, đánh dấu, reload/đăng nhập/lịch sử, bỏ dấu, mobile không tràn ngang, đổi workspace khi response cập nhật đến muộn. Xem `browser-checks.txt`, `browser-test.cjs` và hai ảnh đã kiểm tra trực quan. Ảnh giả lập không phải minh chứng nội dung model thật.
- `sqlite-models-04.json`: upload/parse/index 5 PDF; **BGE-M3 và Qwen thật**, API TestClient và **SQLite tạm trong bộ nhớ**. Ba kế hoạch hoàn tất, xác nhận/đánh dấu/đọc lại thành công; 6 tin nhắn được lưu. Bài quỹ quá ngắn trả lời không khả thi, không sinh kế hoạch.

## Ba mục tiêu lần thử cuối

| Mục tiêu | Mức nền | Quỹ | Kết quả và nguồn | Thời gian |
|---|---|---|---|---|
| SQL/JOIN | Mới bắt đầu | 4 × 45 = 180 phút | Quan hệ → SQL; PDF 01/trang 1 và PDF 02/trang 1 | 22,504 giây |
| ERD/chuẩn hóa | Đã biết cơ bản | 3 × 40 = 120 phút | ERD; PDF 03/trang 2 | 5,678 giây |
| Index | Đã biết cơ bản | 4 × 45 = 180 phút | SQL → index; PDF 02/trang 1 và PDF 05/trang 1 | 12,624 giây |

Rà soát có hỗ trợ AI: nguồn cuối khớp nhóm nội dung; hoạt động SQL mô tả viết/giải thích, không thực thi. Mục tiêu ERD có câu kết thúc thiếu chữ “NF” (“từ 1NF đến 3”), trong khi hoạt động ghi đúng 3NF. Đây là lỗi diễn đạt cần người học rà bản nháp, không tuyên bố mọi nội dung đều hoàn hảo. Một đoạn/bước không bao phủ đầy đủ đề cương. Cần nhóm/giảng viên đánh giá độc lập; trường human_review còn pending.

## Các lần thử trung gian được giữ lại

- `sqlite-models-01.json`: SQL thành công, ERD bị chặn do cấu trúc model sai; chưa hoàn tất ba mục tiêu.
- `sqlite-models-02.json`: SQL/ERD có kết quả, index bị chặn do mã bước; SQL ban đầu chọn nguồn quan hệ chưa phù hợp. Đã sửa ưu tiên tên tài liệu/tần suất từ khóa.
- `sqlite-models-03.json`: model lặp/thiếu mã bước, bị từ chối. Không lưu thành kế hoạch thành công.
- Bản cuối thay array mã bước tự do thành JSON object có các key bắt buộc đúng đề cương và source_ids giới hạn theo từng bước. Code chuyển thành danh sách đúng thứ tự, không để model quyết định tiên quyết/thời gian.

Không cộng các lần thử này thành một tỷ lệ độ chính xác. File JSON chứa plan/spec/source đầy đủ để đối chiếu.

## Chưa kiểm chứng

`test_postgres.py` và đánh giá PostgreSQL không chạy được do connection timeout. Chưa xác nhận migration 0005 trên PostgreSQL, chưa nâng schema database public, không reset dữ liệu. Kết quả PostgreSQL tuần 8 không thay cho kiểm chứng tuần 9.

Người dùng cần bật Docker, chạy `alembic upgrade head`, xác nhận `0005_study_plans`, chạy `test_postgres.py` rồi `evaluate_week9.py --mode postgres --output ...` theo `../../WEEK9.md`. Lưu kết quả với tên mới.

Chưa commit/push. Toàn bộ minh chứng tuần 7–8 được giữ nguyên.
