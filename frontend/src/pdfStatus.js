export function extractionNotice(document) {
  if (document.status === 'ready') return {
    kind: 'success', title: 'Tải lên và đọc văn bản thành công',
    message: `“${document.filename}” · ${document.page_count} trang. Đã lưu trong workspace.`,
  };
  return {
    kind: 'warning', title: 'Tải lên thành công, nhưng chưa đọc được văn bản',
    message: `“${document.filename}”: ${document.error_message || 'Có thể thử trích xuất lại trong Tài liệu.'}`,
  };
}

export function uploadFailureNotice(error, savedDocument) {
  if (savedDocument) return {
    kind: 'warning', title: 'File đã lưu; chưa xác nhận được kết quả đọc văn bản',
    message: 'Mở Tài liệu và làm mới danh sách trước khi thử trích xuất lại. Không cần tải file lên lần nữa.',
  };
  if (!error.status) return {
    kind: 'error', title: 'Mất kết nối; chưa xác nhận được kết quả tải lên',
    message: 'Kiểm tra kết nối rồi làm mới danh sách Tài liệu trước khi thử lại để tránh tải trùng file.',
  };
  return { kind: 'error', title: 'Tải lên thất bại', message: error.message };
}
