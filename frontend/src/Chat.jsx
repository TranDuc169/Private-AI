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
    // Retrieval and generation each have a backend timeout of at most 120 seconds.
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 250000);
    const update = next => setTurns(old => old.map(turn => turn.id === id ? { ...turn, ...next } : turn));
    try {
      const result = await apiRequest(`/workspaces/${workspace.id}/chat`, {
        token, method: 'POST', body: { question: value }, signal: controller.signal,
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
    <p className="retrieval-note">Học Cơ sở dữ liệu qua tài liệu của bạn. {workspace ? `Workspace: ${workspace.name}.` : 'Chọn workspace để bắt đầu.'}</p>
    {turns.length === 0 ? <div className="empty"><span className="empty-icon" aria-hidden="true">◇</span><h2>Bạn muốn hiểu phần nào về Cơ sở dữ liệu?</h2><p>Hỏi về khóa chính, JOIN, chuẩn hóa, transaction hoặc index. Trợ lý dùng PDF đã tạo vector trong workspace để giải thích và dẫn nguồn.</p><p className="retrieval-note">Ví dụ: LEFT JOIN khác INNER JOIN thế nào?<br />Mỗi câu hỏi được xử lý độc lập. Roadmap, quiz và lịch sử lưu lâu dài chưa có ở phiên bản này.</p></div>
      : <div className="retrieval-turns" aria-label="Câu hỏi và các đoạn truy xuất">{turns.map(turn => <article className="retrieval-turn" key={turn.id}>
        <p className="user-question"><strong>Bạn</strong><br />{turn.question}</p>
        {turn.state === 'loading' && <p role="status">Đang tìm tài liệu và soạn câu trả lời… Lần đầu tải model có thể lâu hơn.</p>}
        {turn.state === 'error' && <div role="alert"><p className="error-text">{turn.error}</p><button className="secondary" disabled={busy} onClick={() => setQuestion(turn.question)}>Đưa câu hỏi vào ô nhập để thử lại</button></div>}
        {turn.state === 'done' && <div>
          <p className="answer-label">{turn.result.status === 'answered' ? 'Trợ lý Cơ sở dữ liệu' : 'Cần thêm thông tin'}</p>
          <div className="assistant-answer">{turn.result.answer}</div>
          {turn.result.sources.length > 0 && <p className="retrieval-note">Nguồn được dùng bên dưới. Câu trả lời do AI tạo có thể sai; hãy đối chiếu nội dung tài liệu.</p>}
          <ol className="retrieval-results">{turn.result.sources.map(hit => <li key={hit.chunk_id}>
            <details><summary><strong>[{hit.source_id}] {hit.filename} · Trang {hit.page_number}</strong></summary>
            <p className="source-text">{hit.text}</p>
            <p>Đoạn {hit.chunk_index + 1} · Điểm cosine: {hit.score.toFixed(3)} — không phải xác suất đúng.</p></details>
          </li>)}</ol>
          <small>{turn.result.status !== 'no_documents' ? `${turn.result.model} · ` : ''}{(turn.result.elapsed_ms / 1000).toFixed(1)} giây</small>
        </div>}
      </article>)}<div ref={latest} /></div>}
    <form className="composer" onSubmit={send}>
      <label htmlFor="message" className="sr-only">Câu hỏi Cơ sở dữ liệu</label>
      <textarea id="message" rows={3} value={question} maxLength={2000} disabled={!workspace || busy}
        placeholder={workspace ? 'Hỏi về Cơ sở dữ liệu trong tài liệu của bạn…' : 'Chọn workspace trước khi nhập câu hỏi.'}
        onChange={e => setQuestion(e.target.value)} onKeyDown={e => {
          if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send(e); }
        }} />
      <details className="chat-attachment"><summary>+ Đính kèm PDF</summary><PdfUpload compact token={token} workspace={workspace} onUnauthorized={onUnauthorized} disabled={busy} /></details>
      <div className="composer-actions"><small>Enter để gửi · Shift+Enter xuống dòng. Tối đa 10 lượt trên màn hình, chưa lưu lịch sử; đổi trang/workspace sẽ xóa. Dừng chờ không đảm bảo dừng model.</small>
        {busy ? <button type="button" className="secondary" onClick={() => active.current?.abort()}>Dừng chờ</button>
          : <button type="submit" disabled={!workspace || !question.trim()}>Gửi ↑</button>}
      </div>
    </form>
  </section>;
}
