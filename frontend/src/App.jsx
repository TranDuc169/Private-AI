import { useCallback, useEffect, useRef, useState } from 'react';
import { NavLink, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import { getHealth } from './api.js';
import { Login, WorkspacePicker } from './Account.jsx';
import Documents from './Documents.jsx';
import Chat from './Chat.jsx';
import History from './History.jsx';

function SavedChat(props) {
  const { conversationId } = useParams();
  return <Chat key={`${props.workspace?.id}-${conversationId}`} {...props} conversationId={conversationId} />;
}

function HealthStatus() {
  const [state, setState] = useState({ kind: 'loading', message: 'Đang kiểm tra kết nối…' });
  const active = useRef(null);

  async function check() {
    active.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    setState({ kind: 'loading', message: 'Đang kiểm tra kết nối…' });
    const timer = setTimeout(() => controller.abort(), 8000);
    try {
      const next = await getHealth({ signal: controller.signal });
      if (active.current === controller) setState(next);
    } catch (error) {
      if (active.current === controller) setState({
        kind: 'error',
        message: error.name === 'AbortError'
          ? 'Hết thời gian chờ API. Kiểm tra backend và thử lại.'
          : error instanceof TypeError
            ? 'Không gọi được API. Kiểm tra backend, địa chỉ API và CORS.'
            : error.message,
      });
    } finally {
      clearTimeout(timer);
    }
  }

  useEffect(() => {
    check();
    return () => { active.current?.abort(); active.current = null; };
  }, []);

  return <section className="health" aria-label="Kết nối hệ thống">
    <div role="status" aria-live="polite" className="flex items-center gap-3">
      <span className={`dot ${state.kind}`} aria-hidden="true" />
      <span>{state.message}</span>
    </div>
    <button className="secondary" disabled={state.kind === 'loading'} onClick={check}>Kiểm tra lại</button>
  </section>;
}

function EmptyState({ title, children }) {
  return <div className="empty"><span className="empty-icon" aria-hidden="true">◇</span>
    <h2>{title}</h2><p>{children}</p>
  </div>;
}

export default function App() {
  const navigate = useNavigate();
  // Keep JWT in memory: logout, reload and expiration clear private UI state.
  const [session, setSession] = useState(null);
  const [workspace, setWorkspace] = useState(null);
  const [notice, setNotice] = useState('');
  const expire = useCallback(() => { setSession(null); setWorkspace(null); setNotice('Phiên đã hết hạn. Vui lòng đăng nhập lại.'); }, []);
  useEffect(() => {
    if (!session) return;
    const timer = setTimeout(expire, session.expires_in * 1000);
    return () => clearTimeout(timer);
  }, [session, expire]);
  const onLogin = value => { setWorkspace(null); setNotice(''); setSession(value); };
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-icon">DB</span><div>Trợ lý CSDL<small>Học cùng tài liệu của bạn</small></div></div>
      {session ? <><p className="account-email">{session.user.email}</p><button className="secondary" onClick={() => { setSession(null); setWorkspace(null); setNotice('Đã đăng xuất.'); }}>Đăng xuất</button><WorkspacePicker key={session.access_token} token={session.access_token} selected={workspace} onSelect={value => { setWorkspace(value); navigate('/'); }} onUnauthorized={expire} /></> : <div className="workspace-box">Đăng nhập để quản lý workspace.</div>}
      <nav aria-label="Điều hướng chính">
        <NavLink to="/" end>Chat chung</NavLink>
        <NavLink to="/documents">Tài liệu</NavLink>
        <NavLink to="/history">Lịch sử hội thoại</NavLink>
      </nav>
      <p className="sidebar-note">Tài liệu và lịch sử sẽ được tải theo workspace đã chọn.</p>
    </aside>
    <main>
      <header><div><h1>Trợ lý học Cơ sở dữ liệu</h1></div><span className="badge">Hỏi đáp có nguồn</span></header>
      <HealthStatus />
      {!session ? <Login onLogin={onLogin} notice={notice} /> : <Routes>
        <Route path="/" element={<Chat key={workspace?.id || 'no-workspace'} workspace={workspace} token={session.access_token} onUnauthorized={expire} />} />
        <Route path="/chat/:conversationId" element={<SavedChat workspace={workspace} token={session.access_token} onUnauthorized={expire} />} />
        <Route path="/documents" element={workspace ? <Documents key={`${workspace.id}-documents`} token={session.access_token} workspace={workspace} onUnauthorized={expire} /> : <EmptyState title="Chưa chọn workspace">Chọn workspace để xem tài liệu.</EmptyState>} />
        <Route path="/history" element={workspace ? <History key={`${workspace.id}-history`} token={session.access_token} workspace={workspace} onUnauthorized={expire} /> : <EmptyState title="Chưa chọn workspace">Chọn workspace để xem lịch sử.</EmptyState>} />
        <Route path="*" element={<EmptyState title="Không tìm thấy trang">Chọn Chat chung, Tài liệu hoặc Lịch sử ở thanh điều hướng.</EmptyState>} />
      </Routes>}
    </main>
  </div>;
}
