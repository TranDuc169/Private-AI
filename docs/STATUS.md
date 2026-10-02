# Đối chiếu hiện trạng — 02/10/2026

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

## Phần còn thiếu theo lộ trình

- Nghiệm thu tuần 2 trên máy có runtime: build, chạy frontend/backend/PostgreSQL, kiểm tra migration và ghi minh chứng. Chưa chạy thử BGE-M3/Qwen3 theo kế hoạch phần cứng.
- Tuần 3: auth/JWT, password hashing, workspace CRUD, kiểm tra ownership.
- Tuần 4–5: upload/parse PDF, trạng thái xử lý, chunks, BGE-M3, pgvector.
- Tuần 6–8: retrieval lọc workspace trước Top-K, RAG Qwen3/Ollama, citation và thiếu bằng chứng.
- Tuần 9–10: summary/checklist/roadmap/quiz trong chat chung, lưu và mở lại lịch sử theo workspace.
- Tuần 11–12: quyền Admin/User, kiểm thử tích hợp, đánh giá 30–50 câu, đóng gói, demo và báo cáo.

Hướng dẫn hoặc ảnh prototype không thay cho kiểm thử chạy thật. Không triển khai thêm toàn bộ RAG trong bước này.
