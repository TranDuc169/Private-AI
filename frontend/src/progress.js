// Workspace-scoped aggregates. No scores or plan completion are inferred from AI text.
export function extractActivity(conversations) {
  const plans = new Map();
  const quizzes = new Map();
  for (const conversation of conversations) {
    for (const message of conversation.messages || []) {
      if (message.role !== "assistant" || !message.result) continue;
      const result = message.result;
      if (result.roadmap_id)
        plans.set(result.roadmap_id, {
          id: result.roadmap_id,
          conversationId: conversation.id,
          title: conversation.title,
        });
      if (result.quiz_id)
        quizzes.set(result.quiz_id, {
          id: result.quiz_id,
          conversationId: conversation.id,
          title: conversation.title,
        });
    }
  }
  return { plans: [...plans.values()], quizzes: [...quizzes.values()] };
}

export function summarizeProgress(plans, quizzes) {
  const confirmed = plans.filter((item) => item.status === "confirmed");
  const completedSteps = confirmed.reduce(
    (total, item) =>
      total +
      (item.spec?.steps || []).filter(
        (step) => item.progress?.[step.key] === true,
      ).length,
    0,
  );
  const totalSteps = confirmed.reduce(
    (total, item) => total + (item.spec?.steps?.length || 0),
    0,
  );
  const submitted = quizzes.filter((item) => item.result);
  const correct = submitted.reduce(
    (total, item) => total + item.result.score,
    0,
  );
  const questions = submitted.reduce(
    (total, item) => total + item.result.total,
    0,
  );
  return {
    plans: confirmed.length,
    completedSteps,
    totalSteps,
    submitted: submitted.length,
    correct,
    questions,
  };
}

// Limit in-flight API reads and stop scheduling work when the workspace changes.
export async function readBatches(items, read, signal, size = 4) {
  const results = [];
  for (let offset = 0; offset < items.length; offset += size) {
    signal?.throwIfAborted();
    results.push(
      ...(await Promise.allSettled(
        items.slice(offset, offset + size).map(read),
      )),
    );
  }
  signal?.throwIfAborted();
  return results;
}
