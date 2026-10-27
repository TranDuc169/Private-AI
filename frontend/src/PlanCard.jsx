import { useEffect, useRef, useState } from 'react';
import { apiRequest } from './api.js';
import SourceCard from './SourceCard.jsx';

export default function PlanCard({ id, workspace, token, onUnauthorized }) {
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(true);
  const [attempt, setAttempt] = useState(0);
  const active = useRef(null);
  const base = `/workspaces/${workspace.id}/plans/${id}`;
  useEffect(() => {
    const controller = new AbortController(); active.current = controller;
    setBusy(true); setError(''); setPlan(null);
    apiRequest(base, { token, signal: controller.signal }).then(result => {
      if (!controller.signal.aborted) setPlan(result);
    }).catch(e => { if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) onUnauthorized(); } })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => { active.current?.abort(); active.current = null; };
  }, [base, token, onUnauthorized, attempt]);
  async function mutate(step, done) {
    if (busy || !plan) return;
    const controller = new AbortController(); active.current = controller;
    setBusy(true); setError('');
    try {
      const result = await apiRequest(base + (step ? `/steps/${step}` : '/confirm'), {
        token, signal: controller.signal, method: step ? 'PATCH' : 'POST',
        body: step ? { revision: plan.revision, done } : { revision: plan.revision },
      });
      if (!controller.signal.aborted) setPlan(result);
    } catch (e) {
      if (!controller.signal.aborted) { setError(e.message + ' Tải lại để xem trạng thái đã lưu.'); if (e.status === 401) onUnauthorized(); }
    } finally { if (!controller.signal.aborted) setBusy(false); }
  }
  const completed = plan ? Object.values(plan.progress).filter(Boolean).length : 0;
  return <section className="plan-card" aria-label="Lộ trình học">
    <h3>{plan?.status === 'confirmed' ? 'Kế hoạch đã xác nhận' : 'Bản nháp lộ trình'}</h3>
    {busy && <p role="status">Đang tải/lưu kế hoạch…</p>}
    {error && <p role="alert">{error}</p>}
    <button className="secondary" type="button" disabled={busy} onClick={() => setAttempt(n => n + 1)}>Tải lại kế hoạch</button>
    {plan && <>
      <p>{plan.spec.request.sessions} buổi × {plan.spec.request.minutes_per_session} phút/buổi · Đã phân bổ {plan.spec.planned_minutes}/{plan.spec.budget_minutes} phút.</p>
      <p>{plan.spec.assumptions}</p>
      <p>{plan.spec.limitations}</p>
      <p><strong>{completed}/{plan.spec.steps.length} bước tự đánh dấu hoàn thành</strong> — không phải điểm đánh giá thành thạo.</p>
      {plan.status === 'draft' && <button type="button" disabled={busy || Boolean(error)} onClick={() => mutate(null)}>Xác nhận kế hoạch này</button>}
      <ol className="plan-steps">{plan.spec.steps.map((step, index) => <li key={step.key}>
        <h4>{index + 1}. {step.title} · {step.minutes} phút</h4>
        <p><strong>Học trước:</strong> {step.prerequisites.length ? step.prerequisites.map(key => plan.spec.steps.find(s => s.key === key)?.title || key).join(', ') : 'Bắt đầu tại đây (theo mức nền đã khai).'}</p>
        <p><strong>Mục tiêu:</strong> {step.objective}</p><p><strong>Hoạt động:</strong> {step.activity}</p>
        <p>{step.schedule.map(item => `Buổi ${item.session}: ${item.minutes} phút`).join(' · ')}</p>
        <label className="plan-check"><input type="checkbox" checked={Boolean(plan.progress[step.key])}
          disabled={busy || Boolean(error) || plan.status !== 'confirmed'}
          onChange={e => mutate(step.key, e.target.checked)} /> Tôi đã hoàn thành bước {index + 1}</label>
        <ol className="retrieval-results">{plan.spec.sources.filter(source => step.source_ids.includes(source.source_id)).map(source =>
          <SourceCard key={source.chunk_id} hit={source} workspace={workspace} token={token} onUnauthorized={onUnauthorized} summary />)}</ol>
      </li>)}</ol>
    </>}
  </section>;
}
