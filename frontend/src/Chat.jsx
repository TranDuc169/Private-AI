import { useEffect, useRef, useState } from 'react';
import { apiRequest } from './api.js';
import PdfUpload from './PdfUpload.jsx';

export default function Chat({ workspace, token, onUnauthorized }) {
  const [question, setQuestion] = useState('');
  const [turns, setTurns] = useState([]);
  const [busy, setBusy] = useState(false);
  const active = useRef(null);
  const latest = useRef(null);
  useEffect(() => () => { active.current?.abort(); active.current = null; }, []);
  useEffect(() => { latest.current?.scrollIntoView({ block: 'nearest' }); }, [turns]);

  async function send(event) {
    event.preventDefault();
    const value = question.trim();
    if (!workspace || !value || busy || active.current) return;
    const controller = new AbortController(); active.current = controller;
    const id = crypto.randomUUID();
    setTurns(old => [...old.slice(-9), { id, question: value, state: 'loading' }]);
    setQuestion(''); setBusy(true);
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 130000);
    const update = next => setTurns(old => old.map(turn => turn.id === id ? { ...turn, ...next } : turn));
    try {
      const result = await apiRequest(`/workspaces/${workspace.id}/retrieve`, {
        token, method: 'POST', body: { question: value, top_k: 5 }, signal: controller.signal,
      });
      if (active.current === controller && !controller.signal.aborted) update({ state: 'done', result });
    } catch (error) {
      if (active.current === controller) {
        update({ state: 'error', error: error.name === 'AbortError'
          ? timedOut ? 'Hết thời gian chờ. Kiểm tra Ollama rồi thử lại.' : 'Đã dừng chờ kết quả.'
          : error.message });
        if (error.status === 401) onUnauthorized();
      }
    } finally {
      clearTimeout(timer);
      if (active.current === controller) { active.current = null; setBusy(false); }
    }
  }

  return <section className="chat">
    <p className="retrieval-note">Tìm đoạn trong tài liệu, chưa có câu trả lời AI. {workspace ? `Workspace: ${workspace.name}.` : 'Chọn workspace để bắt đầu.'}</p>
    {turns.length === 0 ? <div className="empty"><span className="empty-icon" aria-hidden="true">◇</span><h2>Bạn muốn tìm thông tin gì?</h2><p>Nhập câu hỏi về PDF đã xử lý. Hệ thống sẽ đưa ra các đoạn gần nghĩa nhất trong workspace này để bạn kiểm tra nguồn.</p></div>
      : <div className="retrieval-turns" aria-label="Câu hỏi và các đoạn truy xuất">{turns.map(turn => <article className="retrieval-turn" key={turn.id}>
        <p className="user-question"><strong>Bạn</strong><br />{turn.question}</p>
        {turn.state === 'loading' && <p role="status">Đang tìm đoạn liên quan trong workspace…</p>}
        {turn.state === 'error' && <div role="alert"><p className="error-text">{turn.error}</p><button className="secondary" disabled={busy} onClick={() => setQuestion(turn.question)}>Đưa câu hỏi vào ô nhập để thử lại</button></div>}
        {turn.state === 'done' && <div>
          <p role="status">{turn.result.results.length ? `Tìm được ${turn.result.results.length} đoạn gần nghĩa. Đây là trích đoạn nguồn, không phải câu trả lời AI.` : 'Workspace chưa có đoạn đã tạo vector phù hợp. Vào Tài liệu để xử lý PDF trước.'}</p>
          {turn.result.results.length > 0 && <p className="retrieval-note">Đoạn gần nghĩa vẫn có thể không chứa đáp án. Hãy đọc và đối chiếu nguồn.</p>}
          <ol className="retrieval-results">{turn.result.results.map((hit, index) => <li key={hit.chunk_id}>
            <strong>[{index + 1}] {hit.filename} · Trang {hit.page_number}</strong>
            <p className="source-text">{hit.text}</p>
            <details><summary>Thông tin truy xuất</summary><p>Đoạn {hit.chunk_index + 1} · Ký tự {hit.start_char}–{hit.end_char}<br />Điểm cosine: {hit.score.toFixed(3)} — không phải xác suất đúng.</p><small>Mã tài liệu: {hit.document_id}</small></details>
          </li>)}</ol>
          <small>Top-K: {turn.result.top_k} · {turn.result.embedding_model} · {turn.result.elapsed_ms} ms</small>
        </div>}
      </article>)}<div ref={latest} /></div>}
    <form className="composer" onSubmit={send}>
      <label htmlFor="message" className="sr-only">Câu hỏi tìm trong tài liệu</label>
      <textarea id="message" rows={3} value={question} maxLength={2000} disabled={!workspace || busy}
        placeholder={workspace ? 'Nhập câu hỏi về tài liệu trong workspace…' : 'Chọn workspace trước khi nhập câu hỏi.'}
        onChange={e => setQuestion(e.target.value)} onKeyDown={e => {
          if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send(e); }
        }} />
      <details className="chat-attachment"><summary>+ Đính kèm PDF</summary><PdfUpload compact token={token} workspace={workspace} onUnauthorized={onUnauthorized} disabled={busy} /></details>
      <div className="composer-actions"><small>Enter để gửi · Shift+Enter xuống dòng. Chỉ giữ tối đa 10 lượt trên màn hình; đổi trang/workspace sẽ xóa.</small>
        {busy ? <button type="button" className="secondary" onClick={() => active.current?.abort()}>Dừng chờ</button>
          : <button type="submit" disabled={!workspace || !question.trim()}>Tìm đoạn ↑</button>}
      </div>
    </form>
  </section>;
}
