import { useEffect, useRef, useState } from 'react';
import { apiRequest } from './api.js';
import { Link, useNavigate } from 'react-router-dom';
import SourceCard from './SourceCard.jsx';
import QuizCard from './QuizCard.jsx';
import PlanCard from './PlanCard.jsx';
import PdfUpload from './PdfUpload.jsx';

export default function Chat({ workspace, token, onUnauthorized, conversationId = null }) {
  const navigate = useNavigate();
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(Boolean(conversationId));
  const [loadError, setLoadError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [question, setQuestion] = useState('');
  const [turns, setTurns] = useState([]);
  const [busy, setBusy] = useState(false);
  const active = useRef(null);
  const latest = useRef(null);
  useEffect(() => () => { active.current?.abort(); active.current = null; }, []);
  useEffect(() => { latest.current?.scrollIntoView({ block: 'nearest' }); }, [turns]);

  useEffect(() => {
    if (!conversationId || !workspace) { setLoading(false); return; }
    const controller = new AbortController();
    setLoading(true); setLoadError(''); setTurns([]);
    apiRequest(`/workspaces/${workspace.id}/conversations/${conversationId}`, { token, signal: controller.signal })
      .then(data => {
        if (controller.signal.aborted) return;
        setRevision(data.revision);
        const restored = [];
        for (const message of data.messages) {
          if (message.role === 'user') restored.push({ id: message.id, question: message.content, state: 'legacy' });
          else if (message.result) restored.push({ id: message.id, question: '', state: 'done', result: message.result });
          else restored.push({ id: message.id, question: '', state: 'done', result: { answer: message.content, sources: [], status: 'answered', elapsed_ms: 0, model: '' } });
        }
        setTurns(restored);
      }).catch(e => { if (!controller.signal.aborted) { setLoadError(e.message); if (e.status === 401) onUnauthorized(); } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [conversationId, workspace?.id, token, onUnauthorized, attempt]);

  async function send(event) {
    event.preventDefault();
    const value = question.trim();
    if (!workspace || !value || busy || loading || loadError || active.current) return;
    const controller = new AbortController(); active.current = controller;
    const id = crypto.randomUUID();
    setTurns(old => [...old, { id, question: value, state: 'loading' }]);
    setQuestion(''); setBusy(true);
    let timedOut = false;
    // Topic summaries may generate two batches; allow time for both model calls.
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 370000);
    const update = next => setTurns(old => old.map(turn => turn.id === id ? { ...turn, ...next } : turn));
    try {
      const result = await apiRequest(`/workspaces/${workspace.id}/chat`, {
        token, method: 'POST', body: { question: value, conversation_id: conversationId, revision }, signal: controller.signal,
      });
      if (active.current === controller && !controller.signal.aborted) {
        setRevision(result.revision); update({ state: 'done', result });
        if (!conversationId) navigate(`/chat/${result.conversation_id}`, { replace: true });
      }
    } catch (error) {
      if (active.current === controller) {
        update({ state: 'error', error: error.name === 'AbortError'
          ? timedOut ? 'Hết thời gian chờ. Kiểm tra Ollama rồi thử lại.' : 'Đã dừng chờ kết quả.'
          : error.message });
        if (error.status === 401) onUnauthorized();
        if (error.status === 409 && conversationId) setLoadError('Hội thoại hoặc tài liệu đã thay đổi. Tải lại hội thoại để tiếp tục.');
      }
    } finally {
      clearTimeout(timer);
      if (active.current === controller) { active.current = null; setBusy(false); }
    }
  }

  return <section className="chat">
    <p className="retrieval-note">Học Cơ sở dữ liệu qua tài liệu của bạn. {workspace ? `Workspace: ${workspace.name}.` : 'Chọn workspace để bắt đầu.'}</p>
    <p><Link to="/">+ Hội thoại mới</Link> · <Link to="/history">Mở lịch sử</Link></p>
    {loading && <p role="status">Đang mở hội thoại…</p>}
    {loadError && <div role="alert"><p>{loadError}</p><button onClick={() => setAttempt(n => n + 1)}>Tải lại hội thoại</button></div>}
    {turns.length === 0 && !loading && !loadError ? <div className="empty"><span className="empty-icon" aria-hidden="true">◇</span><h2>Bạn muốn hiểu phần nào về Cơ sở dữ liệu?</h2><p>Hỏi về khóa chính, JOIN, chuẩn hóa, transaction hoặc index. Trợ lý dùng PDF đã tạo vector trong workspace để giải thích và dẫn nguồn.</p><p className="retrieval-note">Ví dụ: LEFT JOIN khác INNER JOIN thế nào?<br />Ví dụ: “Lập roadmap học SQL JOIN; nền tảng: mới bắt đầu; 4 buổi; 45 phút/buổi.” Hoặc “Tóm tắt chủ đề transaction”, “Quiz SQL JOIN”, “Sinh mới quiz transaction”. Lịch sử được lưu; mỗi yêu cầu vẫn cần viết đủ ý vì model chưa đọc các lượt trước.</p></div>
      : <div className="retrieval-turns" aria-label="Câu hỏi và các đoạn truy xuất">{turns.map(turn => <article className="retrieval-turn" key={turn.id}>
        {turn.question && <p className="user-question"><strong>Bạn</strong><br />{turn.question}</p>}
        {turn.state === 'loading' && <p role="status">Đang tìm tài liệu và soạn câu trả lời… Lần đầu tải model có thể lâu hơn.</p>}
        {turn.state === 'error' && <div role="alert"><p className="error-text">{turn.error}</p><button className="secondary" disabled={busy} onClick={() => setQuestion(turn.question)}>Đưa câu hỏi vào ô nhập để thử lại</button></div>}
        {turn.state === 'done' && <div>
          <p className="answer-label">{turn.result.status === 'answered' ? 'Trợ lý Cơ sở dữ liệu' : 'Cần thêm thông tin'}</p>
          <div className="assistant-answer">{turn.result.answer}</div>
          {turn.result.quiz_id && <QuizCard id={turn.result.quiz_id} workspace={workspace} token={token} onUnauthorized={onUnauthorized} />}
          {turn.result.roadmap_id && <PlanCard id={turn.result.roadmap_id} workspace={workspace} token={token} onUnauthorized={onUnauthorized} />}
          {turn.result.sources.length > 0 && <p className="retrieval-note">Nguồn được ghi trong từng phần trả lời. Nội dung do AI tạo có thể sai; hãy đối chiếu tài liệu.</p>}
          {turn.result.coverage && <div className="summary-scope"><strong>Phạm vi tóm tắt: {turn.result.coverage.topic}</strong><p>{turn.result.coverage.selected_chunks}/{turn.result.coverage.matched_chunks} đoạn khớp từ khóa · {turn.result.coverage.selected_pages} trang. {turn.result.coverage.partial ? 'Chỉ bao phủ một phần.' : 'Đã dùng các đoạn khớp trong phạm vi quét.'}</p><p>{turn.result.coverage.limitation}</p><p>{turn.result.coverage.unavailable_documents || 0} tài liệu trong workspace chưa sẵn sàng để xét.</p>{turn.result.coverage.scan_truncated && <p>Đã chạm giới hạn quét 3.000 đoạn; còn tài liệu chưa xét.</p>}</div>}
          {!turn.result.roadmap_id && <ol className="retrieval-results">{turn.result.sources.map(hit => <SourceCard key={hit.chunk_id} hit={hit} workspace={workspace} token={token} onUnauthorized={onUnauthorized} summary={turn.result.kind === 'summary'} />)}</ol>}
          <small>{turn.result.status !== 'no_documents' ? `${turn.result.model} · ` : ''}{(turn.result.elapsed_ms / 1000).toFixed(1)} giây</small>
        </div>}
      </article>)}<div ref={latest} /></div>}
    <form className="composer" onSubmit={send}>
      <label htmlFor="message" className="sr-only">Câu hỏi Cơ sở dữ liệu</label>
      <textarea id="message" rows={3} value={question} maxLength={2000} disabled={!workspace || busy || loading || Boolean(loadError)}
        placeholder={workspace ? 'Hỏi về Cơ sở dữ liệu trong tài liệu của bạn…' : 'Chọn workspace trước khi nhập câu hỏi.'}
        onChange={e => setQuestion(e.target.value)} onKeyDown={e => {
          if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send(e); }
        }} />
      <details className="chat-attachment"><summary>+ Đính kèm PDF</summary><PdfUpload compact token={token} workspace={workspace} onUnauthorized={onUnauthorized} disabled={busy} /></details>
      <div className="composer-actions"><small>Enter để gửi · Shift+Enter xuống dòng. Lịch sử được lưu sau khi có kết quả. Dừng chờ có thể vẫn lưu ở server; kiểm tra Lịch sử trước khi gửi lại. Mỗi hội thoại tối đa 50 lượt.</small>
        {busy ? <button type="button" className="secondary" onClick={() => active.current?.abort()}>Dừng chờ</button>
          : <button type="submit" disabled={!workspace || !question.trim() || loading || Boolean(loadError)}>Gửi ↑</button>}
      </div>
    </form>
  </section>;
}
