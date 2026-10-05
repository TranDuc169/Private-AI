export function extractionNotice(document) {
  if (document.index_status === 'ready') return {
    kind: 'success', title: 'Tài liệu sẵn sàng tìm kiếm',
    message: `“${document.filename}” · ${document.chunk_count} đoạn đã có vector BGE-M3. Chưa có trả lời AI.`,
  };
  if (document.index_status === 'failed') return {
    kind: 'warning', title: 'Đã đọc văn bản, nhưng tạo vector thất bại',
    message: document.index_error || 'Mở Tài liệu để thử tạo vector lại; không cần upload lại.',
  };
  if (document.index_status === 'processing') return {
    kind: 'progress', title: 'Đang chia đoạn và tạo vector…', message: 'Có thể mở Tài liệu để theo dõi trạng thái.',
  };
  if (document.status === 'ready') return {
    kind: 'warning', title: 'Đã đọc văn bản · chưa tạo vector',
    message: `“${document.filename}” · ${document.page_count} trang. Chưa sẵn sàng tìm kiếm.`,
  };
  return {
    kind: 'warning', title: 'Tải lên thành công, nhưng chưa đọc được văn bản',
    message: `“${document.filename}”: ${document.error_message || 'Có thể thử trích xuất lại trong Tài liệu.'}`,
  };
}

export function uploadFailureNotice(error, savedDocument) {
  if (savedDocument) return {
    kind: 'warning', title: 'File đã lưu; chưa xác nhận được kết quả xử lý',
    message: 'Mở Tài liệu và làm mới danh sách để kiểm tra bước đọc chữ / tạo vector. Không cần tải file lên lần nữa.',
  };
  if (!error.status) return {
    kind: 'error', title: 'Mất kết nối; chưa xác nhận được kết quả tải lên',
    message: 'Kiểm tra kết nối rồi làm mới danh sách Tài liệu trước khi thử lại để tránh tải trùng file.',
  };
  return { kind: 'error', title: 'Tải lên thất bại', message: error.message };
}
