## Tuần 10 — Quiz

POST `/workspaces/{wid}/chat` nhận “Quiz SQL JOIN” (bank) hoặc “Sinh mới quiz SQL JOIN” (draft); trả `kind: quiz`, `quiz_id`, `sources: []`. Không đưa khóa đáp án vào chat/history.

GET `/workspaces/{wid}/quizzes/{qid}` trả id, status, topic, review, related_plan, questions (chỉ question/choices), result null trước nộp. Sau nộp, result có score, total, answers, submitted_at, feedback và sources.

POST `/workspaces/{wid}/quizzes/{qid}/submit`, body `{"answers":[2,3]}`. Chỉ số lựa chọn 0–3; phải đủ số câu; strict integer, không nhận score/correct từ client. Chỉ approved mới chấm. Mỗi quiz một attempt; lặp cùng lựa chọn trả cùng kết quả, đổi lựa chọn trả 409. Unique constraint chặn nộp đồng thời. 401 chưa đăng nhập, 404 sai chủ/workspace, 422 sai input, 409 draft/đã nộp, 503 lỗi lưu. Tất cả phản hồi quiz bình thường có Cache-Control no-store. Không có API duyệt cho người học.

# Bổ sung API tuần 9

`POST /workspaces/{id}/chat` giữ body tuần 8. Response thêm kind=`roadmap`, `roadmap_id` (null khi thiếu đầu vào/nguồn/quỹ thời gian), `planning_request` (các trường đã thu thập). Khi câu trả lời trước là yêu cầu làm rõ roadmap, lượt tiếp theo có thể bổ sung các trường còn thiếu. Không nhận spec kế hoạch do client dựng; code và model tạo kế hoạch ở server.

- `GET /workspaces/{id}/plans/{plan_id}`: id, workspace_id, status (draft/confirmed), revision, spec, progress (step_key → boolean).
- `POST /workspaces/{id}/plans/{plan_id}/confirm`: body `{"revision":0}`; đổi draft thành confirmed và tăng revision.
- `PATCH /workspaces/{id}/plans/{plan_id}/steps/{step_key}`: body `{"revision":1,"done":true}`; lưu done và tăng revision. Có thể bỏ dấu bằng false.

Mọi route cần JWT/quyền workspace. 401 chưa xác thực; 404 không thuộc quyền hoặc ID/bước không tồn tại; 409 revision cũ/chưa xác nhận; 422 body sai hoặc thừa trường. Trả Cache-Control no-store. Tiến độ là tự báo cáo, không chấm điểm. Khi mở lịch sử, client dùng roadmap_id để đọc trạng thái mới nhất qua GET thay vì ghi đè tiến độ từ snapshot tin nhắn.

Spec gồm request(goal/level/sessions/minutes_per_session), curriculum_version, steps(key/title/objective/activity/prerequisites/minutes/schedule/source_ids), sources, budget_minutes, planned_minutes, assumptions, limitations. Model chỉ viết objective/activity/source_ids; cấu trúc, thứ tự và lịch do code quyết định. Kế hoạch và lượt chat cùng transaction. Không tạo kế hoạch khi model lỗi.

# Bổ sung API tuần 8

- `POST /workspaces/{id}/chat`: ngoài question, nhận `conversation_id` (UUID hoặc null) và `revision` (số nguyên >=0, mặc định 0). Hội thoại mới dùng null/0; hội thoại cũ dùng revision đọc từ API. Response thêm conversation_id, revision, kind (`answer`/`summary`), coverage (null hoặc phạm vi tóm tắt). Chỉ lưu cặp user/assistant khi xử lý thành công. 409 khi revision cũ, nguồn thay đổi hoặc đạt 50 lượt. Giữ các mã lỗi tuần 7.
- `GET /workspaces/{id}/conversations`: danh sách hội thoại workspace, Cache-Control no-store.
- `GET /workspaces/{id}/conversations/{conversation_id}`: id, workspace_id, title, revision, messages theo thứ tự; mỗi message có id, role, content, created_at, result (bản chụp ChatOut hoặc null với tin nhắn cũ/user).
- `GET /workspaces/{id}/sources/{chunk_id}`: đoạn hiện tại gồm chunk_id, document_id, filename, page_number, chunk_index, text. 404 nếu không thuộc workspace hoặc tài liệu không còn sẵn sàng.

Mọi route đều cần JWT và workspace thuộc chủ sở hữu; thiếu JWT 401, tài nguyên không thuộc quyền hoặc không tồn tại 404. Lịch sử/nguồn trả no-store. Không trả vector. Xóa PDF không xóa bản chụp nguồn đã lưu trong hội thoại.

Tóm tắt nhận diện từ khóa trong câu hỏi, không nhận mode từ client. coverage gồm topic, matched_chunks, selected_chunks, selected_pages, unavailable_documents, scan_truncated, partial, limitation. Tối đa 8 đoạn từ 3.000 đoạn quét, 2 lần gọi model; không dùng điểm cosine để xếp hạng tóm tắt. score=0 trong nguồn tóm tắt chỉ là giá trị tương thích schema, UI không trình bày nó như điểm tương đồng. Mỗi câu hỏi độc lập; lịch sử không được gửi cho model. Các mô tả tuần 7 dưới đây là hợp đồng trước khi có persistence.

# API contract v0.7

## Tuần 7 — POST /workspaces/{workspace_id}/chat

Yêu cầu JWT và workspace do tài khoản sở hữu. Body duy nhất: `{"question":"LEFT JOIN khác INNER JOIN thế nào?"}`; trim, 1–2000 ký tự, cấm trường thừa. Endpoint retrieve tuần 6 vẫn còn.

Response: `workspace_id`, `question`, `status` (`answered`, `insufficient_context`, `no_documents`), `answer`, `sources`, `model`, `elapsed_ms`. Mỗi source có toàn bộ trường RetrievalHit và `source_id` khớp ký hiệu [n] trong câu trả lời. Có thể là [1] và [3], UI không tự đánh số lại. Workspace không có đoạn ready trả no_documents, không gọi Qwen.

401: chưa đăng nhập; 404: không tồn tại/khác chủ; 422: input sai; 429: model bận (Retry-After 5); 409: nguồn bị thay đổi trong lúc sinh; 502: model trả dữ liệu/citation sai hoặc bị cắt; 503: Ollama/model/database không sẵn sàng; 504: generation timeout. Không trả traceback, credentials hoặc prompt nội bộ trong lỗi.

Không giữ transaction DB khi model chạy. Backend lọc quyền trước Top-K, chỉ gửi nguồn được chọn; kiểm tra nguồn còn tồn tại sau generation. Giới hạn 1 pipeline đồng thời/process, chỉ khởi động 1 worker cho demo. Không lưu hội thoại hoặc thực thi SQL. Citation được kiểm tra ID, chưa tự động kiểm chứng nghĩa. Cache-Control no-store trên kết quả thành công.

Nếu model có source_ids hợp lệ nhưng không chèn ký hiệu trong answer, backend thêm dòng “Nguồn tham khảo: [n]”. Đây là nguồn do model chọn, không phải xác nhận từng nhận định đúng.


## Tuần 6 — POST /workspaces/{workspace_id}/retrieve

Yêu cầu Bearer JWT và quyền sở hữu workspace (khác chủ hoặc không tồn tại: 404). Body: `{"question":"Tôi được nghỉ phép bao nhiêu ngày?","top_k":5}`. Câu hỏi được trim, dài 1–2000 ký tự; top_k nguyên 1–10, mặc định 5; trường thừa bị từ chối (422).

Kết quả: workspace_id, question, top_k, embedding_model, elapsed_ms, results. Mỗi hit: chunk_id, document_id, filename, page_number, chunk_index, start_char, end_char, text, score. Score là 1 trừ khoảng cách cosine, không phải xác suất đúng. Không trả vector. Không có nguồn hợp lệ trả results rỗng và không gọi Ollama. Lỗi embedding/database trả 503.

SQL lọc quyền, workspace, trạng thái extraction/index ready và model trước ORDER BY/LIMIT. Chưa dùng ngưỡng điểm; không có LLM hoặc ghi lịch sử trong endpoint này.


## Index và quản lý tài liệu — tuần 5

Các route này có cùng tiền tố `/workspaces/{workspace_id}/documents` và yêu cầu JWT + owner như API PDF.

| Method / suffix | Kết quả |
|---|---|
| POST /{document_id}/index | Đồng bộ; 200 DocumentOut với index_status ready/failed; 409 nếu chưa đọc chữ hoặc lượt khác đang chạy; 503 nếu lưu DB lỗi. Tài liệu ready trả lại kết quả cũ, không tạo trùng. |
| GET /{document_id}/chunks?offset=0&limit=5 | Tối đa 20 đoạn; 409 nếu chưa index ready; gồm id, document_id, chunk_index từ 0, page_number từ 1, start_char/end_char, text, embedding_model và embedding_dimensions=1024. Không trả vector thô. |
| DELETE /{document_id} | 204 khi dọn xong; 404 nếu không thuộc workspace; 409 nếu đang xử lý; 503 nếu lỗi DB/file. Xóa dây chuyền pages/chunks và file PDF gốc. |

DocumentOut bổ sung index_status (pending/processing/ready/failed), index_error, index_started_at, indexed_at, chunk_count, embedding_model. Không trả index_job_id nội bộ. Trường status=ready cũ chỉ là đọc chữ xong. Frontend hỏi lại GET danh sách mỗi 3 giây khi có processing. Lease 15 phút cho phép retry sau server crash; chưa có queue tự phục hồi.

## PDF — tuần 4

Mọi route dưới đây yêu cầu Bearer JWT và quyền sở hữu workspace. Cả document ID và workspace ID được kiểm tra cùng nhau. Tài liệu/workspace người khác và ID không tồn tại đều trả 404. Không có static URL công khai cho PDF.

| Method / path | Request | Response |
|---|---|---|
| POST /workspaces/{workspace_id}/documents | multipart/form-data, trường file | 201 DocumentOut, status=uploaded |
| GET /workspaces/{workspace_id}/documents | Không body | Danh sách DocumentOut của workspace |
| GET /workspaces/{workspace_id}/documents/{document_id} | Không body | DocumentOut |
| POST /workspaces/{workspace_id}/documents/{document_id}/process | Không body | 200 DocumentOut, status=ready hoặc failed với error_message |
| GET /workspaces/{workspace_id}/documents/{document_id}/pages | offset mặc định 0, limit mặc định 10, tối đa 20 | Danh sách page_number (từ 1) và text |

DocumentOut gồm id, workspace_id, filename, created_at, size_bytes, status, page_count (nullable), error_message (nullable). Đường dẫn storage không được trả về. PDF trùng tên được lưu thành tài liệu mới có UUID khác, không ghi đè.

Upload trả 415 nếu tên/định dạng không phải PDF, 413 nếu quá dung lượng, 422 nếu rỗng. Giới hạn mặc định 20 MiB/file và thêm 64 KiB envelope cho multipart; đếm body thật ngay cả khi không có Content-Length. Header/MIME không thay thế kiểm tra nội dung. File có header PDF nhưng hỏng cấu trúc được ghi nhận failed ở bước process.

Process đồng bộ, giới hạn 30 giây, 200 trang và 2 triệu ký tự; đọc ở subprocess. Không nhận password PDF, không OCR. Trạng thái uploaded/failed giữ nguyên trong transaction cho đến khi process kết thúc. Nếu request khác giữ khóa document, trả 409; nếu process ready đã xong, trả kết quả cũ, không tạo trang trùng. Không có durable queue. GET pages khi chưa ready trả 409. Văn bản chỉ là plain text, không giữ nguyên layout PDF.

Lỗi parser/timeout được lưu failed và thông báo an toàn, không trả stacktrace hay đường dẫn máy chủ. Lỗi lưu file/DB trả 503; lỗi ràng buộc khi workspace thay đổi trong lúc upload trả 409. File upload dở được dọn khi thất bại thông thường; việc crash/ổ đĩa lỗi có thể cần đối soát file mồ côi. API xóa tài liệu đã được bổ sung ở tuần 5; chưa có API tải file gốc.

## GET /health

Không có body, query parameter hoặc workspace ID. Dùng kiểm tra khả năng nhận request và truy vấn DB; chưa có auth vì không trả dữ liệu người dùng. Không trả connection string, mật khẩu hoặc lỗi driver.

HTTP 200, Content-Type application/json:

```json
{"status":"ok","database":"up"}
```

HTTP 503 khi không kết nối/truy vấn được PostgreSQL:

```json
{"status":"degraded","database":"down"}
```

Backend thực thi `SELECT 1` mỗi lần gọi. Có timeout kết nối, chờ pool và câu SQL; frontend hủy request sau 8 giây. Lỗi mạng/CORS hoặc hết thời gian chờ phải khác thông báo DB down. Thông tin schema được kiểm tra riêng bằng `check_db.py`.

CORS local mặc định cho `http://localhost:5173` và `http://127.0.0.1:5173`. Chưa nhận credentials. API docs tại `/docs`, OpenAPI tại `/openapi.json`.

## Tài khoản và workspace — tuần 3

Các body đều là JSON; đăng nhập không dùng OAuth2 form. Gửi Authorization: Bearer <access_token> cho /auth/me và mọi endpoint /workspaces. Token hết hạn sau 30 phút theo mặc định. Trường hợp thiếu, giả mạo hoặc hết hạn trả 401 với WWW-Authenticate: Bearer.

| Method / path | Body | Kết quả |
|---|---|---|
| POST /auth/register | email, password | 201: id, email; 409 email trùng |
| POST /auth/login | email, password | 200: access_token, token_type, expires_in (giây), user; 401 sai thông tin |
| GET /auth/me | — | 200: id, email |
| GET /workspaces | — | 200: danh sách workspace của user |
| POST /workspaces | name | 201: id, name, created_at |
| GET /workspaces/{id} | — | 200: id, name, created_at |
| PATCH /workspaces/{id} | name | 200: workspace sau đổi tên |
| DELETE /workspaces/{id} | — | 204 không body; 409 nếu còn tài liệu/hội thoại |
| GET /workspaces/{id}/documents | — | 200: danh sách id, workspace_id, filename, created_at |
| GET /workspaces/{id}/conversations | — | 200: danh sách id, workspace_id, title, created_at |

Email được chuẩn hóa chữ thường; mật khẩu dài 8–128 ký tự, tên workspace được trim và dài 1–200 ký tự. Body sai hoặc có trường ngoài schema trả 422. owner_id luôn lấy từ user đã xác thực, không nhận từ client. Workspace không tồn tại hoặc thuộc tài khoản khác cùng trả 404, không tiết lộ tài nguyên người khác. JWT chỉ chứa ID user và thông tin xác thực; không chứa mật khẩu.

Logout hiện chỉ xóa JWT và dữ liệu phiên ở frontend, chưa có endpoint thu hồi token. Đã có API upload/process PDF ở phần tuần 4 bên dưới; chưa tạo hội thoại/chat AI hoặc đọc nội dung message. Danh sách trống là phản hồi DB thật, không có dữ liệu mẫu. CORS cho GET/POST/PATCH/DELETE, Accept/Content-Type/Authorization từ hai origin local; không dùng cookie credentials.
