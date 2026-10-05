import { useEffect, useRef, useState } from 'react';
import { apiRequest } from './api.js';
import PdfUpload, { UploadNotice } from './PdfUpload.jsx';
import { extractionNotice, uploadFailureNotice } from './pdfStatus.js';

const labels = { uploaded: 'Đã lưu · chưa trích xuất', ready: 'Đã trích xuất', failed: 'Trích xuất lỗi' };

export default function Documents({ token, workspace, onUnauthorized }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [preview, setPreview] = useState(null);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [chunkPreview, setChunkPreview] = useState(null);
  const [uploadRevision, setUploadRevision] = useState(0);
  const actions = useRef(new Set());
  const pageRequest = useRef(null);
  const base = `/workspaces/${workspace.id}/documents`;
  useEffect(() => {
    const controller = new AbortController();
    apiRequest(base, { token, signal: controller.signal }).then(data => {
      if (!controller.signal.aborted) setItems(data);
    }).catch(e => {
      if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) onUnauthorized(); }
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => { controller.abort(); actions.current.forEach(c => c.abort()); pageRequest.current?.abort(); };
  }, [base, token, onUnauthorized]);

  const processing = items.some(item => item.index_status === 'processing');
  useEffect(() => {
    if (!processing) return;
    const controller = new AbortController();
    let timer;
    async function poll() {
      try {
        const data = await apiRequest(base, { token, signal: controller.signal });
        if (!controller.signal.aborted) { setItems(data); setError(''); }
      } catch (e) {
        if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) onUnauthorized(); }
      } finally {
        if (!controller.signal.aborted) timer = setTimeout(poll, 3000);
      }
    }
    timer = setTimeout(poll, 3000);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [processing, base, token, onUnauthorized]);

  const working = !!busy || uploadBusy;
  function upsert(item) {
    setItems(old => old.some(value => value.id === item.id) ? old.map(value => value.id === item.id ? item : value) : [...old, item]);
  }

  async function action(document) {
    const controller = new AbortController();
    actions.current.add(controller);
    const options = { token, signal: controller.signal };
    setError(''); setNotice(null); setUploadRevision(value => value + 1); setBusy('Đang xử lý tài liệu…');
    try {
      let result = document;
      if (result.status !== 'ready') result = await apiRequest(`${base}/${document.id}/process`, { ...options, method: 'POST' });
      if (controller.signal.aborted) return;
      if (result.status === 'ready') {
        upsert({ ...result, index_status: 'processing' });
        result = await apiRequest(`${base}/${document.id}/index`, { ...options, method: 'POST' });
      }
      if (!controller.signal.aborted) { upsert(result); setNotice(extractionNotice(result)); }
    } catch (e) {
      if (!controller.signal.aborted) { setNotice(uploadFailureNotice(e, document)); if (e.status === 401) onUnauthorized(); }
    } finally {
      actions.current.delete(controller);
      if (!controller.signal.aborted) setBusy('');
    }
  }

  async function remove(document) {
    const controller = new AbortController(); actions.current.add(controller);
    setBusy('Đang xóa tài liệu…'); setError(''); setNotice(null);
    try {
      await apiRequest(`${base}/${document.id}`, { token, method: 'DELETE', signal: controller.signal });
      if (!controller.signal.aborted) {
        setItems(old => old.filter(item => item.id !== document.id));
        setConfirmDelete(null); setPreview(null); setChunkPreview(null); pageRequest.current?.abort();
        setNotice({ kind: 'success', title: 'Đã xóa tài liệu', message: 'Đã dọn file PDF, văn bản, các đoạn và vector.' });
      }
    } catch (e) { if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) onUnauthorized(); } }
    finally { actions.current.delete(controller); if (!controller.signal.aborted) setBusy(''); }
  }

  async function viewChunk(document, number) {
    pageRequest.current?.abort();
    const controller = new AbortController(); pageRequest.current = controller;
    setPreview(null); setChunkPreview({ document, number, loading: true });
    try {
      const chunks = await apiRequest(`${base}/${document.id}/chunks?offset=${number}&limit=1`, { token, signal: controller.signal });
      if (!controller.signal.aborted) setChunkPreview({ document, number, chunk: chunks[0], loading: false });
    } catch (e) { if (!controller.signal.aborted) { setChunkPreview({ document, number, error: e.message }); if (e.status === 401) onUnauthorized(); } }
  }

  async function refresh() {
    const controller = new AbortController(); actions.current.add(controller);
    setLoading(true); setError(''); setPreview(null); setChunkPreview(null); pageRequest.current?.abort();
    try {
      const result = await apiRequest(base, { token, signal: controller.signal });
      if (!controller.signal.aborted) setItems(result);
    } catch (e) { if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) onUnauthorized(); } }
    finally { actions.current.delete(controller); if (!controller.signal.aborted) setLoading(false); }
  }

  async function viewPage(document, number) {
    setChunkPreview(null);
    pageRequest.current?.abort();
    const controller = new AbortController(); pageRequest.current = controller;
    setPreview({ document, number, loading: true, text: '', error: '' });
    try {
      const pages = await apiRequest(`${base}/${document.id}/pages?offset=${number - 1}&limit=1`, { token, signal: controller.signal });
      if (!controller.signal.aborted) setPreview({ document, number, loading: false, text: pages[0]?.text || '', error: '' });
    } catch (e) {
      if (!controller.signal.aborted) { setPreview({ document, number, loading: false, text: '', error: e.message }); if (e.status === 401) onUnauthorized(); }
    }
  }

  return <section className="data-panel">
    <h2>Tài liệu · {workspace.name}</h2>
    <PdfUpload key={uploadRevision} token={token} workspace={workspace} onUnauthorized={onUnauthorized} onDocument={upsert} onBusy={value => { setUploadBusy(value); if (value) setNotice(null); }} disabled={!!busy || loading} />
    <UploadNotice notice={notice} />
    {busy && <p role="status">{busy}</p>}
    {error && <p role="alert" className="error-text">{error}</p>}
    <button className="secondary" onClick={refresh} disabled={working || loading}>Làm mới danh sách</button>
    {loading ? <p role="status">Đang tải danh sách…</p> : items.length === 0 ? <p>Workspace này chưa có tài liệu.</p> : <ul className="document-list">{items.map(item => <li key={item.id}>
      <strong>{item.filename}</strong><p>{labels[item.status] || item.status} · {(item.size_bytes / 1024).toFixed(1)} KB{item.page_count != null ? ` · ${item.page_count} trang` : ''}</p>
      <p role="status">{({ pending: 'Chưa tạo vector', processing: 'Đang tạo vector · tự cập nhật mỗi 3 giây', ready: 'Sẵn sàng tìm kiếm', failed: 'Tạo vector lỗi' })[item.index_status]} · {item.chunk_count || 0} đoạn</p>
      {item.error_message && <p className="error-text">{item.error_message}</p>}
      {item.index_error && <p className="error-text">{item.index_error}</p>}
      <div className="page-controls">
        {item.status === 'ready' && <button className="secondary" disabled={working} onClick={() => viewPage(item, 1)}>Xem văn bản · {item.filename}</button>}
        {item.index_status !== 'ready' && <button className="secondary" disabled={working} onClick={() => action(item)}>{item.status !== 'ready' ? 'Thử trích xuất' : item.index_status === 'processing' ? 'Kiểm tra / thử lại' : 'Tạo vector / thử lại'} · {item.filename}</button>}
        {item.index_status === 'ready' && <button className="secondary" disabled={working} onClick={() => viewChunk(item, 0)}>Chi tiết các đoạn · {item.filename}</button>}
        <button className="secondary" disabled={working} onClick={() => setConfirmDelete(item)}>Xóa · {item.filename}</button>
      </div>
      {item.index_status === 'processing' && <small>Nếu server dừng giữa chừng, có thể thử lại sau 15 phút.</small>}
      {confirmDelete?.id === item.id && <div className="upload-notice warning" role="alert"><p>Xóa “{item.filename}” cùng toàn bộ chữ và vector? Không thể hoàn tác.</p><button disabled={working} onClick={() => remove(item)}>Xác nhận xóa</button> <button className="secondary" disabled={working} onClick={() => setConfirmDelete(null)}>Hủy</button></div>}
    </li>)}</ul>}
    {preview && <section className="text-preview" aria-label="Văn bản trích xuất"><h3>{preview.document.filename} · Trang {preview.number}/{preview.document.page_count}</h3>
      <div className="page-controls"><button disabled={preview.loading || preview.number <= 1} onClick={() => viewPage(preview.document, preview.number - 1)}>Trang trước</button><button disabled={preview.loading || preview.number >= preview.document.page_count} onClick={() => viewPage(preview.document, preview.number + 1)}>Trang sau</button><button className="secondary" onClick={() => { pageRequest.current?.abort(); setPreview(null); }}>Đóng</button></div>
      {preview.loading ? <p role="status">Đang đọc trang…</p> : preview.error ? <p role="alert">{preview.error}</p> : <pre>{preview.text || 'Trang này không có văn bản trích xuất được.'}</pre>}
    </section>}
    {chunkPreview && <section className="text-preview" aria-label="Chi tiết đoạn văn bản"><h3>{chunkPreview.document.filename} · Đoạn {chunkPreview.number + 1}/{chunkPreview.document.chunk_count}</h3>
      <div className="page-controls"><button disabled={chunkPreview.loading || chunkPreview.number === 0} onClick={() => viewChunk(chunkPreview.document, chunkPreview.number - 1)}>Đoạn trước</button><button disabled={chunkPreview.loading || chunkPreview.number + 1 >= chunkPreview.document.chunk_count} onClick={() => viewChunk(chunkPreview.document, chunkPreview.number + 1)}>Đoạn sau</button><button className="secondary" onClick={() => { pageRequest.current?.abort(); setChunkPreview(null); }}>Đóng chi tiết</button></div>
      {chunkPreview.loading ? <p role="status">Đang đọc đoạn…</p> : chunkPreview.error ? <p role="alert">{chunkPreview.error}</p> : chunkPreview.chunk && <><p>Trang {chunkPreview.chunk.page_number} · Ký tự {chunkPreview.chunk.start_char}–{chunkPreview.chunk.end_char} · Vector {chunkPreview.chunk.embedding_dimensions} chiều · {chunkPreview.chunk.embedding_model}</p><pre>{chunkPreview.chunk.text}</pre></>}
    </section>}
    <p><small>Sẵn sàng tìm kiếm nghĩa là đã lưu đủ các đoạn và vector. Chưa có tìm kiếm hoặc trả lời AI trong tuần 5.</small></p>
  </section>;
}
