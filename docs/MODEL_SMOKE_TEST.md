# Chạy thử model — tuần 2

Cập nhật ngày 04/10/2026. Nguồn minh chứng: output CMD do Đức gửi trong cuộc trò chuyện; trợ lý đọc, phân tích JSON và lưu lại, không tự nhận đã chạy lại hai phép thử thành công.

## Kết quả

| Model | Đầu ra | Tổng thời gian | Nạp model | Kết luận |
|---|---|---:|---:|---|
| qwen3:4b-instruct-2507-q4_K_M | 3 câu tiếng Việt, 87 token, done_reason=stop | 9,664 s | 6,169 s | PASS chạy sinh văn bản |
| bge-m3 | 1 vector × 1024 chiều, 13 token đầu vào | 5,236 s | 5,197 s | PASS tạo embedding |

Qwen sinh 87 token trong 3,298 s. Thời gian tổng bao gồm nạp model; đây là một lần chạy, không phải benchmark tốc độ ổn định. BGE-M3 không trả riêng thời gian encode: không gọi hiệu tổng trừ thời gian nạp là thời gian encode chính xác.

Máy theo ảnh Task Manager: Intel Core i5-12450H, RAM khoảng 16 GB (15,7 GB khả dụng), NVIDIA GeForce RTX 2050; chưa xác minh dung lượng VRAM hay tỷ lệ thực thi CPU/GPU. Ollama 0.35.1 theo output người dùng. Qwen có created_at 2026-10-02T19:27:32.0866764Z (02:27:32 ngày 03/10 tại Việt Nam); phản hồi BGE-M3 không chứa timestamp nên không suy đoán giờ chạy.

## Minh chứng

- [Qwen3: phản hồi JSON](evidence/week2/qwen3-4b-instruct-result.json), chép từ output người dùng.
- [BGE-M3: phản hồi JSON](evidence/week2/bge-m3-result.json), trích nguyên JSON từ file người dùng gửi.
- [BGE-M3: lệnh và output gốc](evidence/week2/bge-m3-cmd.txt).

Kiểm tra cấu trúc: Qwen kết thúc stop, không bị cắt ở giới hạn token; BGE có đúng 1024 phần tử số hữu hạn, vector khác 0. Các kiểm tra này không đánh giá độ chính xác RAG hay chất lượng truy xuất.

Câu trả lời Qwen có diễn đạt quá mạnh rằng dữ liệu luôn mới và thay thế kiến thức đã học. Cách hiểu đúng: RAG bổ sung tài liệu truy xuất vào ngữ cảnh của model; độ mới phụ thuộc kho tài liệu và vẫn có thể trả lời sai. Giữ nguyên output làm minh chứng, không sửa câu trả lời của model.

## Chạy lại bằng CMD

Mở Ollama, đứng tại thư mục gốc repository:

```cmd
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama pull bge-m3
curl.exe --fail-with-body --max-time 120 http://localhost:11434/api/chat -H "Content-Type: application/json" --data-binary @tools/qwen3-4b-instruct-test.json
curl.exe --fail-with-body --max-time 120 http://localhost:11434/api/embed -H "Content-Type: application/json" --data-binary @tools/bge-m3-test.json
```

Hai file request chỉ dùng thử model độc lập, chưa được gọi từ FastAPI hay giao diện.

## Vấn đề đã gặp

Tag qwen3:4b đã cài trên máy báo metadata Thinking và thinking.values=[true]. Các lần yêu cầu tắt suy luận vẫn trả suy nghĩ dài rồi dừng do length. Chuyển sang tag Instruct cụ thể ở trên đã có câu trả lời hoàn chỉnh. Giữ [kết quả raw thất bại](evidence/week2/qwen3-4b-raw-result.json) và request tools/qwen3-4b-raw-test.json chỉ để tra cứu chẩn đoán; không dùng làm cấu hình chính hay minh chứng PASS.

## Việc còn lại

- Đã bổ sung output kiểm thử/build/migration và ảnh kết nối trong commit 3007e3a; xem VALIDATION.md.
- Khánh clone repository, ghi commit bằng git rev-parse HEAD, chạy theo README và xác nhận kết quả. Chưa có xác nhận; chưa gửi tin nhắn cho Khánh.
- Chưa triển khai RAG, pgvector, upload PDF hay chat AI trong ứng dụng ở bước này.
