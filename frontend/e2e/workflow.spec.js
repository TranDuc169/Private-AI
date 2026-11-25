import { test, expect } from "@playwright/test";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

const apiBase = process.env.E2E_API_URL || "http://127.0.0.1:8000";
const pdf = fileURLToPath(
  new URL("../../docs/course/pdfs/02-sql-join.pdf", import.meta.url),
);

async function noOverflow(page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  expect(
    await page.locator(".suggestion").evaluateAll((items) =>
      items.every((item) => {
        const icon = item.querySelector("svg").getBoundingClientRect();
        const title = item.querySelector("strong").getBoundingClientRect();
        return icon.right <= title.left || icon.bottom <= title.top;
      }),
    ),
  ).toBe(true);
}

async function login(page, email, password) {
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(page.getByLabel("Chọn workspace")).toBeVisible();
}

for (const width of [1440, 390]) {
  test(`real API: account, workspace, saved chat, PDF, history and isolation (${width}px)`, async ({
    page,
    request,
  }) => {
    await page.setViewportSize({ width, height: 1000 });
    const email = `khanh-e2e-${randomUUID()}@example.com`;
    const password = randomUUID();
    await page.goto("/");
    await expect(
      page.getByText("Đã kết nối FastAPI và truy vấn PostgreSQL thành công."),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Chưa có tài khoản? Đăng ký" })
      .click();
    await page.getByLabel("Email", { exact: true }).fill(email);
    await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
    await page
      .getByRole("button", { name: "Đăng ký và đăng nhập", exact: true })
      .click();
    await page.getByText("Quản lý workspace", { exact: true }).click();
    await page.getByLabel("Tên workspace mới").fill("Kiểm thử CSDL");
    await page
      .getByRole("button", { name: "Tạo workspace", exact: true })
      .click();
    await expect(page.getByLabel("Chọn workspace")).not.toHaveValue("");
    const workspaceId = await page.getByLabel("Chọn workspace").inputValue();
    await page.getByText("Quản lý workspace", { exact: true }).click();
    await page.screenshot({
      path: `/tmp/private-ai-chat-${width}.png`,
      fullPage: true,
    });
    await noOverflow(page);
    await page.getByRole("button", { name: /Hiểu một khái niệm/ }).click();
    await expect(page.getByLabel("Câu hỏi Cơ sở dữ liệu")).toHaveValue(
      "LEFT JOIN khác INNER JOIN thế nào?",
    );
    await page.getByRole("button", { name: "Gửi ↑" }).click();
    await expect(page).toHaveURL(/\/chat\//);
    await expect(page.locator(".assistant-answer")).toContainText(
      "Workspace chưa có đoạn tài liệu sẵn sàng",
    );
    const conversationUrl = page.url();
    await page.getByRole("navigation").getByText("Lịch sử hội thoại").click();
    await page.getByRole("searchbox").fill("LEFT JOIN");
    await page.locator(".history-list a").click();
    await expect(page).toHaveURL(conversationUrl);
    await expect(page.locator(".assistant-answer")).toContainText(
      "Workspace chưa có đoạn tài liệu sẵn sàng",
    );
    await page.reload();
    await login(page, email, password);
    await page.getByLabel("Chọn workspace").selectOption(workspaceId);
    await page.getByRole("navigation").getByText("Lịch sử hội thoại").click();
    await page.locator(".history-list a").click();
    await expect(page.locator(".assistant-answer")).toContainText(
      "Workspace chưa có đoạn tài liệu sẵn sàng",
    );
    // Upload and text extraction are real; do not require a model to validate saved PDF rendering.
    const auth = await request.post(`${apiBase}/auth/login`, {
      data: { email, password },
    });
    expect(auth.ok()).toBeTruthy();
    const { access_token } = await auth.json();
    const headers = { Authorization: `Bearer ${access_token}` };
    const fs = await import("node:fs/promises");
    const uploaded = await request.post(
      `${apiBase}/workspaces/${workspaceId}/documents`,
      {
        headers,
        multipart: {
          file: {
            name: path.basename(pdf),
            mimeType: "application/pdf",
            buffer: await fs.readFile(pdf),
          },
        },
      },
    );
    expect(uploaded.status()).toBe(201);
    const document = await uploaded.json();
    const processed = await request.post(
      `${apiBase}/workspaces/${workspaceId}/documents/${document.id}/process`,
      { headers },
    );
    expect((await processed.json()).status).toBe("ready");
    await page
      .getByRole("navigation")
      .getByText("Tài liệu", { exact: true })
      .click();
    await expect(page.locator(".document-list")).toContainText(
      "02-sql-join.pdf",
    );
    await page.getByRole("button", { name: /Xem văn bản/ }).click();
    await expect(
      page.getByRole("region", { name: "Văn bản trích xuất" }).locator("pre"),
    ).not.toBeEmpty();
    await noOverflow(page);
    await page.getByRole("button", { name: /Xóa ·/ }).click();
    await page
      .getByRole("button", { name: "Xác nhận xóa", exact: true })
      .click();
    await expect(
      page.getByText("Workspace này chưa có tài liệu.", { exact: true }),
    ).toBeVisible();
    await page.getByRole("navigation").getByText("Tiến độ học tập").click();
    await expect(page.locator(".progress-grid article").first()).toContainText(
      "1",
    );
    await page.getByText("Quản lý workspace", { exact: true }).click();
    await page.getByLabel("Tên workspace mới").fill("Workspace riêng");
    await page
      .getByRole("button", { name: "Tạo workspace", exact: true })
      .click();
    await expect(page.getByLabel("Chọn workspace")).not.toHaveValue(
      workspaceId,
    );
    await page.getByRole("navigation").getByText("Lịch sử hội thoại").click();
    await expect(page.getByText("Câu hỏi đầu tiên đang chờ bạn")).toBeVisible();
    await expect(page.locator(".history-list")).toHaveCount(0);
    await page.getByRole("navigation").getByText("Tiến độ học tập").click();
    await expect(page.locator(".progress-grid article").first()).toContainText(
      "0",
    );
    await noOverflow(page);
    await page.getByRole("button", { name: "Đăng xuất", exact: true }).click();
    await expect(
      page.getByRole("heading", { name: "Đăng nhập", exact: true }),
    ).toBeVisible();
  });
}

// These isolated UI fixtures validate card interactions only, never model quality or real API readiness.
test("contract fixtures: roadmap revisions, quiz submission, persisted progress and expired session", async ({
  page,
}) => {
  const source = {
    source_id: 1,
    chunk_id: "chunk-1",
    filename: "sql-join.pdf",
    page_number: 1,
    score: 0.8,
    text: "JOIN kết hợp các hàng từ nhiều bảng.",
  };
  let sourceDeleted = false;
  let plan = {
    id: "plan-1",
    status: "draft",
    revision: 0,
    progress: { join: false },
    spec: {
      request: { goal: "Học SQL JOIN", sessions: 1, minutes_per_session: 45 },
      planned_minutes: 45,
      budget_minutes: 45,
      assumptions: "Nền tảng cơ bản",
      limitations: "Tiến độ tự khai",
      sources: [source],
      steps: [
        {
          key: "join",
          title: "SQL JOIN",
          minutes: 45,
          prerequisites: [],
          objective: "Phân biệt JOIN",
          activity: "Đọc tài liệu và luyện tập",
          schedule: [{ session: 1, minutes: 45 }],
          source_ids: [1],
        },
      ],
    },
  };
  let quiz = {
    id: "quiz-1",
    status: "approved",
    topic: "SQL JOIN",
    review: "Bộ câu hỏi kiểm thử giao diện",
    questions: [
      {
        question: "JOIN dùng để làm gì?",
        choices: ["Kết hợp bảng", "Xóa bảng", "Tạo user", "Sao lưu"],
      },
    ],
    result: null,
  };
  const conversation = {
    id: "chat-1",
    title: "Học SQL JOIN",
    revision: 1,
    created_at: "2026-11-08T00:00:00Z",
    messages: [
      {
        id: "m1",
        role: "assistant",
        content: "Lộ trình và quiz",
        result: {
          answer: "Lộ trình và quiz",
          status: "answered",
          sources: [],
          roadmap_id: "plan-1",
          quiz_id: "quiz-1",
          elapsed_ms: 1,
          model: "UI fixture",
        },
      },
    ],
  };
  let expired = false;
  await page.route(`${apiBase}/**`, async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const p = url.pathname;
    const json = (body, status = 200) => route.fulfill({ status, json: body });
    if (p === "/health") return json({ status: "ok", database: "up" });
    if (p === "/auth/login")
      return json({
        access_token: "ui-fixture",
        expires_in: 1800,
        user: { email: "fixture@example.com" },
      });
    if (expired) return json({ detail: "Phiên hết hạn" }, 401);
    if (p === "/workspaces") return json([{ id: "w1", name: "UI fixture" }]);
    if (p.endsWith("/conversations")) return json([conversation]);
    if (p.endsWith("/conversations/chat-1")) return json(conversation);
    if (p.endsWith("/plans/plan-1/confirm")) {
      expect(req.postDataJSON()).toEqual({ revision: 0 });
      plan = { ...plan, status: "confirmed", revision: 1 };
      return json(plan);
    }
    if (p.endsWith("/steps/join")) {
      expect(req.postDataJSON()).toEqual({ revision: 1, done: true });
      plan = { ...plan, revision: 2, progress: { join: true } };
      return json(plan);
    }
    if (p.endsWith("/sources/chunk-1"))
      return sourceDeleted
        ? json({ detail: "Nguồn không còn sẵn sàng" }, 404)
        : json({ ...source, text: "Đoạn nguồn hiện tại từ API kiểm thử." });
    if (p.endsWith("/plans/plan-1")) return json(plan);
    if (p.endsWith("/quizzes/quiz-1/submit")) {
      expect(req.postDataJSON()).toEqual({ answers: [0] });
      quiz = {
        ...quiz,
        result: {
          answers: [0],
          score: 1,
          total: 1,
          feedback: [
            { correct: 0, explanation: "Kết hợp các hàng", source_id: 1 },
          ],
          sources: [],
        },
      };
      return json(quiz);
    }
    if (p.endsWith("/quizzes/quiz-1")) return json(quiz);
    return json({ detail: "Unexpected test route" }, 404);
  });
  await page.goto("/");
  await login(page, "fixture@example.com", "fixture-password");
  await page.getByLabel("Chọn workspace").selectOption("w1");
  await page.getByRole("navigation").getByText("Lịch sử hội thoại").click();
  await page.locator(".history-list a").click();
  await page.locator(".plan-card summary").click();
  await page.getByRole("button", { name: "Mở đoạn nguồn hiện tại" }).click();
  await expect(
    page.getByText("Đoạn nguồn hiện tại từ API kiểm thử."),
  ).toBeVisible();
  sourceDeleted = true;
  await page.getByRole("button", { name: "Mở đoạn nguồn hiện tại" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Bản trích đã lưu vẫn nằm trong lịch sử",
  );
  await page.getByRole("button", { name: "Xác nhận kế hoạch này" }).click();
  await page.getByRole("checkbox").click();
  await expect(page.getByRole("checkbox")).toBeChecked();
  await expect(page.getByRole("progressbar")).toHaveAttribute("value", "1");
  await expect(
    page.getByRole("button", { name: "Nộp bài", exact: true }),
  ).toBeDisabled();
  await page.getByRole("radio").first().check();
  await page.getByRole("button", { name: "Nộp bài", exact: true }).click();
  await expect(page.getByText("Kết quả: 1/1 câu đúng.")).toBeVisible();
  await page.getByRole("navigation").getByText("Tiến độ học tập").click();
  await expect(page.locator(".progress-grid article").nth(2)).toContainText(
    "1/1",
  );
  await expect(page.locator(".progress-grid article").nth(4)).toContainText(
    "1/1",
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await noOverflow(page);
  await page.locator(".progress-section").first().getByRole("link").click();
  await expect(page.getByRole("checkbox")).toBeChecked();
  await expect(page.getByText("Kết quả: 1/1 câu đúng.")).toBeVisible();
  await noOverflow(page);
  await page.screenshot({
    path: "/tmp/private-ai-cards-mobile.png",
    fullPage: true,
  });
  expired = true;
  await page.getByRole("button", { name: "Tải lại kế hoạch" }).click();
  await expect(
    page.getByRole("heading", { name: "Đăng nhập", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("checkbox")).toHaveCount(0);
});
