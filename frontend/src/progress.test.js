import test from "node:test";
import assert from "node:assert/strict";
import { extractActivity, summarizeProgress, readBatches } from "./progress.js";

test("aggregates only assistant references and de-duplicates ids", () => {
  const activity = extractActivity([
    {
      id: "chat-1",
      title: "SQL",
      messages: [
        { role: "user", result: { quiz_id: "forged" } },
        { role: "assistant", result: { roadmap_id: "p1", quiz_id: "q1" } },
        { role: "assistant", result: { quiz_id: "q1" } },
      ],
    },
  ]);
  assert.deepEqual(
    activity.plans.map((item) => item.id),
    ["p1"],
  );
  assert.deepEqual(
    activity.quizzes.map((item) => item.id),
    ["q1"],
  );
});

test("only confirmed checklist and submitted quiz count as progress", () => {
  assert.deepEqual(
    summarizeProgress(
      [
        {
          status: "confirmed",
          progress: { a: true, b: false, stale: true },
          spec: { steps: [{ key: "a" }, { key: "b" }] },
        },
        { status: "draft", progress: { c: true }, spec: { steps: [{}] } },
      ],
      [
        { status: "approved", result: { score: 1, total: 2 } },
        { status: "draft", result: null },
      ],
    ),
    {
      plans: 1,
      completedSteps: 1,
      totalSteps: 2,
      submitted: 1,
      correct: 1,
      questions: 2,
    },
  );
});

test("API reads preserve order, report partial failures and limit concurrency", async () => {
  let active = 0;
  let peak = 0;
  const result = await readBatches(
    [1, 2, 3, 4, 5],
    async (value) => {
      peak = Math.max(peak, ++active);
      await new Promise((resolve) => setTimeout(resolve, 5));
      active--;
      if (value === 3) throw new Error("Unavailable");
      return value * 2;
    },
    new AbortController().signal,
    2,
  );
  assert.equal(peak, 2);
  assert.deepEqual(
    result.map((item) => (item.status === "fulfilled" ? item.value : "failed")),
    [2, 4, "failed", 8, 10],
  );
});

test("workspace cancellation prevents later batches from being requested", async () => {
  const controller = new AbortController();
  const seen = [];
  await assert.rejects(
    readBatches(
      [1, 2, 3],
      async (value) => {
        seen.push(value);
        controller.abort();
        return value;
      },
      controller.signal,
      1,
    ),
    { name: "AbortError" },
  );
  assert.deepEqual(seen, [1]);
});
