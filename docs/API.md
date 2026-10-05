# API contract v0.4

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

Lỗi parser/timeout được lưu failed và thông báo an toàn, không trả stacktrace hay đường dẫn máy chủ. Lỗi lưu file/DB trả 503; lỗi ràng buộc khi workspace thay đổi trong lúc upload trả 409. File upload dở được dọn khi thất bại thông thường; việc crash/ổ đĩa lỗi có thể cần đối soát file mồ côi. Chưa có API xóa tài liệu hoặc tải file gốc.

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
