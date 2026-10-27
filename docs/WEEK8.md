# Tuần 8 — Nguồn, lịch sử và tóm tắt chủ đề

## Thay đổi bạn nhìn thấy

1. Gửi câu hỏi xong, ứng dụng lưu cả câu hỏi, câu trả lời và các nguồn vào PostgreSQL. Vào **Lịch sử hội thoại** để mở lại. Reload vẫn cần đăng nhập lại vì JWT chỉ giữ trong bộ nhớ; lịch sử không bị mất.
2. Trong thẻ nguồn có **bản trích đã lưu** và nút **Mở đoạn nguồn hiện tại**. Nếu PDF đã bị xóa hoặc tạo vector lại, nguồn hiện tại trả lỗi rõ ràng; bản trích cũ vẫn giữ cùng hội thoại.
3. Gõ **Tóm tắt chủ đề transaction** ngay trong ô chat. Không có bộ chọn tác vụ. Khi chưa rõ chủ đề hoặc nêu nhiều chủ đề, backend hỏi làm rõ.
4. Tóm tắt có thông tin số đoạn/trang đã xét, tài liệu chưa sẵn sàng và giới hạn phạm vi. Nó không tự nhận là bao phủ toàn bộ môn học.

## Code nằm ở đâu và vì sao cần nó?

Các đường dẫn dưới đây tính từ thư mục gốc dự án. Trong VS Code nhấn Ctrl+P và gõ tên file để mở.

| File | Việc thực hiện | Lý do |
|---|---|---|
| `backend/app/models.py` | Thêm revision vào Conversation; position và payload vào Message | Xếp thứ tự lượt, phát hiện phiên hội thoại cũ, lưu nguồn và phạm vi tóm tắt cùng câu trả lời. |
| `backend/alembic/versions/0004_chat_history.py` | Thêm các cột bằng migration mới | Python đổi model chưa tự đổi bảng PostgreSQL; migration nâng bảng mà không xóa nội dung cũ. |
| `backend/app/chat.py` | Nhận conversation_id/revision, chọn hỏi đáp hay tóm tắt, lưu cặp tin nhắn trong một transaction | Không lưu câu hỏi dở dang khi model lỗi; không ghi tiếp lên hội thoại đã đổi ở tab khác. |
| `backend/app/history.py` | API mở hội thoại và đọc nguồn hiện tại | Luôn kiểm tra workspace thuộc tài khoản đang đăng nhập; không tin ID do frontend gửi. |
| `backend/app/summaries.py` | Nhận diện 5 chủ đề, gom đoạn theo từ khóa, chọn trải theo trang, chia nhóm gọi Qwen | Tóm tắt không chỉ dùng Top-K của một vector câu hỏi. |
| `frontend/src/History.jsx` | Danh sách và đường dẫn mở hội thoại | Người dùng tìm lại nội dung sau reload. |
| `frontend/src/Chat.jsx` | Tải lịch sử, gửi tiếp, trình bày phạm vi tóm tắt | Một ô nhập chung; phản hồi đến muộn không lẫn workspace mới. |
| `frontend/src/SourceCard.jsx` | Hiện bản chụp nguồn và lấy đoạn hiện tại qua API | Phân biệt lịch sử với trạng thái hiện tại của PDF. |
| `frontend/src/App.jsx` | Đường dẫn `/chat/:conversationId`, trang lịch sử và reset khi đổi workspace | Mỗi workspace có trạng thái giao diện riêng. |
| `backend/tests/test_history_summary.py` | Kiểm tra quyền, lưu/mở, lỗi, revision, nguồn bị xóa và chọn đoạn tóm tắt | Kiểm chứng các hành vi dễ sai, không chỉ nhìn giao diện. |
| `backend/evaluate_week8.py` | Thử nhỏ với PDF, PostgreSQL, BGE-M3 và Qwen thật trong schema tạm | Tách kiểm thử model thật khỏi kiểm thử giả lập; không nạp dữ liệu demo vào tài khoản thật. |

`revision` là số phiên bản hội thoại: lượt đầu tạo revision 1, lượt tiếp theo lên 2. Client gửi số mình đang xem; nếu database đã đổi, backend báo 409 và yêu cầu mở lại. Cặp tin nhắn được commit cùng nhau; một lỗi không được ghi thành câu trả lời thành công.

## Tóm tắt hoạt động như thế nào?

Nhận dạng cụm “tóm tắt”, “tổng hợp”, “summary”, “summarize”, bỏ dấu để nhận cả tiếng Việt không dấu. Tìm đúng một trong 5 nhóm chủ đề: quan hệ/ràng buộc, SQL/JOIN, ERD/chuẩn hóa, transaction, index/EXPLAIN.

Backend chỉ đọc đoạn đã index sẵn sàng, đúng workspace/chủ sở hữu và model embedding. Nó quét tối đa 3.000 đoạn, tìm đoạn khớp từ khóa chủ đề rồi chọn tối đa 8 đoạn, trải qua các nhóm tài liệu/trang. Nếu có nhiều trang, lấy mẫu trải đều; không khẳng định đã đọc hết. Qwen xử lý mỗi nhóm tối đa 4 đoạn; backend ghép phần tóm tắt và đổi số trích dẫn về danh sách chung.

Đây là phương pháp demo có giới hạn: từ đồng nghĩa ngoài danh sách có thể bị bỏ sót, tài liệu dùng từ khóa chồng lấn có thể được chọn rộng, các nhóm có thể lặp ý. `partial=false` chỉ nghĩa đã dùng các đoạn khớp trong phạm vi quét, không phải đầy đủ mọi kiến thức. Số tài liệu chưa sẵn sàng là của workspace, không khẳng định chúng thuộc chủ đề đang hỏi. Không có ngưỡng độ tin cậy đã hiệu chỉnh; AI vẫn có thể sai, cần đối chiếu nguồn.

## Cách chạy sau cập nhật

Mở Docker Desktop và Ollama. Dùng CMD, tại thư mục gốc:

```cmd
docker compose up -d --wait db
```

Lệnh bật database nền và chờ healthy. Dừng backend cũ bằng Ctrl+C rồi chạy trong thư mục `backend`:

```cmd
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m alembic current
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

- Python trong `.venv` dùng thư viện của dự án.
- `alembic upgrade head`: nâng cấu trúc bảng lên phiên bản mới nhất. Không phải xóa/tạo lại database.
- `alembic current`: cần thấy `0004_chat_history (head)`. Nếu migration lỗi thì sửa lỗi trước, không tiếp tục chạy server với schema cũ.
- `uvicorn`: mở API tại cổng 8000; `--reload` nạp lại khi sửa code, không tự chạy migration.

Terminal mới trong `frontend`:

```cmd
npm.cmd run dev -- --port 5173 --strictPort
```

Lệnh chạy giao diện trên cổng 5173; strictPort báo lỗi khi cổng bận thay vì đổi cổng gây nhầm CORS. Mở http://127.0.0.1:5173. Không cần cài thêm dependency cho tuần 8.

Nếu quên cách vào thư mục hoặc mở terminal: [hướng dẫn từ đầu](../HUONG_DAN_CHAY.md), đặc biệt mục 10.

## Bạn cần thử gì trên giao diện?

| Thao tác | Kết quả cần thấy |
|---|---|
| Chọn workspace có PDF transaction đã index, hỏi COMMIT và ROLLBACK khác nhau thế nào | Câu trả lời có thẻ nguồn đúng tài liệu/trang. |
| Mở nguồn hiện tại | Đúng đoạn; không lấy tài liệu workspace khác. |
| Gửi “Tóm tắt chủ đề transaction” | Các ý tóm tắt, nguồn và phạm vi/giới hạn. |
| Gửi “Tóm tắt giúp tôi” | Hỏi rõ chủ đề, không tự bịa phạm vi. |
| Hỏi lịch thi của trường | Nêu thiếu căn cứ nếu PDF không chứa lịch thi. |
| Reload, đăng nhập, chọn lại workspace, vào Lịch sử | Mở được câu hỏi/câu trả lời và nguồn cũ. |
| Đổi workspace khi đang chờ | Không thấy câu trả lời workspace trước xuất hiện ở workspace mới. |
| Dùng tài khoản khác | Không xem được hội thoại hoặc nguồn của tài khoản ban đầu. |

Không cần xóa PDF thật để thử lỗi nguồn; bài kiểm thử tự động đã kiểm tra tình huống này trong dữ liệu tạm. Trong lịch sử, bản chụp nguồn vẫn còn sau khi PDF bị xóa — xóa PDF không đồng nghĩa xóa nội dung đã lưu trong hội thoại.

## Các lệnh kiểm thử

Trong backend:

```cmd
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe test_postgres.py
.venv\Scripts\python.exe evaluate_week8.py --output ..\docs\evidence\week8\live-user-01.json
```

Lệnh 1 kiểm tra logic; các bài cần PostgreSQL bỏ qua nếu chưa cấu hình chế độ đó. Lệnh 2 dùng PostgreSQL thật nhưng giả lập model, kiểm tra cả migration trong schema riêng. Lệnh 3 upload một PDF transaction, trích chữ/index, hỏi 3 câu qua API TestClient với model thật, kiểm tra lưu/mở và nguồn, rồi dọn schema tạm. Không phải chạy trình duyệt thật. Có thể mất vài phút; nếu file output đã tồn tại, đổi tên `02` để giữ minh chứng cũ. Tránh vừa sửa dữ liệu thật vừa chạy đánh giá vì công cụ so sánh dấu kiểm tra dữ liệu public trước/sau.

Trong frontend: `npm.cmd test` kiểm tra API client; `npm.cmd run build` kiểm tra đóng gói giao diện. Build đạt không thay thế kiểm tra luồng thật.

## Giới hạn và bàn giao

- Tối đa 50 lượt mỗi hội thoại mới. Hội thoại cũ từ trước migration giữ nguyên văn bản; có thể chưa có nguồn.
- Lưu lịch sử không có nghĩa model nhớ ngữ cảnh: mỗi yêu cầu vẫn độc lập. Viết đầy đủ chủ đề trong câu tiếp theo.
- Dừng chờ trên trình duyệt không bảo đảm dừng backend; server có thể vẫn lưu. Kiểm tra Lịch sử trước khi gửi lại. Chưa có khóa chống trùng cho retry tạo hội thoại mới.
- Chưa có đổi tên/xóa hội thoại, roadmap, checklist hay quiz; không gắn số tuần lên giao diện sản phẩm.
- Chưa tự commit/push/tag. Minh chứng các tuần cũ được giữ nguyên.

Xem [kết quả kiểm thử thực tế](evidence/week8/README.md).
