# API contract v0.2

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

## Quy ước tuần sau — chưa phải endpoint đã triển khai

Các API documents/conversations phải xác minh user sở hữu workspace và chỉ query tài nguyên trong workspace đó. Đường dẫn dự kiến `/workspaces/{workspace_id}/documents` và `/workspaces/{workspace_id}/conversations`; chi tiết chốt cùng auth ở tuần 3. Không thêm endpoint nhận câu hỏi và trả câu mẫu trong tuần 2.
