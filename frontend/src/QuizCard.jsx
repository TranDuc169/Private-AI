import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from './api.js';
import SourceCard from './SourceCard.jsx';

export default function QuizCard({ id, workspace, token, onUnauthorized }) {
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const active = useRef(null);
  const path = `/workspaces/${workspace.id}/quizzes/${id}`;
  useEffect(() => {
    const controller = new AbortController(); active.current = controller;
    setQuiz(null); setError(''); setBusy(false); setAnswers({});
    apiRequest(path, { token, signal: controller.signal }).then(data => {
      if (!controller.signal.aborted) setQuiz(data);
    }).catch(e => { if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) onUnauthorized(); } });
    return () => { active.current?.abort(); active.current = null; };
  }, [path, token, reload, onUnauthorized]);
  async function submit() {
    if (busy || !quiz || quiz.result || quiz.questions.some((_, i) => answers[i] === undefined)) return;
    const controller = new AbortController(); active.current = controller;
    setBusy(true); setError('');
    try {
      const data = await apiRequest(`${path}/submit`, { token, method: 'POST', signal: controller.signal,
        body: { answers: quiz.questions.map((_, i) => answers[i]) } });
      if (!controller.signal.aborted) setQuiz(data);
    } catch (e) { if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) onUnauthorized(); } }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }
  if (!quiz) return <section className="quiz-card"><p role="status">{error || 'Đang mở bài luyện tập…'}</p>{error && <button onClick={() => setReload(n => n + 1)}>Tải lại quiz</button>}</section>;
  const result = quiz.result;
  return <section className="quiz-card" aria-label="Bài luyện tập">
    <h3>Quiz · {quiz.topic}</h3><p className="retrieval-note">{quiz.review}</p>
    {quiz.status === 'draft' && <p role="status">Bản nháp AI: chỉ xem câu hỏi, chưa được phép nộp hoặc chấm. Dùng “Quiz {quiz.topic}” để mở bộ demo đã đối chiếu nguồn.</p>}
    {quiz.questions.map((q, i) => <fieldset key={i} disabled={busy || !!result || quiz.status !== 'approved'}>
      <legend>{i + 1}. {q.question}</legend>
      {q.choices.map((choice, j) => <label key={j}><input type="radio" name={`${id}-${i}`} checked={(result ? result.answers[i] : answers[i]) === j}
        onChange={() => setAnswers(a => ({ ...a, [i]: j }))} /> {String.fromCharCode(65+j)}. {choice}</label>)}
      {result && <div className="quiz-feedback"><strong>{result.answers[i] === result.feedback[i].correct ? 'Đúng' : 'Chưa đúng'} · Bạn chọn {String.fromCharCode(65+result.answers[i])} · Đáp án {String.fromCharCode(65+result.feedback[i].correct)}</strong><p>{result.feedback[i].explanation} [{result.feedback[i].source_id}]</p></div>}
    </fieldset>)}
    {!result && quiz.status === 'approved' && <button disabled={busy || quiz.questions.some((_, i) => answers[i] === undefined)} onClick={submit}>{busy ? 'Đang lưu kết quả…' : 'Nộp bài'}</button>}
    {result && <><p role="status"><strong>Kết quả: {result.score}/{result.total} câu đúng.</strong> Đây là kết quả bài luyện tập, không chứng nhận thành thạo.</p>
      <ol className="retrieval-results">{result.sources.map(hit => <SourceCard key={hit.chunk_id} hit={hit} workspace={workspace} token={token} onUnauthorized={onUnauthorized} />)}</ol>
      <p>Muốn luyện lại, gửi yêu cầu quiz mới trong chat. Kết quả này được giữ nguyên.</p></>}
    {quiz.related_plan && <p><Link to={`/chat/${quiz.related_plan.conversation_id}#plan-${quiz.related_plan.plan_id}-${quiz.related_plan.step_key}`}>Quay lại kế hoạch · bước {quiz.related_plan.step_key}</Link></p>}
    {error && <p role="alert">{error}</p>}<button className="secondary" disabled={busy} onClick={() => setReload(n => n + 1)}>Tải lại quiz</button>
  </section>;
}
