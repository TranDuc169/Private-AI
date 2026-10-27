import { useEffect, useRef, useState } from 'react';
import { apiRequest } from './api.js';

export default function SourceCard({ hit, workspace, token, onUnauthorized, summary }) {
  const [state, setState] = useState({ busy: false, current: null, error: '' });
  const active = useRef(null);
  useEffect(() => () => { active.current?.abort(); active.current = null; }, []);
  async function check() {
    active.current?.abort();
    const controller = new AbortController(); active.current = controller;
    setState({ busy: true, current: null, error: '' });
    try {
      const current = await apiRequest(`/workspaces/${workspace.id}/sources/${hit.chunk_id}`, { token, signal: controller.signal });
      if (!controller.signal.aborted) setState({ busy: false, current, error: '' });
    } catch (e) {
      if (!controller.signal.aborted) { setState({ busy: false, current: null, error: e.message }); if (e.status === 401) onUnauthorized(); }
    }
  }
  return <li><details><summary><strong>[{hit.source_id}] {hit.filename} · Trang {hit.page_number}</strong></summary>
    <p className="retrieval-note">Trích đoạn đã lưu cùng câu trả lời</p><p className="source-text">{hit.text}</p>
    {!summary && <small>Điểm cosine lúc truy xuất: {hit.score.toFixed(3)} — không phải xác suất đúng.</small>}
    <p><button type="button" className="secondary" disabled={state.busy} onClick={check}>{state.busy ? 'Đang kiểm tra…' : 'Mở đoạn nguồn hiện tại'}</button></p>
    {state.error && <p role="alert">{state.error} Bản trích đã lưu vẫn nằm trong lịch sử này.</p>}
    {state.current && <div><strong>{state.current.filename} · Trang {state.current.page_number}</strong><p className="source-text">{state.current.text}</p></div>}
  </details></li>;
}
