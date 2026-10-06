# Minh chứng tuần 6

Baseline: `f5c8564`. Hoàn tất tài liệu ngày 06/10/2026. Minh chứng tuần 2–5 giữ nguyên.

| Minh chứng | Kết quả |
|---|---|
| postgres-tests-01.txt | 33 test pass trên PostgreSQL/pgvector; gồm lọc workspace trước Top-K, quyền, lỗi và xóa tài liệu. |
| backend-tests.txt | 29 pass, 7 skip cần PostgreSQL trong lần chạy bộ mặc định. |
| frontend-tests.txt | 9 test API/status pass. Không coi đây là unit test đầy đủ của Chat. |
| frontend-build.txt | Vite production build pass. Dùng configLoader runner để chạy trong môi trường công cụ. |
| evaluation-live-01.json | BGE-M3 + pgvector thật: 6/6 câu có nguồn đúng Top-1; hit@1/hit@3/MRR@3 = 1 trên bộ mẫu nhỏ. Một câu ngoài tài liệu vẫn trả đoạn gần nhất. |
| browser-tests.txt | Edge với API/PG/BGE thật: upload/index PDF, hỏi tiếng Việt, nguồn đúng trang, mobile không tràn ngang. Thử lỗi 503 bằng mô phỏng; thử đổi workspace khi đang chờ và không hiện kết quả cũ. |
| browser-public-isolation.txt | Hash các bảng public không đổi; schema riêng dùng kiểm thử UI đã dọn. |
| 01-retrieval-sources.png, 02-mobile-retrieval.png | Ảnh màn hình nguồn truy xuất desktop/mobile, đã kiểm tra trực quan. |

Đánh giá dùng tài liệu tổng hợp, không phải PDF của người dùng. Test DB dùng schema riêng và tạo bảng với checkfirst=False trong schema mới để tránh nhầm bảng public. Công cụ đánh giá tự xóa schema sau khi chạy. Không suy rộng kết quả 6 câu thành độ chính xác trên mọi tài liệu.

Chưa có sinh câu trả lời bằng Qwen, ngưỡng từ chối câu ngoài tài liệu, reranker hoặc lưu lịch sử truy xuất. Chưa push/tag tuần 6; để người dùng tự kiểm tra và thực hành Git.

Chạy lại theo [WEEK6.md](../../WEEK6.md).
