import test from 'node:test';
import assert from 'node:assert/strict';
import { extractActivity, summarizeProgress } from './progress.js';

test('aggregates only assistant references and de-duplicates ids', () => {
  const activity = extractActivity([{ id: 'chat-1', title: 'SQL', messages: [
    { role: 'user', result: { quiz_id: 'forged' } },
    { role: 'assistant', result: { roadmap_id: 'p1', quiz_id: 'q1' } },
    { role: 'assistant', result: { quiz_id: 'q1' } },
  ] }]);
  assert.deepEqual(activity.plans.map(item => item.id), ['p1']);
  assert.deepEqual(activity.quizzes.map(item => item.id), ['q1']);
});

test('only confirmed checklist and submitted quiz count as progress', () => {
  assert.deepEqual(summarizeProgress([
    { status: 'confirmed', progress: { a: true, b: false }, spec: { steps: [{}, {}] } },
    { status: 'draft', progress: { c: true }, spec: { steps: [{}] } },
  ], [
    { status: 'approved', result: { score: 1, total: 2 } },
    { status: 'draft', result: null },
  ]), { plans: 1, completedSteps: 1, totalSteps: 2, submitted: 1, correct: 1, questions: 2 });
});
