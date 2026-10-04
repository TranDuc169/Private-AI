import { useEffect, useRef, useState } from 'react';
import { apiRequest } from './api.js';

export function Login({ onLogin, notice }) {
  const [register, setRegister] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    const body = { email: values.get('email'), password: values.get('password') };
    setBusy(true); setError('');
    try {
      if (register) await apiRequest('/auth/register', { method: 'POST', body });
      onLogin(await apiRequest('/auth/login', { method: 'POST', body }));
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  return <section className="account-panel">
    <h2>{register ? 'Tạo tài khoản' : 'Đăng nhập'}</h2>
    <p>Mỗi tài khoản có workspace, tài liệu và lịch sử riêng.</p>
    {notice && <p role="status">{notice}</p>}
    <form onSubmit={submit} className="stack">
      <label>Email<input name="email" type="email" autoComplete="email" required maxLength={320} disabled={busy} /></label>
      <label>Mật khẩu<input name="password" type="password" autoComplete={register ? 'new-password' : 'current-password'} required minLength={8} maxLength={128} disabled={busy} /></label>
      <small>Mật khẩu từ 8 đến 128 ký tự.</small>
      {error && <p role="alert" className="error-text">{error}</p>}
      <button disabled={busy}>{busy ? 'Đang xử lý…' : register ? 'Đăng ký và đăng nhập' : 'Đăng nhập'}</button>
      <button type="button" className="secondary" disabled={busy} onClick={() => { setRegister(!register); setError(''); }}>{register ? 'Đã có tài khoản' : 'Chưa có tài khoản? Đăng ký'}</button>
    </form>
  </section>;
}

export function WorkspacePicker({ token, selected, onSelect, onUnauthorized }) {
  const [items, setItems] = useState([]);
  const [name, setName] = useState('');
  const [rename, setRename] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(true);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    const controller = new AbortController();
    apiRequest('/workspaces', { token, signal: controller.signal }).then(setItems).catch(e => {
      if (e.name !== 'AbortError') { setError(e.message); if (e.status === 401) onUnauthorized(); }
    }).finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => { mounted.current = false; controller.abort(); };
  }, [token, onUnauthorized]);
  useEffect(() => { setRename(selected?.name || ''); setConfirmDelete(false); }, [selected]);
  async function mutate(kind) {
    setBusy(true); setError('');
    const id = selected?.id;
    try {
      const result = await apiRequest(kind === 'create' ? '/workspaces' : `/workspaces/${id}`, {
        token, method: kind === 'create' ? 'POST' : kind === 'rename' ? 'PATCH' : 'DELETE',
        body: kind === 'delete' ? undefined : { name: kind === 'create' ? name : rename },
      });
      if (!mounted.current) return;
      if (kind === 'create') { setItems(old => [...old, result]); setName(''); onSelect(result); }
      if (kind === 'rename') { setItems(old => old.map(item => item.id === id ? result : item)); onSelect(result); }
      if (kind === 'delete') { setItems(old => old.filter(item => item.id !== id)); onSelect(null); }
    } catch (e) { if (mounted.current) { setError(e.message); if (e.status === 401) onUnauthorized(); } }
    finally { if (mounted.current) setBusy(false); }
  }
  return <section className="workspace-box stack">
    <label>WORKSPACE<select aria-label="Chọn workspace" value={selected?.id || ''} disabled={busy} onChange={e => onSelect(items.find(item => item.id === e.target.value) || null)}>
      <option value="">Chọn workspace</option>{items.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
    </select></label>
    {!busy && items.length === 0 && <small>Chưa có workspace. Tạo workspace đầu tiên bên dưới.</small>}
    <form className="stack" onSubmit={e => { e.preventDefault(); mutate('create'); }}>
      <label>Tên workspace mới<input value={name} onChange={e => setName(e.target.value)} required maxLength={200} disabled={busy} /></label>
      <button disabled={busy || !name.trim()}>Tạo workspace</button>
    </form>
    {selected && <>
      <form className="stack" onSubmit={e => { e.preventDefault(); mutate('rename'); }}>
        <label>Đổi tên<input value={rename} onChange={e => setRename(e.target.value)} required maxLength={200} disabled={busy} /></label>
        <button className="secondary" disabled={busy || !rename.trim()}>Lưu tên</button>
      </form>
      {confirmDelete ? <div className="stack"><p>Xóa workspace “{selected.name}”? Chỉ xóa được workspace trống.</p><button disabled={busy} onClick={() => mutate('delete')}>Xác nhận xóa</button><button disabled={busy} className="secondary" onClick={() => setConfirmDelete(false)}>Hủy</button></div> : <button disabled={busy} className="secondary" onClick={() => setConfirmDelete(true)}>Xóa workspace</button>}
    </>}
    {busy && <small role="status">Đang xử lý workspace…</small>}
    {error && <p role="alert" className="error-text">{error}</p>}
  </section>;
}

export function WorkspaceList({ token, workspace, kind, onUnauthorized }) {
  const [state, setState] = useState({ loading: true, items: [], error: '' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setState({ loading: true, items: [], error: '' });
    apiRequest(`/workspaces/${workspace.id}/${kind}`, { token, signal: controller.signal })
      .then(items => { if (!controller.signal.aborted) setState({ loading: false, items, error: '' }); })
      .catch(e => { if (!controller.signal.aborted) { setState({ loading: false, items: [], error: e.message }); if (e.status === 401) onUnauthorized(); } });
    return () => controller.abort();
  }, [token, workspace.id, kind, onUnauthorized, attempt]);
  return <section className="data-panel"><h2>{kind === 'documents' ? 'Tài liệu' : 'Lịch sử hội thoại'} · {workspace.name}</h2>
    {state.loading ? <p role="status">Đang tải…</p> : state.error ? <><p role="alert">{state.error}</p><button onClick={() => setAttempt(n => n + 1)}>Thử lại</button></> : state.items.length ? <ul>{state.items.map(item => <li key={item.id}>{item.filename || item.title}</li>)}</ul> : <p>Workspace này chưa có {kind === 'documents' ? 'tài liệu' : 'hội thoại'}.</p>}
    <small>{kind === 'documents' ? 'Chức năng tải PDF sẽ được bổ sung sau.' : 'Chat AI và mở nội dung hội thoại sẽ được bổ sung sau.'}</small>
  </section>;
}
