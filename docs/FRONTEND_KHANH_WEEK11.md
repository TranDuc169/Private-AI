# Frontend Khánh — tuần 11

Nhánh `frontend-khanh` được tách từ `main`, không thay đổi backend hay migration.

## Tích hợp hiện tại

- Giữ toàn bộ React/Vite và luồng **Chat chung**, upload/index PDF, **Lịch sử**, **roadmap/checklist**, và **quiz** hiện có.
- Thêm trang **Tiến độ học tập** ở `/progress`. Dữ liệu từ các API hiện có: `GET /workspaces/{wid}/conversations`, `GET /workspaces/{wid}/conversations/{cid}`, `GET /workspaces/{wid}/plans/{pid}`, `GET /workspaces/{wid}/quizzes/{qid}`.
- Sử dụng `apiRequest` hiện hành, có Bearer JWT, `cache: no-store` và AbortController; đổi workspace hủy request cũ.
- Phân biệt checklist tự báo cáo, điểm quiz đã nộp, bản nháp chưa duyệt. Không biến cosine score thành độ tin cậy và không tạo dữ liệu mẫu.
- Trạng thái đang tải / trống / lỗi / thiếu một phần, hỗ trợ thử lại.
- Dữ liệu tổng hợp bị giới hạn **50 hội thoại cuối trong danh sách API** vì backend chưa cung cấp endpoint thống kê có phân trang; UI nêu giới hạn rõ. Không có yêu cầu đổi backend.

## Kiểm tra

```bash
cd frontend
npm ci
npm test
npm run build
npm run dev
```

Chạy backend/PostgreSQL/Ollama theo `HUONG_DAN_CHAY.md`, truy cập `http://127.0.0.1:5173`. Đăng nhập và chọn workspace có hội thoại thật, tạo roadmap, xác nhận rồi đánh dấu một bước; tạo quiz demo, nộp bài; mở Tiến độ để kiểm tra số liệu. Đổi sang workspace khác phải thấy số liệu của workspace đó; đăng xuất phải xóa quyền xem. Kiểm tra mobile 375px và trạng thái API lỗi.

## Hạn chế / đề nghị thống nhất với Đức

API hiện chỉ liệt kê hội thoại và tra cứu từng kế hoạch/quiz theo ID, chưa có endpoint thống kê tổng hợp (hay liệt kê mọi plan/quiz). Trang tiến độ đọc tuần tự qua lịch sử trong phạm vi 50 hội thoại; với dữ liệu lớn, nên thống nhất API thống kê có cursor trước khi phát triển dashboard toàn cục. Không tự thêm endpoint backend.

## Phạm vi Pull Request

PR chỉ bổ sung frontend và tài liệu. Bản `main` đang chạy vẫn được giữ nguyên để Đức/Khánh cùng review rồi mới merge.
