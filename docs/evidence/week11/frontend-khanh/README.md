# Minh chứng frontend Khánh — 08/11/2026

Chuẩn bị trên nhánh `frontend-khanh`, giữ các commit có sẵn và backend nguyên trạng. Không thay minh chứng tuần 1–10. Phạm vi theo [bàn giao](../../../FRONTEND_KHANH_WEEK11.md).

## Kết quả đã chạy

| Kiểm tra | Kết quả | Bản chất |
| --- | --- | --- |
| `npm test` | 14 passed, 0 skipped | Unit: HTTP/JWT, lỗi JSON, PDF status, tổng hợp tiến độ, hủy và giới hạn request |
| `npm run build` | PASS | Vite production build |
| `CHROMIUM_PATH=/usr/bin/chromium npm run test:e2e` | 3 passed | 2 browser test dùng API/DB thật ở 1440px và 390px; 1 browser test dùng fixtures API |
| `.venv/bin/python -m pytest -q` | 102 passed, 8 skipped | Lượt mặc định trước khi chạy bộ PostgreSQL |
| `.venv/bin/python test_postgres.py` | 107 passed, không skip | PostgreSQL/pgvector thật, model giả lập theo bộ test repository |
| `alembic upgrade head`, `alembic check` | PASS | Migration lên 0006, không phát hiện upgrade mới |
| `GET /health` | HTTP 200, status=ok, database=up | FastAPI truy vấn DB thật |

Log: [unit](unit.log), [build](build.log), [browser](browser.log), [PostgreSQL](postgres.log). Có warning deprecation của dependency; không có test bị vô hiệu hóa để đạt kết quả.

Browser thật kiểm: đăng ký/đăng nhập, tạo workspace, gợi ý chỉ điền câu hỏi, chat không có tài liệu/lưu hội thoại, tìm/mở lịch sử, reload rồi đăng nhập/chọn/mở lại, upload + process PDF bằng HTTP thật, xem văn bản và xóa qua UI, chuyển workspace không lẫn lịch sử/tiến độ, logout. Kiểm tra không tràn ngang, icon gợi ý không đè tiêu đề.

Browser fixtures kiểm: card nguồn tải đoạn hiện tại và lỗi 404 vẫn giữ bản chụp, xác nhận roadmap/PATCH revision, checklist, lựa chọn/nộp quiz (payload chỉ answers), kết quả, dashboard, mở lại trạng thái, 401 xóa UI riêng. Các response giả chỉ có trong `frontend/e2e`, không nằm trong ứng dụng.

## Ảnh

- [Đăng nhập desktop](login-desktop.png).
- [Chat desktop 1440px](chat-desktop.png), [chat mobile 390px](chat-mobile.png): API thật, tài khoản thử nghiệm tự sinh; không có phản hồi AI dựng sẵn.
- [Cards mobile — fixture](cards-mobile-fixture.png): dữ liệu **kiểm thử giao diện**, không phải kết quả model thật.

## Giới hạn và danh sách lỗi

- Đã sửa: icons gợi ý đè chữ trên mobile; thêm assertion hình học.
- Đã sửa: tổng hợp dùng thứ tự API thay vì thời gian mới nhất; request cùng lúc quá nhiều; progress tính cả key không còn trong spec; lỗi HTML làm mất HTTP status cần xử lý 401.
- Chưa nghiệm thu sinh câu trả lời/embedding/model thật: không có Ollama, `registry.ollama.ai` bị chính sách mạng chặn (403). Cần chạy kịch bản đầu cuối với máy model của Đức trước khi merge/nghiệm thu AI.
- Chưa khảo sát sinh viên: **0 người**, chưa có phản hồi thực tế.
- Giới hạn dashboard: tối đa 50 hội thoại mới nhất; không phải thống kê toàn bộ workspace lớn. Muốn endpoint tổng hợp mới cần thống nhất API trước.
- Script `check_db.py` backend lỗi thời (assert 0003 thay vì 0006); giữ backend nguyên trạng và dùng Alembic + test PostgreSQL để kiểm schema.

Công cụ lưu cấu hình môi trường trả lỗi không xác nhận được bản nháp. Không khẳng định cấu hình đã publish hoặc khôi phục thành công trong task mới.
