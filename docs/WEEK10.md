# Tuần 10 — Quiz có nguồn và kết quả luyện tập

## Đã thêm những gì và vì sao?

Một ô chat vẫn dùng cho mọi yêu cầu. Nhập `Quiz SQL JOIN` để mở bộ demo 2 câu. Chọn mỗi câu một đáp án rồi nộp. Backend chấm, lưu điểm và trả giải thích cùng nguồn; mở lại Lịch sử vẫn thấy kết quả.

- `backend/app/quiz_bank.py`: 10 câu cố định (2 câu × 5 chủ đề), mỗi câu 4 lựa chọn, một đáp án và trích đoạn căn cứ. Đã đối chiếu kỹ thuật với `docs/course/corpus.json`; chưa phải giảng viên thẩm định. Chỉ dùng khi đoạn căn cứ thực sự có trong tài liệu sẵn sàng của workspace.
- `backend/app/quizzes.py`: nhận diện chủ đề, lấy nguồn, sinh bản nháp bằng Qwen, kiểm tra JSON/nguồn; API đọc và nộp bài. Điểm = số đáp án người học trùng đáp án lưu trên server, không gọi model chấm điểm.
- `backend/app/models.py`: thêm Quiz (đề, đáp án riêng, nguồn và chủ đề) và QuizAttempt (lựa chọn, điểm, thời gian nộp).
- `backend/alembic/versions/0006_quizzes.py`: tạo hai bảng mới, không sửa migration cũ, không xóa dữ liệu.
- `backend/app/chat.py`: nhận quiz ngay trong chat; lưu quiz cùng lượt hội thoại trong một giao dịch. Nếu lỗi, không lưu bài thành công giả.
- `frontend/src/QuizCard.jsx`: thẻ câu hỏi, nút Nộp bài, kết quả và nguồn. Trước nộp, API chỉ gửi câu hỏi/lựa chọn, không gửi đáp án/giải thích/trích đoạn.
- `frontend/src/PlanCard.jsx`: thêm điểm đến theo bước để liên kết từ quiz quay về đúng bước trong kế hoạch đã xác nhận gần nhất cùng chủ đề/workspace.
- `backend/tests/test_quizzes.py`: kiểm thử quyền, giấu đáp án, chấm điểm, lưu/reload, bản nháp và dữ liệu model sai.
- `backend/evaluate_week10.py`: thử PDF + BGE-M3 + Qwen thật trong schema riêng rồi xóa schema thử; không ghi quiz vào tài khoản của bạn.

Mở file nhanh: mở thư mục dự án trong VS Code, nhấn Ctrl+P và nhập tên file, ví dụ `QuizCard.jsx`. Sửa chữ/bố cục thẻ trong file này; màu/khoảng cách trong `frontend/src/styles.css`; luật chấm và quyền trong `backend/app/quizzes.py`.

## Hai loại quiz khác nhau

1. `Quiz SQL JOIN` / `Quiz transaction` / `Quiz index` / `Quiz ERD chuẩn hóa` / `Quiz quan hệ ràng buộc`: dùng bộ demo cố định đã đối chiếu. Không gọi model để bịa đáp án mới; có thể làm và chấm ngay. Hiện mỗi bài đúng 2 câu, không hỗ trợ tùy chọn số câu/độ khó.
2. `Sinh mới quiz SQL JOIN`: Qwen soạn 3 câu dựa trên tối đa 3 đoạn nguồn. Nguồn được quét trong tối đa 3.000 đoạn sẵn sàng của workspace; thiếu đoạn trong phạm vi quét thì không mở bộ demo. Khi sinh mới, ưu tiên tài liệu có tên khớp chủ đề. Backend kiểm tra 4 lựa chọn khác nhau, chỉ số đáp án, trích đoạn có thật, không lặp câu. JSON đúng không chứng minh kiến thức đúng: lưu là **bản nháp**, không cho nộp/chấm. API người học không có quyền duyệt.

Bản nháp chưa có giao diện giảng viên duyệt. Muốn đưa câu mới vào bộ chấm: người duy trì rà lại câu, 4 lựa chọn, tính duy nhất của đáp án và nguồn; sửa ngân hàng bằng commit mới và tăng phiên bản. Không đổi trực tiếp đáp án của quiz đã lưu. Bài cũ luôn giữ snapshot để điểm cũ không thay đổi. File đánh giá model có phần đáp án riêng chỉ để nhóm phát triển rà soát, không phải payload gửi tới trình duyệt người học.

Mỗi quiz chỉ có một lần nộp chính thức. Gửi lại đúng lựa chọn trả cùng kết quả; đổi lựa chọn sau nộp trả 409. Muốn làm lại, yêu cầu quiz mới. Checklist không tự được đánh dấu khi đạt điểm quiz. Nếu chưa có kế hoạch đã xác nhận cùng chủ đề thì không hiện link quay lại bước học.

## Cách chạy bằng CMD hoặc Terminal của VS Code

Mở Docker Desktop và Ollama. Nếu backend đang chạy, nhấn Ctrl+C trong cửa sổ backend trước khi nâng cấp database.

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2"
docker compose up -d --wait db
cd backend
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m alembic current
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Giải thích từng lệnh:

- `cd /d "..."`: chuyển vào thư mục gốc dự án, kể cả khi đang ở ổ đĩa khác.
- `docker compose up -d --wait db`: bật database từ compose.yaml; `-d` chạy nền, `--wait` chờ database khỏe.
- `cd backend`: chuyển vào nơi chứa API, cấu hình Alembic và môi trường Python.
- `.venv\Scripts\python.exe`: dùng Python và thư viện riêng của dự án, tránh nhầm Python hệ thống.
- `-m alembic upgrade head`: chạy những migration chưa áp dụng tới bản mới nhất. Nếu đã ở head thì không tạo lại bảng.
- `-m alembic current`: xem phiên bản hiện tại; tuần 10 cần **0006_quizzes (head)**. Nếu lỗi thì xử lý lỗi trước, không xóa volume.
- `-m uvicorn ...`: khởi động FastAPI. `--factory` gọi hàm tạo app; `--reload` tự nạp lại khi sửa code; `--host 127.0.0.1 --port 8000` chỉ phục vụ trên máy tại cổng 8000. Giữ cửa sổ này mở.

Mở Terminal CMD thứ hai:

```cmd
cd /d "C:\Users\Admin\Documents\Codex\2026-10-02\t-i-ti-p-t-c\outputs\private-ai-week2\frontend"
npm.cmd run dev -- --port 5173 --strictPort
```

`npm.cmd run dev` chạy Vite để phục vụ React. Phần sau `--` truyền cho Vite: dùng cổng 5173, báo lỗi nếu cổng đang bận thay vì tự đổi cổng gây sai CORS. Mở http://127.0.0.1:5173 và http://127.0.0.1:8000/health. Tuần này không thêm dependency, không cần cài lại npm/pip.

## Bạn tự kiểm tra gì?

1. Đăng nhập, chọn workspace chứa 5 PDF mẫu đã tạo vector. Gửi `Quiz SQL JOIN`.
2. Chưa chọn hết → nút Nộp bài bị khóa. Trước nộp không có giải thích/nguồn của quiz. Chọn hai câu rồi nộp → thấy điểm, đáp án, giải thích và mở được nguồn.
3. Reload trang, đăng nhập nếu cần, chọn đúng workspace và mở hội thoại trong Lịch sử → điểm và đáp án đã chọn vẫn còn.
4. Đổi workspace/tài khoản → không thấy quiz trước. Thử quiz ở workspace chưa có tài liệu → báo thiếu nguồn.
5. Gửi `Sinh mới quiz SQL JOIN` → bản nháp chưa cho chấm, hoặc lỗi model rõ ràng, không báo thành công giả.
6. Nếu có roadmap SQL đã xác nhận, mở quiz SQL mới → có liên kết quay lại bước SQL. Quiz không tự xác nhận kế hoạch hay hoàn thành checklist.

## Lệnh kiểm thử

Trong backend:

```cmd
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe test_postgres.py
.venv\Scripts\python.exe evaluate_week10.py --mode postgres --output ..\docs\evidence\week10\user-live-01.json
```

Lệnh 1 chạy bộ kiểm thử logic (một số bài PostgreSQL bị skip). Lệnh 2 tạo schema riêng để chạy PostgreSQL thật và thử migration giữ dữ liệu cũ, rồi dọn schema. Lệnh 3 upload/index 5 PDF mẫu trong schema riêng, thử quiz 5 chủ đề, lưu/mở kết quả, rồi thử một bản nháp Qwen; có thể mất vài phút. Không ghi kết quả vào tài khoản thật. Output có sẵn sẽ không ghi đè; đổi 01 thành 02 nếu chạy lại.

Trong frontend: `npm.cmd test` kiểm tra API client; `npm.cmd run build` kiểm tra đóng gói React. Xem số passed/failed và phân biệt skipped với passed.

## Giới hạn

Bộ demo nhỏ và có thể lặp lại câu. Nguồn đúng không tự bảo đảm AI sinh câu hỏi hay/đúng, nên câu sinh mới không tự được duyệt. Không có chấm tự luận, thực thi SQL, thống kê nhiều lượt hay chứng nhận năng lực. Nguồn lưu snapshot; nếu PDF bị xóa, kết quả cũ vẫn đọc được, nút lấy nguồn hiện tại sẽ báo không còn nguồn. Minh chứng kiểm thử ở `docs/evidence/week10/`, không ghi đè tuần trước. Code chưa tự commit/push.

Ghi nhận bàn giao 27/10/2026: database ứng dụng trên máy đã được nâng từ 0003 lên **0006_quizzes**, đối chiếu các cột cũ không thay đổi. Các lệnh migration ở trên vẫn dùng để kiểm tra hoặc cài trên máy khác. Với máy này bạn chỉ cần bật lại backend/frontend rồi thử quiz. Xem [minh chứng](evidence/week10/README.md) cho số liệu và lỗi model đã tìm thấy.
