import test from 'node:test';
import assert from 'node:assert/strict';
import { getHealth, apiRequest } from './api.js';
import { extractionNotice, uploadFailureNotice } from './pdfStatus.js';

test('upload feedback distinguishes extraction failures from rejected or uncertain uploads', () => {
  assert.equal(extractionNotice({ filename: 'notes.pdf', status: 'ready', page_count: 2 }).kind, 'warning');
  const failed = extractionNotice({ filename: 'scan.pdf', status: 'failed', error_message: 'OCR chưa hỗ trợ' });
  assert.equal(failed.kind, 'warning');
  assert.match(failed.title, /Tải lên thành công/);
  assert.match(failed.message, /OCR/);
  assert.equal(uploadFailureNotice({ status: 413, message: 'File quá lớn' }, null).title, 'Tải lên thất bại');
  assert.match(uploadFailureNotice(new TypeError('Failed to fetch'), null).title, /chưa xác nhận/);
  assert.match(uploadFailureNotice(new TypeError('Failed to fetch'), { id: 'saved' }).title, /File đã lưu/);
});

test('PDF upload sends FormData without overriding the multipart boundary', async () => {
  const form = new FormData(); form.append('file', new Blob(['%PDF-1.7'], { type: 'application/pdf' }), 'sample.pdf');
  await apiRequest('/workspaces/w/documents', { token: 'jwt', method: 'POST', body: form, fetchImpl: async (url, options) => {
    assert.equal(options.body, form);
    assert.equal(options.headers['Content-Type'], undefined);
    assert.equal(options.headers.Authorization, 'Bearer jwt');
    return Response.json({ status: 'uploaded' }, { status: 201 });
  } });
});

test('authenticated requests send bearer and JSON; delete accepts empty 204', async () => {
  const result = await apiRequest('/workspaces', { token: 'test-token', method: 'POST', body: { name: 'A' }, fetchImpl: async (url, options) => {
    assert.ok(url.endsWith('/workspaces'));
    assert.equal(options.headers.Authorization, 'Bearer test-token');
    assert.equal(options.body, JSON.stringify({ name: 'A' }));
    return Response.json({ id: 'a', name: 'A' }, { status: 201 });
  } });
  assert.equal(result.id, 'a');
  assert.equal(await apiRequest('/workspaces/a', { method: 'DELETE', fetchImpl: async () => new Response(null, { status: 204 }) }), null);
});

test('401 retains status for session reset; validation errors are readable', async () => {
  await assert.rejects(apiRequest('/workspaces', { fetchImpl: async () => Response.json({ detail: 'Expired' }, { status: 401 }) }), error => error.status === 401 && error.message === 'Expired');
  await assert.rejects(apiRequest('/workspaces', { fetchImpl: async () => Response.json({ detail: [{ msg: 'invalid' }] }, { status: 422 }) }), error => error.status === 422 && !error.message.includes('[object Object]'));
});

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


test('only completed indexing can mark a document ready for search', () => {
  assert.equal(extractionNotice({ status: 'ready', index_status: 'pending' }).kind, 'warning');
  assert.equal(extractionNotice({ status: 'ready', index_status: 'processing' }).kind, 'progress');
  assert.equal(extractionNotice({ status: 'ready', index_status: 'failed', index_error: 'Ollama off' }).message, 'Ollama off');
  assert.equal(extractionNotice({ status: 'ready', index_status: 'ready', chunk_count: 2 }).title, 'Tài liệu sẵn sàng tìm kiếm');
});
