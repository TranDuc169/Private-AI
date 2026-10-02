import test from 'node:test';
import assert from 'node:assert/strict';
import { getHealth } from './api.js';

test('health calls backend and accepts only the agreed healthy response', async () => {
  const result = await getHealth({ fetchImpl: async (url) => {
    assert.ok(url.endsWith('/health'));
    return new Response(JSON.stringify({ status: 'ok', database: 'up' }));
  } });
  assert.equal(result.kind, 'success');
});

test('database outage is distinct from network failure', async () => {
  const result = await getHealth({ fetchImpl: async () => new Response(
    JSON.stringify({ status: 'degraded', database: 'down' }), { status: 503 },
  ) });
  assert.equal(result.kind, 'database-error');
  await assert.rejects(getHealth({ fetchImpl: async () => { throw new TypeError('network failure'); } }), /network failure/);
});

test('HTML fallback and unexpected JSON cannot report a healthy database', async () => {
  await assert.rejects(getHealth({ fetchImpl: async () => new Response('<html>Vite</html>') }), /JSON/);
  await assert.rejects(getHealth({ fetchImpl: async () => new Response('{"status":"ok"}') }), /contract/);
  await assert.rejects(getHealth({ fetchImpl: async () => new Response('null') }), /contract/);
});

test('unexpected HTTP errors cannot report success', async () => {
  await assert.rejects(getHealth({ fetchImpl: async () => new Response('{"detail":"error"}', { status: 500 }) }), /HTTP 500/);
});
