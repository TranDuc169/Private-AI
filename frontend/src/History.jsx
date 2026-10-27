import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from './api.js';

export default function History({ workspace, token, onUnauthorized }) {
  const [state, setState] = useState({ loading: true, items: [], error: '' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setState({ loading: true, items: [], error: '' });
    apiRequest(`/workspaces/${workspace.id}/conversations`, { token, signal: controller.signal })
      .then(items => { if (!controller.signal.aborted) setState({ loading: false, items: [...items].reverse(), error: '' }); })
      .catch(e => { if (!controller.signal.aborted) { setState({ loading: false, items: [], error: e.message }); if (e.status === 401) onUnauthorized(); } });
    return () => controller.abort();
  }, [workspace.id, token, onUnauthorized, attempt]);
  return <section className="data-panel"><h2>Lịch sử · {workspace.name}</h2>
    <Link to="/">Hội thoại mới</Link>
    {state.loading ? <p role="status">Đang tải lịch sử…</p> : state.error ? <div role="alert"><p>{state.error}</p><button onClick={() => setAttempt(n => n + 1)}>Thử lại</button></div>
      : state.items.length ? <ul>{state.items.map(item => <li key={item.id}>
        <Link to={`/chat/${item.id}`}>{item.title}</Link><small> · {new Date(item.created_at).toLocaleString('vi-VN')}</small>
      </li>)}</ul> : <p>Chưa có hội thoại. Gửi câu hỏi ở Chat chung để tạo lịch sử.</p>}
    <p>Lịch sử lưu trong database theo workspace. Nguồn trong câu trả lời là bản chụp tại thời điểm trả lời.</p>
  </section>;
}
