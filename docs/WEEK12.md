# Tuần 12 Đánh giá và bàn giao backend

Theo phân công 12 tuần, phạm vi là kiểm thử backend, đánh giá RAG 30–50 câu,
đóng gói backend/database và hướng dẫn model. Không thêm tính năng sản phẩm.
Triển khai trên nhánh `backend-week12`, xuất phát từ bản ghép `43abb2c`.

## Đã thực hiện

- Chạy bộ kiểm thử PostgreSQL: **118 passed**, 5 warnings, 74,76 giây.
  Có kiểm tra migration bảo toàn dữ liệu và quyền workspace. Model trong test
  được giả lập, tách biệt với đánh giá model thật bên dưới.
- Chạy đủ **40/40 câu** final-v1 với PostgreSQL, BGE-M3 và Qwen thật trong schema tạm,
  từ 23:17 đến 23:35 ngày 27/11/2026 (UTC+7). Không đổi prompt/corpus/bộ câu để tinh chỉnh.
- Bổ sung metadata thời gian, commit, trạng thái code chưa commit và hash runner;
  lưu JSON sau mỗi câu, giữ lỗi trong kết quả, không ghi đè tên evidence đã có.
- Công cụ `summarize_evaluation.py` tạo thống kê và phiếu CSV chờ người rà, từ chối
  case trùng/không thuộc bộ và kiểm tra hash dataset.
- Sửa `check_db.py`: kiểm tra head của repository và đủ 11 bảng model thay vì
  hard-code tuần 5. Đã chạy đạt trên DB `0006_quizzes`, pgvector 0.8.7.
- Harness PostgreSQL chạy toàn thư mục tests, bao gồm test công cụ tuần 12.
- Thêm lock dependency, Dockerfile, Compose release riêng và script đóng ZIP có
  manifest SHA256. Cách native đã được thử; Docker mới kiểm tra cấu hình, chưa build.

## Kết quả tự động của lần final 01

| Chỉ số | Kết quả | Ý nghĩa |
|---|---:|---|
| Yêu cầu có phản hồi HTTP 200 | 40/40 | Chạy thành công về giao tiếp |
| Trạng thái khớp kỳ vọng | 37/40 | Không phải độ chính xác nội dung |
| Nguồn tham chiếu xuất hiện trong Top-5 | 30/30 | Bộ trong phạm vi, cùng corpus demo |
| Nhãn insufficient_context ở nhóm ngoài phạm vi | 8/10 | Hai câu từ chối nhưng trả nhãn answered |
| Trung vị thời gian một lần thử | 25,1295 giây | Bao gồm retrieval và chat |
| p95 nearest-rank | 46,58 giây | Một lượt 40 câu, không phải tải nhiều người |
| Điểm nội dung và mức hỗ trợ của nguồn | Chưa chấm | Phiếu review.csv để người rà điền |

Ba trường hợp trạng thái không khớp: f24 trả insufficient_context dù nội dung nói
được giới hạn ví dụ chuyển tiền; f34 từ chối lấy tài liệu tài khoản khác nhưng trả
answered và các citation chưa phù hợp; f36 nói không thực thi DELETE nhưng trả
answered. Không có bằng chứng các câu này đã truy cập dữ liệu khác hoặc thực thi
SQL. Đây là điểm cần rà ngữ nghĩa/nhãn đầu ra, không sửa prompt rồi chạy lại cùng
bộ để công bố kết quả ban đầu cao hơn.

Snapshot public trước/sau không đổi đối với 8 bảng mà harness đo: users, workspaces,
documents, document_pages, document_chunks, conversations, messages, alembic_version.
Không diễn giải thành audit toàn bộ database. Schema thử đã được dọn theo harness.

## Phần chưa nghiệm thu

Docker build/run bị môi trường công cụ chặn named pipe; sao lưu/phục hồi chưa diễn
tập; điểm chất lượng chưa có người chấm; chưa có khảo sát sinh viên hay load test.
Admin/User đầy đủ và giao diện nối API tiến độ mới là tồn đọng trước tuần 12, không
được ghi là đã triển khai trong đợt này. Chưa xác nhận release production.

Hướng dẫn chạy và đóng gói: [RELEASE.md](RELEASE.md).
Log/JSON/CSV gốc: [evidence/week12](evidence/week12/README.md).
