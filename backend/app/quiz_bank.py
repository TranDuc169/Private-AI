"""Demo bank technically checked against corpus v1, not instructor certification."""
BANK_VERSION = 'csdl-quiz-v1'
REVIEW = 'Đối chiếu kỹ thuật với phiếu học tập csdl-demo-v1; chưa có giảng viên thẩm định.'
# topic, question, choices, correct index, exact evidence anchor
BANK = [
 ('relations', 'PRIMARY KEY yêu cầu điều gì?', ['Duy nhất và không NULL', 'Cho phép mọi giá trị NULL', 'Chỉ cần sắp xếp tăng', 'Chỉ dùng cho văn bản'], 0, 'giá trị phải duy nhất và không NULL'),
 ('relations', 'Muốn khóa ngoại bắt buộc có giá trị, cần thêm gì?', ['ORDER BY', 'NOT NULL', 'HAVING', 'SAVEPOINT'], 1, 'Khóa ngoại không tự cấm NULL; muốn bắt buộc có lớp thì thêm NOT NULL'),
 ('sql', 'LEFT JOIN xử lý hàng trái không có hàng phải khớp thế nào?', ['Loại hàng trái', 'Báo lỗi', 'Giữ hàng trái, cột bên phải là NULL', 'Tạo hàng mới trong bảng phải'], 2, 'LEFT JOIN giữ mọi hàng bên trái; nếu không có hàng khớp bên phải, các cột phía phải nhận NULL'),
 ('sql', 'Mệnh đề nào lọc nhóm sau GROUP BY?', ['WHERE', 'ON', 'ORDER BY', 'HAVING'], 3, 'HAVING lọc nhóm sau GROUP BY'),
 ('erd', 'Quan hệ nhiều–nhiều SinhVien–MonHoc trong ví dụ được chuyển sang bảng thế nào?', ['Tạo bảng liên kết DangKy', 'Xóa MonHoc', 'Gộp mọi môn vào một ô', 'Không cần khóa ngoại'], 0, 'tạo bảng liên kết DangKy(ma_sv, ma_mon, diem), hai mã là khóa ngoại'),
 ('erd', 'Vì sao không xác định dạng chuẩn chỉ từ vài hàng mẫu?', ['Luôn cần index', 'Cần biết khóa và phụ thuộc hàm', 'Mọi bảng đều ở 3NF', 'Phải chạy COMMIT'], 1, 'Không thể kết luận dạng chuẩn chỉ từ vài hàng mẫu; cần biết khóa và phụ thuộc hàm'),
 ('transaction', 'ROLLBACK toàn bộ giao dịch có tác dụng gì?', ['Xác nhận thay đổi', 'Tạo index', 'Hủy thay đổi chưa commit trong giao dịch', 'Xóa mọi bảng đã commit'], 2, 'ROLLBACK hủy thay đổi chưa commit trong giao dịch'),
 ('transaction', 'ROLLBACK TO SAVEPOINT làm gì?', ['Hủy giao dịch đã commit', 'Luôn kết thúc kết nối', 'Xác nhận toàn bộ giao dịch', 'Hủy thay đổi sau mốc, giữ thay đổi trước mốc'], 3, 'ROLLBACK TO SAVEPOINT hủy các thay đổi sau mốc, giữ các thay đổi trước mốc'),
 ('index', 'Nhận định nào đúng về index?', ['Không bảo đảm mọi truy vấn nhanh hơn', 'Luôn được planner sử dụng', 'Không chiếm dung lượng', 'Không cần cập nhật khi ghi'], 0, 'Có index không có nghĩa mọi truy vấn nhanh hơn hoặc planner luôn dùng nó'),
 ('index', 'EXPLAIN ANALYZE khác EXPLAIN ở điểm nào?', ['Không hiển thị kế hoạch', 'Thực sự chạy câu lệnh và bổ sung số liệu thực tế', 'Chỉ đổi tên bảng', 'Luôn chạy nhanh hơn truy vấn gốc'], 1, 'EXPLAIN ANALYZE thực sự chạy câu lệnh và bổ sung số liệu thực tế'),
]
