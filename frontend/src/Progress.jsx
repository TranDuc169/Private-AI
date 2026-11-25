import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest } from "./api.js";
import { extractActivity, summarizeProgress, readBatches } from "./progress.js";

const initial = {
  kind: "loading",
  plans: [],
  quizzes: [],
  conversations: 0,
  errors: [],
};
export default function Progress({ workspace, token, onUnauthorized }) {
  const [state, setState] = useState(initial);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setState(initial);
    const opts = { token, signal: controller.signal };
    const root = `/workspaces/${workspace.id}`;
    async function load() {
      try {
        const index = await apiRequest(`${root}/conversations`, opts);
        // Bounded reads avoid flooding the API on large workspaces.
        const batch = [...index]
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
          .slice(0, 50);
        const details = await readBatches(
          batch,
          (c) => apiRequest(`${root}/conversations/${c.id}`, opts),
          controller.signal,
        );
        const errors = details
          .filter((x) => x.status === "rejected")
          .map((x) => x.reason);
        const conversations = details
          .filter((x) => x.status === "fulfilled")
          .map((x) => x.value);
        const activity = extractActivity(conversations);
        const [plans, quizzes] = await Promise.all([
          readBatches(
            activity.plans,
            (item) => apiRequest(`${root}/plans/${item.id}`, opts),
            controller.signal,
          ),
          readBatches(
            activity.quizzes,
            (item) => apiRequest(`${root}/quizzes/${item.id}`, opts),
            controller.signal,
          ),
        ]);
        const resolvedPlans = plans.flatMap((x, i) =>
          x.status === "fulfilled"
            ? [{ ...activity.plans[i], ...x.value }]
            : [],
        );
        const resolvedQuizzes = quizzes.flatMap((x, i) =>
          x.status === "fulfilled"
            ? [{ ...activity.quizzes[i], ...x.value }]
            : [],
        );
        errors.push(
          ...plans.filter((x) => x.status === "rejected").map((x) => x.reason),
          ...quizzes
            .filter((x) => x.status === "rejected")
            .map((x) => x.reason),
        );
        if (!controller.signal.aborted) {
          if (errors.some((x) => x.status === 401)) onUnauthorized();
          else
            setState({
              kind: errors.length ? "partial" : "ready",
              plans: resolvedPlans,
              quizzes: resolvedQuizzes,
              conversations: index.length,
              errors,
            });
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          if (error.status === 401) onUnauthorized();
          else setState({ ...initial, kind: "error", errors: [error] });
        }
      }
    }
    load();
    return () => controller.abort();
  }, [workspace.id, token, onUnauthorized, retry]);
  const summary = summarizeProgress(state.plans, state.quizzes);
  return (
    <section className="progress-page" aria-label="Tiến độ học tập">
      <div className="progress-heading">
        <div>
          <h2>Tiến độ học tập</h2>
          <p>
            Thống kê từ kế hoạch và bài luyện tập đã lưu trên API của workspace{" "}
            <strong>{workspace.name}</strong>.
          </p>
        </div>
        <button
          className="secondary"
          onClick={() => setRetry((v) => v + 1)}
          disabled={state.kind === "loading"}
        >
          Cập nhật dữ liệu
        </button>
      </div>
      {state.kind === "loading" && (
        <p role="status">Đang đọc hội thoại, kế hoạch và kết quả luyện tập…</p>
      )}
      {state.kind === "error" && (
        <div role="alert">
          <p>Không tải được tiến độ: {state.errors[0]?.message}</p>
          <button onClick={() => setRetry((v) => v + 1)}>Thử lại</button>
        </div>
      )}
      {state.kind === "partial" && (
        <p role="alert">
          Một số dữ liệu không tải được. Số liệu bên dưới chưa đầy đủ; hãy thử
          cập nhật lại.
        </p>
      )}
      {state.kind !== "loading" && state.kind !== "error" && (
        <>
          <div className="progress-grid">
            <article>
              <span>Hội thoại đã lưu</span>
              <strong>{state.conversations}</strong>
            </article>
            <article>
              <span>Kế hoạch đã xác nhận</span>
              <strong>{summary.plans}</strong>
            </article>
            <article>
              <span>Bước tự đánh dấu</span>
              <strong>
                {summary.completedSteps}/{summary.totalSteps}
              </strong>
            </article>
            <article>
              <span>Bài quiz đã nộp</span>
              <strong>{summary.submitted}</strong>
            </article>
            <article>
              <span>Câu trả lời đúng</span>
              <strong>
                {summary.correct}/{summary.questions}
              </strong>
            </article>
          </div>
          <p className="retrieval-note">
            Checklist là tiến độ tự khai, không đo mức độ thành thạo. Kế hoạch
            và quiz được tổng hợp từ tối đa 50 hội thoại mới nhất; số hội thoại
            đã lưu là tổng danh sách API.
          </p>
          <section className="progress-section">
            <h3>Lộ trình học</h3>
            {!state.plans.length ? (
              <p>
                Chưa tìm thấy kế hoạch trong phạm vi đã kiểm tra. Tạo roadmap ở
                Chat chung để bắt đầu.
              </p>
            ) : (
              <ul>
                {state.plans.map((plan) => (
                  <li key={plan.id}>
                    <Link to={`/chat/${plan.conversationId}#plan-${plan.id}`}>
                      {plan.spec?.request?.goal || plan.title || "Kế hoạch học"}
                    </Link>
                    <span>
                      {
                        (plan.spec?.steps || []).filter(
                          (step) => plan.progress?.[step.key] === true,
                        ).length
                      }
                      /{plan.spec?.steps?.length || 0} bước ·{" "}
                      {plan.status === "confirmed" ? "Đã xác nhận" : "Bản nháp"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section className="progress-section">
            <h3>Bài luyện tập</h3>
            {!state.quizzes.length ? (
              <p>Chưa có quiz trong lịch sử được kiểm tra.</p>
            ) : (
              <ul>
                {state.quizzes.map((quiz) => (
                  <li key={quiz.id}>
                    <Link to={`/chat/${quiz.conversationId}`}>
                      {quiz.topic || quiz.title || "Bài luyện tập"}
                    </Link>
                    <span>
                      {quiz.result
                        ? `${quiz.result.score}/${quiz.result.total} đúng`
                        : quiz.status === "draft"
                          ? "Bản nháp chưa duyệt"
                          : "Chưa nộp"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </section>
  );
}
