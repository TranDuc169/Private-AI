# Bộ quiz demo v1 và biên bản đối chiếu kỹ thuật

Đối chiếu kỹ thuật với phiếu học tập csdl-demo-v1; chưa có giảng viên thẩm định.

Đây là tài liệu cho nhóm phát triển, chứa đáp án. API người học không gửi các trường này trước khi nộp. Không tuyên bố có giảng viên duyệt.

## 1. relations — PRIMARY KEY yêu cầu điều gì?

- A. Duy nhất và không NULL
- B. Cho phép mọi giá trị NULL
- C. Chỉ cần sắp xếp tăng
- D. Chỉ dùng cho văn bản

Đáp án: **A**. Căn cứ: “giá trị phải duy nhất và không NULL”.

Đối chiếu: đáp án đúng diễn đạt trực tiếp căn cứ; ba lựa chọn còn lại trái với căn cứ hoặc không trả lời câu hỏi. Phạm vi: phiếu học tập demo PostgreSQL 16.

## 2. relations — Muốn khóa ngoại bắt buộc có giá trị, cần thêm gì?

- A. ORDER BY
- B. NOT NULL
- C. HAVING
- D. SAVEPOINT

Đáp án: **B**. Căn cứ: “Khóa ngoại không tự cấm NULL; muốn bắt buộc có lớp thì thêm NOT NULL”.

Đối chiếu: đáp án đúng diễn đạt trực tiếp căn cứ; ba lựa chọn còn lại trái với căn cứ hoặc không trả lời câu hỏi. Phạm vi: phiếu học tập demo PostgreSQL 16.

## 3. sql — LEFT JOIN xử lý hàng trái không có hàng phải khớp thế nào?

- A. Loại hàng trái
- B. Báo lỗi
- C. Giữ hàng trái, cột bên phải là NULL
- D. Tạo hàng mới trong bảng phải

Đáp án: **C**. Căn cứ: “LEFT JOIN giữ mọi hàng bên trái; nếu không có hàng khớp bên phải, các cột phía phải nhận NULL”.

Đối chiếu: đáp án đúng diễn đạt trực tiếp căn cứ; ba lựa chọn còn lại trái với căn cứ hoặc không trả lời câu hỏi. Phạm vi: phiếu học tập demo PostgreSQL 16.

## 4. sql — Mệnh đề nào lọc nhóm sau GROUP BY?

- A. WHERE
- B. ON
- C. ORDER BY
- D. HAVING

Đáp án: **D**. Căn cứ: “HAVING lọc nhóm sau GROUP BY”.

Đối chiếu: đáp án đúng diễn đạt trực tiếp căn cứ; ba lựa chọn còn lại trái với căn cứ hoặc không trả lời câu hỏi. Phạm vi: phiếu học tập demo PostgreSQL 16.

## 5. erd — Quan hệ nhiều–nhiều SinhVien–MonHoc trong ví dụ được chuyển sang bảng thế nào?

- A. Tạo bảng liên kết DangKy
- B. Xóa MonHoc
- C. Gộp mọi môn vào một ô
- D. Không cần khóa ngoại

Đáp án: **A**. Căn cứ: “tạo bảng liên kết DangKy(ma_sv, ma_mon, diem), hai mã là khóa ngoại”.

Đối chiếu: đáp án đúng diễn đạt trực tiếp căn cứ; ba lựa chọn còn lại trái với căn cứ hoặc không trả lời câu hỏi. Phạm vi: phiếu học tập demo PostgreSQL 16.

## 6. erd — Vì sao không xác định dạng chuẩn chỉ từ vài hàng mẫu?

- A. Luôn cần index
- B. Cần biết khóa và phụ thuộc hàm
- C. Mọi bảng đều ở 3NF
- D. Phải chạy COMMIT

Đáp án: **B**. Căn cứ: “Không thể kết luận dạng chuẩn chỉ từ vài hàng mẫu; cần biết khóa và phụ thuộc hàm”.

Đối chiếu: đáp án đúng diễn đạt trực tiếp căn cứ; ba lựa chọn còn lại trái với căn cứ hoặc không trả lời câu hỏi. Phạm vi: phiếu học tập demo PostgreSQL 16.

## 7. transaction — ROLLBACK toàn bộ giao dịch có tác dụng gì?

- A. Xác nhận thay đổi
- B. Tạo index
- C. Hủy thay đổi chưa commit trong giao dịch
- D. Xóa mọi bảng đã commit

Đáp án: **C**. Căn cứ: “ROLLBACK hủy thay đổi chưa commit trong giao dịch”.

Đối chiếu: đáp án đúng diễn đạt trực tiếp căn cứ; ba lựa chọn còn lại trái với căn cứ hoặc không trả lời câu hỏi. Phạm vi: phiếu học tập demo PostgreSQL 16.

## 8. transaction — ROLLBACK TO SAVEPOINT làm gì?

- A. Hủy giao dịch đã commit
- B. Luôn kết thúc kết nối
- C. Xác nhận toàn bộ giao dịch
- D. Hủy thay đổi sau mốc, giữ thay đổi trước mốc

Đáp án: **D**. Căn cứ: “ROLLBACK TO SAVEPOINT hủy các thay đổi sau mốc, giữ các thay đổi trước mốc”.

Đối chiếu: đáp án đúng diễn đạt trực tiếp căn cứ; ba lựa chọn còn lại trái với căn cứ hoặc không trả lời câu hỏi. Phạm vi: phiếu học tập demo PostgreSQL 16.

## 9. index — Nhận định nào đúng về index?

- A. Không bảo đảm mọi truy vấn nhanh hơn
- B. Luôn được planner sử dụng
- C. Không chiếm dung lượng
- D. Không cần cập nhật khi ghi

Đáp án: **A**. Căn cứ: “Có index không có nghĩa mọi truy vấn nhanh hơn hoặc planner luôn dùng nó”.

Đối chiếu: đáp án đúng diễn đạt trực tiếp căn cứ; ba lựa chọn còn lại trái với căn cứ hoặc không trả lời câu hỏi. Phạm vi: phiếu học tập demo PostgreSQL 16.

## 10. index — EXPLAIN ANALYZE khác EXPLAIN ở điểm nào?

- A. Không hiển thị kế hoạch
- B. Thực sự chạy câu lệnh và bổ sung số liệu thực tế
- C. Chỉ đổi tên bảng
- D. Luôn chạy nhanh hơn truy vấn gốc

Đáp án: **B**. Căn cứ: “EXPLAIN ANALYZE thực sự chạy câu lệnh và bổ sung số liệu thực tế”.

Đối chiếu: đáp án đúng diễn đạt trực tiếp căn cứ; ba lựa chọn còn lại trái với căn cứ hoặc không trả lời câu hỏi. Phạm vi: phiếu học tập demo PostgreSQL 16.

## Câu bị loại / chưa duyệt

- Lần live-02, câu 1 Qwen chép các câu hỏi vào lựa chọn, còn lựa chọn thứ tư là `correct`. Đáp án đánh dấu C không trả lời câu hỏi LEFT JOIN. Loại khỏi ngân hàng chấm; toàn bộ bài vẫn draft, API nộp trả 409.
- Lần live-02, câu 3 chuyển sang EXPLAIN khi yêu cầu SQL JOIN. Chưa duyệt vì lệch phạm vi. Đã ưu tiên tài liệu có tên khớp chủ đề ở lần thử sau.
- Lần live-02, câu 2 giải thích ON như lọc “trước JOIN” là diễn đạt quá đơn giản; cần rà thuật ngữ và giảm độ dài lựa chọn trước khi xét duyệt.
- Kiểm thử tự động loại nguồn không tồn tại, trích đoạn bịa, lựa chọn trùng, câu hỏi trùng, bool thay chỉ số đáp án và lựa chọn chép câu hỏi. Các kiểm tra này không thay thế rà soát học thuật.

- Lần live-04: bộ demo cả 5 chủ đề đạt; bản nháp Qwen bị validator từ chối (HTTP 502), không lưu quiz sai. Sau đó đổi hợp đồng JSON sang các key bắt buộc q1/q2/q3 và lựa chọn A/B/C/D để giảm lặp/thiếu trường.

- Lần live-05: hợp đồng q1/q2/q3 tạo được 3 câu có cấu trúc/căn cứ hợp lệ. Câu 1 (INNER/LEFT JOIN) và câu 3 (WHERE/HAVING) phù hợp phiếu. Câu 2 có lựa chọn C và D đều có thể được hiểu là đúng; giải thích nói WHERE loại NULL nói chung là quá rộng (chỉ đúng với điều kiện loại NULL như ví dụ d.mon = 'CSDL'). Không duyệt bài để chấm, vẫn draft. Cần viết lại thành tình huống SQL cụ thể trước khi đưa vào ngân hàng.
