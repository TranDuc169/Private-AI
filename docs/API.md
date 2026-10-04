# API contract v0.3

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

Logout hiện chỉ xóa JWT và dữ liệu phiên ở frontend, chưa có endpoint thu hồi token. Chưa có API upload, tạo hội thoại/chat AI hoặc đọc nội dung message. Danh sách trống là phản hồi DB thật, không có dữ liệu mẫu. CORS cho GET/POST/PATCH/DELETE, Accept/Content-Type/Authorization từ hai origin local; không dùng cookie credentials.
