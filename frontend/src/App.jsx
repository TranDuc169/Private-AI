import { useCallback, useEffect, useRef, useState } from "react";
import {
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import Icon from "./Icon.jsx";
import { getHealth } from "./api.js";
import { Login, WorkspacePicker } from "./Account.jsx";
import Documents from "./Documents.jsx";
import Chat from "./Chat.jsx";
import History from "./History.jsx";
import Progress from "./Progress.jsx";

function SavedChat(props) {
  const { conversationId } = useParams();
  return (
    <Chat
      key={`${props.workspace?.id}-${conversationId}`}
      {...props}
      conversationId={conversationId}
    />
  );
}

function HealthStatus() {
  const [state, setState] = useState({
    kind: "loading",
    message: "Đang kiểm tra kết nối…",
  });
  const active = useRef(null);

  async function check() {
    active.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    setState({ kind: "loading", message: "Đang kiểm tra kết nối…" });
    const timer = setTimeout(() => controller.abort(), 8000);
    try {
      const next = await getHealth({ signal: controller.signal });
      if (active.current === controller) setState(next);
    } catch (error) {
      if (active.current === controller)
        setState({
          kind: "error",
          message:
            error.name === "AbortError"
              ? "Hết thời gian chờ API. Kiểm tra backend và thử lại."
              : error instanceof TypeError
                ? "Không gọi được API. Kiểm tra backend, địa chỉ API và CORS."
                : error.message,
        });
    } finally {
      clearTimeout(timer);
    }
  }

  useEffect(() => {
    check();
    return () => {
      active.current?.abort();
      active.current = null;
    };
  }, []);

  return (
    <section className="health" aria-label="Kết nối hệ thống">
      <div role="status" aria-live="polite" className="flex items-center gap-3">
        <span className={`dot ${state.kind}`} aria-hidden="true" />
        <span>{state.message}</span>
      </div>
      <button
        className="secondary"
        disabled={state.kind === "loading"}
        onClick={check}
      >
        Kiểm tra lại
      </button>
    </section>
  );
}

function EmptyState({ title, children }) {
  return (
    <div className="empty">
      <span className="empty-icon" aria-hidden="true">
        ◇
      </span>
      <h2>{title}</h2>
      <p>{children}</p>
    </div>
  );
}

export default function App() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const page =
    pathname === "/documents"
      ? "Thư viện tài liệu"
      : pathname === "/history"
        ? "Lịch sử hội thoại"
        : pathname === "/progress"
          ? "Tiến độ học tập"
          : "Góc học tập";
  // Keep JWT in memory: logout, reload and expiration clear private UI state.
  const [session, setSession] = useState(null);
  const [workspace, setWorkspace] = useState(null);
  const [notice, setNotice] = useState("");
  const expire = useCallback(() => {
    setSession(null);
    setWorkspace(null);
    setNotice("Phiên đã hết hạn. Vui lòng đăng nhập lại.");
  }, []);
  useEffect(() => {
    if (!session) return;
    const timer = setTimeout(expire, session.expires_in * 1000);
    return () => clearTimeout(timer);
  }, [session, expire]);
  const onLogin = (value) => {
    setWorkspace(null);
    setNotice("");
    setSession(value);
  };
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Đến nội dung chính
      </a>
      <aside className="sidebar">
        <Link to="/" className="brand">
          <span className="brand-icon">
            <Icon name="book" />
          </span>
          <div>
            Trợ lý CSDL<small>KHÔNG GIAN TỰ HỌC</small>
          </div>
        </Link>
        <div className="sidebar-caption">KHÔNG GIAN CỦA BẠN</div>
        {session ? (
          <WorkspacePicker
            key={session.access_token}
            token={session.access_token}
            selected={workspace}
            onSelect={(value) => {
              setWorkspace(value);
              navigate("/");
            }}
            onUnauthorized={expire}
          />
        ) : (
          <div className="workspace-box">
            Đăng nhập để mở không gian học tập riêng.
          </div>
        )}
        <nav aria-label="Điều hướng chính">
          <NavLink to="/" end>
            <Icon name="chat" />
            Chat chung
          </NavLink>
          <NavLink to="/documents">
            <Icon name="book" />
            Tài liệu
          </NavLink>
          <NavLink to="/history">
            <Icon name="history" />
            Lịch sử hội thoại
          </NavLink>
          <NavLink to="/progress">
            <Icon name="chart" />
            Tiến độ học tập
          </NavLink>
        </nav>
        <div className="sidebar-note">
          <Icon name="spark" />
          <strong>Mỗi ngày, hiểu thêm một chút.</strong>
          <p>
            Hỏi từ tài liệu, học theo lộ trình và tự kiểm tra kiến thức ngay
            trong chat.
          </p>
        </div>
        {session && (
          <div className="account-footer">
            <span className="avatar">
              {session.user.email[0].toUpperCase()}
            </span>
            <div>
              <p className="account-email">{session.user.email}</p>
              <button
                className="text-button"
                onClick={() => {
                  setSession(null);
                  setWorkspace(null);
                  setNotice("Đã đăng xuất.");
                }}
              >
                Đăng xuất
              </button>
            </div>
          </div>
        )}
      </aside>
      <main id="main-content" tabIndex={-1}>
        <header className="topbar">
          <div>
            <span className="eyebrow">
              CƠ SỞ DỮ LIỆU <span aria-hidden="true">/</span>{" "}
              {workspace?.name || "Bắt đầu hành trình"}
            </span>
            <h1>{page}</h1>
          </div>
          <span className="badge">
            <Icon name="spark" />
            Học từ nguồn của bạn
          </span>
        </header>
        <HealthStatus />
        {!session ? (
          <Login onLogin={onLogin} notice={notice} />
        ) : (
          <Routes>
            <Route
              path="/"
              element={
                <Chat
                  key={workspace?.id || "no-workspace"}
                  workspace={workspace}
                  token={session.access_token}
                  onUnauthorized={expire}
                />
              }
            />
            <Route
              path="/chat/:conversationId"
              element={
                <SavedChat
                  workspace={workspace}
                  token={session.access_token}
                  onUnauthorized={expire}
                />
              }
            />
            <Route
              path="/documents"
              element={
                workspace ? (
                  <Documents
                    key={`${workspace.id}-documents`}
                    token={session.access_token}
                    workspace={workspace}
                    onUnauthorized={expire}
                  />
                ) : (
                  <EmptyState title="Chưa chọn workspace">
                    Chọn workspace để xem tài liệu.
                  </EmptyState>
                )
              }
            />
            <Route
              path="/history"
              element={
                workspace ? (
                  <History
                    key={`${workspace.id}-history`}
                    token={session.access_token}
                    workspace={workspace}
                    onUnauthorized={expire}
                  />
                ) : (
                  <EmptyState title="Chưa chọn workspace">
                    Chọn workspace để xem lịch sử.
                  </EmptyState>
                )
              }
            />
            <Route
              path="/progress"
              element={
                workspace ? (
                  <Progress
                    key={`${workspace.id}-progress`}
                    token={session.access_token}
                    workspace={workspace}
                    onUnauthorized={expire}
                  />
                ) : (
                  <EmptyState title="Chưa chọn workspace">
                    Chọn workspace để xem tiến độ.
                  </EmptyState>
                )
              }
            />
            <Route
              path="*"
              element={
                <EmptyState title="Không tìm thấy trang">
                  Chọn Chat chung, Tài liệu, Lịch sử hoặc Tiến độ ở thanh điều
                  hướng.
                </EmptyState>
              }
            />
          </Routes>
        )}
      </main>
    </div>
  );
}
