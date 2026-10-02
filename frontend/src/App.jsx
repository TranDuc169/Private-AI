import { useEffect, useRef, useState } from 'react';
import { NavLink, Route, Routes } from 'react-router-dom';
import { getHealth } from './api.js';

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

function Chat() {
  return <section className="chat">
    <EmptyState title="Tri thức riêng, trong một cuộc trò chuyện">
      Hỏi đáp, tóm tắt, roadmap, checklist và quiz sẽ cùng dùng một ô chat.
      Chưa có workspace được chọn. API workspace và RAG chưa được triển khai.
    </EmptyState>
    <form className="composer" onSubmit={(event) => event.preventDefault()}>
      <label htmlFor="message" className="sr-only">Nội dung chat</label>
      <textarea id="message" rows={3} disabled placeholder="Chat sẽ khả dụng sau khi có workspace và API RAG." />
      <div className="flex items-center justify-between gap-4">
        <small>Tuần 2 · Chưa có chức năng trả lời AI</small>
        <button disabled>Gửi ↑</button>
      </div>
    </form>
  </section>;
}

export default function App() {
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-icon">P</span><div>Private AI<small>Knowledge Platform</small></div></div>
      <div className="workspace-box"><small>WORKSPACE</small><p>Chưa chọn workspace</p><span>Tạo và chọn workspace ở tuần 3.</span></div>
      <nav aria-label="Điều hướng chính">
        <NavLink to="/" end>Chat chung</NavLink>
        <NavLink to="/documents">Tài liệu</NavLink>
        <NavLink to="/history">Lịch sử hội thoại</NavLink>
      </nav>
      <p className="sidebar-note">Tài liệu và lịch sử sẽ được tải theo workspace đã chọn.</p>
      <div className="team">Đức · Backend / Database<br />Khánh · Frontend / UI</div>
    </aside>
    <main>
      <header><div><p className="eyebrow">ĐỒ ÁN 1 / TUẦN 02</p><h1>Private AI Knowledge Platform</h1></div><span className="badge">Khung kết nối</span></header>
      <HealthStatus />
      <Routes>
        <Route path="/" element={<Chat />} />
        <Route path="/documents" element={<EmptyState title="Chưa có workspace được chọn">Danh sách tài liệu chưa được tải. Upload và xử lý PDF bắt đầu ở tuần 4.</EmptyState>} />
        <Route path="/history" element={<EmptyState title="Chưa có lịch sử hội thoại">Lịch sử sẽ thuộc từng workspace. API lưu và mở lại hội thoại dự kiến ở tuần 10.</EmptyState>} />
        <Route path="*" element={<EmptyState title="Không tìm thấy trang">Chọn Chat chung, Tài liệu hoặc Lịch sử ở thanh điều hướng.</EmptyState>} />
      </Routes>
    </main>
  </div>;
}
