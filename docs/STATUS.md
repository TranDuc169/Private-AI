# Đối chiếu hiện trạng — cập nhật 05/10/2026

## Tuần 5

Đã triển khai chia đoạn 1.200 ký tự/overlap 200 theo trang, gọi BGE-M3 qua Ollama, migration vector(1024), trạng thái index độc lập, retry, chi tiết đoạn và xóa tài liệu có xác nhận/cascade. Đã thử BGE-M3 thật qua UI trên SQLite tạm; PostgreSQL local chưa có extension vector tại thời điểm kiểm tra, chưa chạy migration hoặc xác minh lưu pgvector thật. Không coi SQLite hoặc SQL offline là nghiệm thu pgvector. Xem [WEEK5](WEEK5.md) và [minh chứng](evidence/week5/README.md). Chưa có RAG/tìm kiếm, chưa gắn tag week-05.

## Tuần 4

Đã triển khai upload PDF thật theo workspace, lưu file riêng bằng UUID, metadata và trạng thái, trích xuất văn bản theo trang, xem văn bản và retry trên giao diện. Có giới hạn dung lượng/trang/ký tự/thời gian; kiểm tra quyền ở mọi API. Migration 0002_pdf_documents đã chạy trên DB local, số bản ghi cũ không đổi. Chưa có OCR, chunks, embedding, pgvector hoặc RAG. Xem [WEEK4](WEEK4.md) và [minh chứng tuần 4](evidence/week4/README.md). Chưa nghiệm thu bởi người dùng/Khánh, chưa gắn tag week-04. Các phần dưới mô tả các mốc trước.

## Tuần 3

Đã triển khai đăng ký/đăng nhập Argon2 + JWT, /auth/me, workspace CRUD theo chủ sở hữu, danh sách tài liệu/hội thoại theo workspace; có giao diện thật gọi API. Không thêm migration vì schema tuần 2 đã đủ. Token chỉ giữ trong bộ nhớ; tải lại trang cần đăng nhập lại. Chưa triển khai RAG hoặc upload. Xem [hướng dẫn](WEEK3.md) và [minh chứng mới](evidence/week3/README.md). Các phần dưới giữ bối cảnh lịch sử tuần 2.

Đã đọc văn bản của `Phan_cong_12_tuan_Duc_Khanh.pdf` (7 trang) và `Bao_cao_tuan_01_RAG_rut_gon.pdf` (11 trang), đồng thời xem ảnh chat prototype trích từ báo cáo. Tài liệu là căn cứ mô tả/thiết kế; không coi danh sách công việc trong PDF là bằng chứng đã triển khai.

## Trước thay đổi

| Hạng mục | Bằng chứng và kết luận |
|---|---|
| Requirements, MVP, use case, kiến trúc, pipeline, ERD | Đã có thiết kế ban đầu trong báo cáo |
| Kế hoạch, phân công Đức/Khánh | Có lịch 12 tuần, đầu ra và điều kiện nghiệm thu |
| Prototype | Báo cáo có ảnh đăng nhập demo, Documents và chat; theo người dùng là HTML/CSS/JS dữ liệu mẫu |
| Repository | GitHub public TranDuc169/Private-AI hiển thị “This repository is empty”; chưa có source/commit để audit |
| Backend, DB, RAG thật | Báo cáo xác nhận chưa triển khai; không có source chứng minh chức năng |
| Login, chọn PDF, câu trả lời mẫu | Không tính là auth, upload/parse hay AI thật |

Ảnh chat dùng nền tối, tím, sidebar workspace/lịch sử và một ô nhập chung. Workspace Electronics trống vẫn có gợi ý liên quan tài liệu; báo cáo đã lưu ý nên ẩn hoặc đổi gợi ý. Khung tuần 2 giữ một ô chat, thể hiện chưa chọn workspace và bỏ các gợi ý/câu trả lời giả.

## Sau thay đổi

Đã có mã nguồn React/Vite/Tailwind, routing/sidebar/component, API client, FastAPI `/health`, SQLAlchemy/session factory, migration 5 bảng và hướng dẫn local. Đây là bộ mã mới tham chiếu thiết kế, chưa phải chuyển đổi source prototype vì source chưa được cung cấp. Các kiểm tra thực tế ghi ở VALIDATION.md.

Người dùng đã xác nhận chạy tích hợp thành công, test/build đạt và push GitHub. Kiểm tra trực tiếp ngày 03/10 xác nhận commit local `fcfbca1`, HEAD và bản ghi local `origin/main` trùng nhau; 4 test frontend chạy lại đạt. Chưa xác minh lại remote trực tuyến. Build/backend chưa chạy lại được trong môi trường công cụ do giới hạn quyền, API không hoạt động tại thời điểm kiểm tra lại. Không suy diễn thành lỗi ở lần chạy trước của người dùng.

## Phần còn thiếu theo lộ trình

- Qwen3 4B Instruct và BGE-M3 đã chạy thử độc lập thành công theo JSON người dùng cung cấp: Qwen trả 3 câu tiếng Việt, stop, 87 token; BGE tạo 1 vector 1024 chiều. Đã lưu output, cấu hình máy đã biết và thời gian trong [MODEL_SMOKE_TEST.md](MODEL_SMOKE_TEST.md). Chưa tích hợp model vào ứng dụng.
- Đã có log kiểm thử/build/migration và ảnh trong docs/evidence/week2 tại commit 3007e3a, tag week-02 giữ nguyên. Còn chờ Khánh clone repo và xác nhận chạy được.
- Tuần 3: đã có auth/JWT, password hashing, workspace CRUD, kiểm tra ownership; người dùng đã báo chạy thử OK, ghi nhận riêng trong minh chứng tuần 3; còn chờ Khánh chạy thử. Mốc week-03 lưu code và minh chứng hiện có.
- Tuần 4–5: upload/parse PDF, trạng thái xử lý, chunks, BGE-M3, pgvector.
- Tuần 6–8: retrieval lọc workspace trước Top-K, RAG Qwen3/Ollama, citation và thiếu bằng chứng.
- Tuần 9–10: summary/checklist/roadmap/quiz trong chat chung, lưu và mở lại lịch sử theo workspace.
- Tuần 11–12: quyền Admin/User, kiểm thử tích hợp, đánh giá 30–50 câu, đóng gói, demo và báo cáo.

Hướng dẫn hoặc ảnh prototype không thay cho kiểm thử chạy thật. Không triển khai thêm toàn bộ RAG trong bước này.
