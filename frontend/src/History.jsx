import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest } from "./api.js";

export default function History({ workspace, token, onUnauthorized }) {
  const [state, setState] = useState({ loading: true, items: [], error: "" });
  const [attempt, setAttempt] = useState(0);
  const [search, setSearch] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setState({ loading: true, items: [], error: "" });
    apiRequest(`/workspaces/${workspace.id}/conversations`, {
      token,
      signal: controller.signal,
    })
      .then((items) => {
        if (!controller.signal.aborted)
          setState({
            loading: false,
            items: [...items].sort(
              (a, b) => new Date(b.created_at) - new Date(a.created_at),
            ),
            error: "",
          });
      })
      .catch((e) => {
        if (!controller.signal.aborted) {
          setState({ loading: false, items: [], error: e.message });
          if (e.status === 401) onUnauthorized();
        }
      });
    return () => controller.abort();
  }, [workspace.id, token, onUnauthorized, attempt]);
  const filtered = state.items.filter((item) =>
    item.title.toLocaleLowerCase("vi").includes(search.toLocaleLowerCase("vi")),
  );
  return (
    <section className="data-panel history-page">
      <span className="eyebrow">TIẾP TỤC ĐIỀU BẠN ĐANG KHÁM PHÁ</span>
      <div className="section-heading">
        <div>
          <h2>Những cuộc trò chuyện của bạn</h2>
          <p>
            Mở lại câu trả lời, lộ trình và bài luyện tập trong {workspace.name}
            .
          </p>
        </div>
        <Link className="button-link" to="/">
          + Hội thoại mới
        </Link>
      </div>
      <label className="history-search">
        Tìm trong lịch sử
        <input
          type="search"
          placeholder="Tìm theo tên hội thoại…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </label>
      {state.loading ? (
        <p role="status">Đang tải lịch sử…</p>
      ) : state.error ? (
        <div role="alert">
          <p>{state.error}</p>
          <button onClick={() => setAttempt((n) => n + 1)}>Thử lại</button>
        </div>
      ) : filtered.length ? (
        <ul className="history-list">
          {filtered.map((item) => (
            <li key={item.id}>
              <Link to={`/chat/${item.id}`}>
                <span className="history-symbol" aria-hidden="true">
                  ↗
                </span>
                <span>
                  <strong>{item.title}</strong>
                  <small>
                    {new Date(item.created_at).toLocaleString("vi-VN")}
                  </small>
                </span>
                <span aria-hidden="true">→</span>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <div className="empty">
          <h3>
            {state.items.length
              ? "Chưa tìm thấy hội thoại phù hợp"
              : "Câu hỏi đầu tiên đang chờ bạn"}
          </h3>
          <p>
            {state.items.length
              ? "Thử một từ khóa khác."
              : "Gửi câu hỏi ở Chat chung để bắt đầu lưu hành trình học."}
          </p>
        </div>
      )}
      <p>
        Lịch sử lưu trong database theo workspace. Nguồn trong câu trả lời là
        bản chụp tại thời điểm trả lời.
      </p>
    </section>
  );
}
