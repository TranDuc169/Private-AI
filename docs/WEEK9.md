# Tuần 9 — Roadmap và checklist lưu tiến độ

## Bạn sẽ thấy gì mới?

Nhập trong Chat chung:

> Lập roadmap học SQL JOIN; nền tảng: mới bắt đầu; 4 buổi; 45 phút/buổi.

Hệ thống tạo **bản nháp** với từng bước học, mục tiêu, hoạt động, thời gian và nguồn PDF. Đọc xong, bấm **Xác nhận kế hoạch này**. Các ô checklist mới được bật. Đánh dấu rồi mở lại hội thoại trong Lịch sử: tiến độ vẫn còn.

Nếu thiếu mục tiêu/mức nền/số buổi/phút mỗi buổi, ứng dụng hỏi phần thiếu. Bạn có thể bổ sung ngay trong cùng hội thoại, ví dụ `mới bắt đầu; 4 buổi; 45 phút/buổi`. Luồng này giữ các trường kế hoạch đã thu thập; không phải model được cấp toàn bộ lịch sử chat. Không có bộ chọn tác vụ riêng.

## Hiểu cách hệ thống làm việc

1. Backend đọc yêu cầu bằng quy tắc từ khóa, lấy mục tiêu, mức nền và thời gian. Đây là bộ nhận diện đơn giản, chưa hiểu mọi cách diễn đạt.
2. Đề cương cố định xác định thứ tự học: quan hệ/ràng buộc → SQL/JOIN → transaction hoặc index; ERD/chuẩn hóa cần quan hệ/ràng buộc. Mục tiêu toàn bộ gồm cả 5 nhóm.
3. Người khai `đã biết cơ bản` được giả định đã học phần quan hệ/ràng buộc khi nó là tiên quyết. Đây là tự khai, chưa phải kết quả kiểm tra trình độ.
4. Code tính quỹ thời gian bằng số buổi × phút/buổi. Mỗi bước có định mức demo tối thiểu 20, tối đa 60 phút. Thiếu quỹ thì báo không khả thi; không yêu cầu Qwen bịa lịch để vừa thời gian. Thời gian dư chưa phân bổ hiển thị qua tổng đã phân bổ/quỹ.
5. Backend lấy một đoạn khớp chủ đề cho mỗi bước, ưu tiên tên tài liệu và tần suất từ khóa, từ tài liệu đã sẵn sàng trong workspace. Qwen viết mục tiêu và hoạt động bằng JSON object có key bắt buộc cho từng bước; mã bước/số bước/mã nguồn đều bị kiểm tra. Qwen không được đổi thời lượng hay cấu trúc tiên quyết.
6. Backend kiểm tra nguồn vẫn tồn tại, rồi lưu kế hoạch nháp cùng lượt chat. Bạn xác nhận riêng trước khi đánh dấu tiến độ. Khi mở lại, frontend lấy trạng thái mới nhất của kế hoạch từ API thay vì dùng trạng thái cũ trong tin nhắn.

Ví dụ 4 × 45 = 180 phút cho SQL từ đầu: gồm quan hệ và SQL, mỗi bước tối đa 60 phút, tổng phân bổ 120 phút. Có thể chia bước qua hai buổi; mỗi buổi vẫn tối đa 45 phút. 60 phút còn lại là quỹ chưa phân bổ, không bị giả vờ tính thành thời gian đã học.

## Những file đã thêm/sửa

Mở VS Code, Ctrl+P rồi gõ tên file trong bảng.

| File | Dùng để làm gì? |
|---|---|
| `backend/app/planning.py` | Nhận yêu cầu, đề cương tiên quyết, tính lịch, chọn nguồn và yêu cầu Qwen trả JSON hợp lệ. |
| `backend/app/plans.py` | API đọc kế hoạch, xác nhận và cập nhật checklist; kiểm tra quyền và phiên bản. |
| `backend/app/models.py` | Mô tả bảng StudyPlan/StudyStep bằng SQLAlchemy. |
| `backend/alembic/versions/0005_study_plans.py` | Tạo hai bảng mới, giữ bảng/dữ liệu cũ. |
| `backend/app/chat.py` | Nhận yêu cầu roadmap trong ô chat, lưu bản nháp và liên kết với lịch sử. |
| `frontend/src/PlanCard.jsx` | Thẻ lộ trình, lịch từng bước, nguồn, nút xác nhận và checkbox. |
| `frontend/src/Chat.jsx`, `styles.css` | Gắn thẻ kế hoạch vào câu trả lời, bố cục desktop/mobile. |
| `backend/tests/test_plans.py` | Kiểm tra thời gian, tiên quyết, thiếu nguồn, quyền và lưu/reload tiến độ. |
| `backend/evaluate_week9.py` | Thử 3 mục tiêu với model thật, xác nhận/đánh dấu/đọc lại; chọn PostgreSQL hoặc SQLite tạm. |

`study_plans.spec` lưu bản JSON của kế hoạch và nguồn. `study_steps.done` lưu từng dấu hoàn thành. `revision` là số phiên bản kế hoạch: nếu tab khác đã sửa trước, backend trả 409, bạn bấm Tải lại kế hoạch. Phiên bản kế hoạch độc lập với phiên bản hội thoại.

## Cập nhật database trước khi chạy

Mở Docker Desktop và Ollama. Nếu backend đang chạy, Ctrl+C để dừng. Mở CMD và chạy:

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2"
docker compose up -d --wait db
cd backend
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m alembic current
```

- `cd /d`: vào đúng thư mục, kể cả khi khác ổ đĩa.
- `docker compose ...`: bật PostgreSQL, chạy nền và chờ healthy.
- `cd backend`: vào nơi chứa môi trường Python/backend.
- `alembic upgrade head`: cập nhật database theo các migration chưa chạy. Nếu đang ở tuần 7, nó chạy lần lượt 0004 rồi 0005; không cần chạy từng file tay.
- `alembic current`: cần hiện **0005_study_plans (head)**. Nếu có lỗi, dừng tại đây và đọc lỗi, không xóa volume database.

Sau khi migration thành công:

```cmd
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Lệnh bật API, giữ terminal mở. `--reload` tự nạp code khi lưu file, nhưng không tự chạy migration.

Terminal CMD khác:

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\frontend"
npm.cmd run dev -- --port 5173 --strictPort
```

Lệnh bật giao diện tại http://127.0.0.1:5173. Không cần cài dependency mới. Đăng nhập, chọn workspace có đủ bộ PDF CSDL đã index. Nếu thiếu nguồn cho bước tiên quyết, backend yêu cầu bổ sung tài liệu thay vì tạo bước không có nguồn.

## Các bài thử bạn nên thực hiện

1. `Lập roadmap SQL JOIN` → hỏi bổ sung mức nền và thời gian. Gửi tiếp `mới bắt đầu; 4 buổi; 45 phút/buổi` → tạo bản nháp.
2. `Lập roadmap ERD chuẩn hóa; đã biết cơ bản; 3 buổi; 40 phút/buổi`.
3. `Lập roadmap index; đã biết cơ bản; 4 buổi; 45 phút/buổi`.
4. `Lập roadmap SQL; mới bắt đầu; 1 buổi; 15 phút/buổi` → báo quỹ quá ngắn, không lưu kế hoạch giả.
5. Trước xác nhận, checkbox bị khóa. Sau xác nhận, đánh dấu một bước; reload, đăng nhập, chọn đúng workspace và mở hội thoại từ Lịch sử → dấu vẫn còn. Bỏ đánh dấu rồi mở lại để kiểm tra lần nữa.
6. Đổi workspace hoặc tài khoản → không thấy dữ liệu của nơi trước. Mở nguồn trong từng bước để đối chiếu tính phù hợp, không chỉ nhìn có số trích dẫn.

Mẫu nhập hiện hỗ trợ số nguyên 1–30 buổi và 15–180 phút/buổi. Dùng đúng cụm `mới bắt đầu` hoặc `đã biết cơ bản`. Mục tiêu có thể là SQL/JOIN, ERD/chuẩn hóa, transaction, index, quan hệ/ràng buộc hoặc toàn bộ CSDL. Chưa hỗ trợ hạn chót theo ngày, nhiều môn, hoặc câu mô tả mức nền tùy ý.

## Kiểm thử tự động

Trong thư mục backend:

```cmd
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe test_postgres.py
.venv\Scripts\python.exe evaluate_week9.py --mode postgres --output ..\docs\evidence\week9\postgres-user-01.json
```

Lệnh đầu kiểm tra logic, một số bài database sẽ skip. Lệnh hai chạy bộ PostgreSQL thật và kiểm tra migration trong schema tạm; model giả lập. Lệnh ba dùng PDF, BGE-M3 và Qwen thật, tạo 3 kế hoạch qua API TestClient, xác nhận/đánh dấu/đọc lại rồi dọn schema. Nó không thêm kế hoạch vào tài khoản thật của bạn và có thể mất vài phút.

Nếu chỉ muốn thử model và API khi PostgreSQL chưa chạy:

```cmd
.venv\Scripts\python.exe evaluate_week9.py --mode sqlite --output ..\docs\evidence\week9\sqlite-user-01.json
```

SQLite là database tạm trong bộ nhớ cho bài thử này; **không thay PostgreSQL của ứng dụng** và không xác nhận migration PostgreSQL đã đạt. File output có sẵn sẽ bị từ chối ghi đè, hãy đổi số 01 thành 02 ở lần sau.

Frontend: `npm.cmd test` kiểm tra API client; `npm.cmd run build` kiểm tra đóng gói giao diện. Các bài đều cần đọc kết quả, không coi skipped hay timeout là passed.

## Giới hạn cần hiểu

- Checklist chỉ là người học tự đánh dấu, không phải điểm số hay chứng nhận thành thạo. Có thể bỏ dấu; không khóa đánh dấu bước sau theo bước trước.
- Đề cương và định mức thời gian là cấu hình demo của nhóm, cần giảng viên rà soát. Mỗi bước chỉ dùng một đoạn nguồn, chưa đủ thay giáo trình.
- Model có thể sinh mục tiêu/hoạt động chưa tốt dù JSON hợp lệ; người học đọc bản nháp và nguồn trước khi xác nhận. Lỗi schema/timeout không được lưu thành kế hoạch thành công.
- Chưa có sửa trực tiếp/xóa kế hoạch, dời lịch theo ngày hoặc quiz. Muốn lịch khác thì gửi yêu cầu mới để tạo bản nháp mới, giữ kế hoạch cũ trong lịch sử.
- Cả tuần 8 và tuần 9 đang là thay đổi chưa commit trong cùng repository. Không tự commit/push hoặc sửa lịch sử Git. Minh chứng các tuần cũ giữ nguyên.

Kết quả đã chạy và phần chưa kiểm chứng: [evidence/week9/README.md](evidence/week9/README.md).
