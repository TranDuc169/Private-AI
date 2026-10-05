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

  const working = !!busy || uploadBusy;
  function upsert(item) {
    setItems(old => old.some(value => value.id === item.id) ? old.map(value => value.id === item.id ? item : value) : [...old, item]);
  }

  async function action(document) {
    const controller = new AbortController();
    actions.current.add(controller);
    const options = { token, signal: controller.signal };
    setError(''); setNotice(null); setBusy('Đang trích xuất văn bản…');
    try {
      const result = await apiRequest(`${base}/${document.id}/process`, { ...options, method: 'POST' });
      if (!controller.signal.aborted) { upsert(result); setNotice(extractionNotice(result)); }
    } catch (e) {
      if (!controller.signal.aborted) { setNotice(uploadFailureNotice(e, document)); if (e.status === 401) onUnauthorized(); }
    } finally {
      actions.current.delete(controller);
      if (!controller.signal.aborted) setBusy('');
    }
  }

  async function refresh() {
    const controller = new AbortController(); actions.current.add(controller);
    setLoading(true); setError(''); setPreview(null); pageRequest.current?.abort();
    try {
      const result = await apiRequest(base, { token, signal: controller.signal });
      if (!controller.signal.aborted) setItems(result);
    } catch (e) { if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) onUnauthorized(); } }
    finally { actions.current.delete(controller); if (!controller.signal.aborted) setLoading(false); }
  }

  async function viewPage(document, number) {
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
    <PdfUpload token={token} workspace={workspace} onUnauthorized={onUnauthorized} onDocument={upsert} onBusy={setUploadBusy} disabled={!!busy || loading} />
    <UploadNotice notice={notice} />
    {busy && <p role="status">{busy}</p>}
    {error && <p role="alert" className="error-text">{error}</p>}
    <button className="secondary" onClick={refresh} disabled={working || loading}>Làm mới danh sách</button>
    {loading ? <p role="status">Đang tải danh sách…</p> : items.length === 0 ? <p>Workspace này chưa có tài liệu.</p> : <ul className="document-list">{items.map(item => <li key={item.id}>
      <strong>{item.filename}</strong><p>{labels[item.status] || item.status} · {(item.size_bytes / 1024).toFixed(1)} KB{item.page_count != null ? ` · ${item.page_count} trang` : ''}</p>
      {item.error_message && <p className="error-text">{item.error_message}</p>}
      {item.status === 'ready' ? <button className="secondary" disabled={working} onClick={() => viewPage(item, 1)}>Xem văn bản · {item.filename}</button> : <button className="secondary" disabled={working} onClick={() => action(item)}>Thử trích xuất · {item.filename}</button>}
    </li>)}</ul>}
    {preview && <section className="text-preview" aria-label="Văn bản trích xuất"><h3>{preview.document.filename} · Trang {preview.number}/{preview.document.page_count}</h3>
      <div className="page-controls"><button disabled={preview.loading || preview.number <= 1} onClick={() => viewPage(preview.document, preview.number - 1)}>Trang trước</button><button disabled={preview.loading || preview.number >= preview.document.page_count} onClick={() => viewPage(preview.document, preview.number + 1)}>Trang sau</button><button className="secondary" onClick={() => { pageRequest.current?.abort(); setPreview(null); }}>Đóng</button></div>
      {preview.loading ? <p role="status">Đang đọc trang…</p> : preview.error ? <p role="alert">{preview.error}</p> : <pre>{preview.text || 'Trang này không có văn bản trích xuất được.'}</pre>}
    </section>}
    <p><small>Văn bản được đọc từ PDF; bố cục bảng/cột có thể khác bản gốc. Tài liệu chưa được dùng để trả lời AI.</small></p>
  </section>;
}
