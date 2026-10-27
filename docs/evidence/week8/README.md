# Minh chứng tuần 8 — 27/10/2026

## Kết quả đã quan sát

- Backend toàn bộ chế độ mặc định: **55 passed, 8 skipped**, 22,22 giây (trước khi thêm bài kiểm tra revision đến muộn cuối cùng).
- `test_postgres.py`: **60 passed**, 39,38 giây, PostgreSQL thật trong các schema tạm; model giả lập. Bao gồm migration lên 0004, bảo toàn tài khoản/tài liệu/tin nhắn cũ và so sánh schema với ORM. Xem kết quả bổ sung cuối trong `checks.txt`.
- Frontend: **9 passed**, build thành công (49 modules).
- `browser-checks.txt`, `browser-test.cjs`, hai ảnh PNG: Chrome desktop/mobile, API giả lập. Kiểm tra reload/đăng nhập/mở lịch sử, nguồn hiện tại/xóa nguồn, phạm vi tóm tắt, đổi workspace khi phản hồi đến muộn, không tràn ngang và không lỗi JavaScript. Đã xem ảnh; không dùng ảnh giả lập làm minh chứng model thật.
- `live-01.json`: API TestClient + PostgreSQL + BGE-M3 + Qwen thật. Upload/parse/index PDF transaction, hỏi 3 câu, lưu/mở lại 6 tin nhắn, kiểm tra nguồn hiện tại. Dấu kiểm tra dữ liệu public trước/sau không đổi; schema thử đã dọn.

## Đối chiếu nhỏ từ lần chạy thật

| Câu | Kết quả | Thời gian | Rà soát có hỗ trợ AI, cần nhóm xác nhận |
|---|---|---|---|
| COMMIT và ROLLBACK khác nhau thế nào? | answered, nguồn trang 1 và 2 | 20,537 giây | Phân biệt ghi nhận/hủy phù hợp. Cách nói “hai lệnh đảm bảo nguyên tử” là diễn đạt đơn giản hóa; tính nguyên tử do cơ chế giao dịch đảm bảo. |
| Tóm tắt chủ đề transaction | answered, 2/2 đoạn trên 2 trang | 15,600 giây | Có BEGIN/COMMIT/ROLLBACK/SAVEPOINT, giao dịch ngầm và phần còn thiếu; đối chiếu được với hai trang demo. Phạm vi tài liệu nhỏ, không đại diện giáo trình đầy đủ. |
| Lịch thi môn CSDL của trường tôi ngày nào? | insufficient_context, không có nguồn giả | 25,878 giây | Đúng giới hạn bộ tài liệu: không có lịch thi. |

Không suy ra độ chính xác chung từ ba câu này. `human_review` còn pending để sinh viên/giảng viên rà độc lập. Dữ liệu trả lời và đoạn nguồn đầy đủ nằm trong JSON.

## Việc cần làm trên database sử dụng hằng ngày

Chưa áp dụng migration vào database public. Sau các bài thử thành công, lệnh đọc `alembic current` bị connection timeout hai lần. Chưa chạy upgrade public, không xóa/reset dữ liệu. Người dùng cần mở Docker, chạy `alembic upgrade head`, xác nhận `0004_chat_history`, khởi động lại backend và thử UI theo `../../WEEK8.md`.

Giữ nguyên toàn bộ minh chứng tuần 2–7. Chưa commit/push trong phiên triển khai này.
