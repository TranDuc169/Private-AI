const baseUrl = (import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

export async function getHealth({ signal, fetchImpl = fetch } = {}) {
  const response = await fetchImpl(`${baseUrl}/health`, {
    signal,
    headers: { Accept: 'application/json' },
    cache: 'no-store',
  });
  let body;
  try {
    body = await response.json();
  } catch {
    throw new Error('Backend trả dữ liệu không đúng JSON. Kiểm tra địa chỉ API.');
  }
  if (response.status === 503 && body?.status === 'degraded' && body?.database === 'down') {
    return { kind: 'database-error', message: 'FastAPI đang chạy, nhưng chưa kết nối được PostgreSQL.' };
  }
  if (!response.ok) throw new Error(`Backend trả lỗi HTTP ${response.status}.`);
  if (body?.status !== 'ok' || body?.database !== 'up') {
    throw new Error('Phản hồi /health không đúng API contract.');
  }
  return { kind: 'success', message: 'Đã kết nối FastAPI và truy vấn PostgreSQL thành công.' };
}
