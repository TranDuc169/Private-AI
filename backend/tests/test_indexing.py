import os
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.embedding import CHUNK_SIZE, CHUNK_OVERLAP, EmbeddingError, chunk_pages, embed_batch
from app.models import Document, DocumentChunk, DocumentPage
from tests.test_documents import client, setup, upload, account


def extracted(client):
    headers, base = setup(client)
    item = upload(client, headers, base).json()
    path = base + '/' + item['id']
    assert client.post(path + '/process', headers=headers).json()['status'] == 'ready'
    return headers, base, path, item


def fake_embed(config, texts, timeout=None):
    return [[1.0] + [0.0] * 1023 for _ in texts]


def test_chunks_cover_source_with_overlap_offsets_and_page_metadata():
    original = 'Tiếng Việt 😀 ' * 250
    pages = [SimpleNamespace(page_number=2, text=original), SimpleNamespace(page_number=3, text=' '), SimpleNamespace(page_number=4, text='Kết thúc')]
    chunks = chunk_pages(pages)
    first_page = [c for c in chunks if c['page_number'] == 2]
    assert first_page[0]['start_char'] == 0 and first_page[-1]['end_char'] == len(original)
    for i, chunk in enumerate(first_page):
        assert chunk['text'] == original[chunk['start_char']:chunk['end_char']]
        assert len(chunk['text']) <= CHUNK_SIZE
        if i: assert first_page[i-1]['end_char'] - chunk['start_char'] == CHUNK_OVERLAP
    assert chunks[-1]['page_number'] == 4
    with pytest.raises(EmbeddingError): chunk_pages(pages, maximum=1)
    with pytest.raises(EmbeddingError): chunk_pages([SimpleNamespace(page_number=1, text='  ')])


def test_real_http_contract_and_reject_invalid_embeddings(monkeypatch):
    original_client = httpx.Client
    payloads = []
    config = SimpleNamespace(ollama_base_url='http://localhost:11434', embedding_model='bge-m3:latest', embedding_timeout_seconds=1)
    payload = {'embeddings': [[2.0] + [0.0] * 1023]}
    def handler(request):
        import json
        payloads.append(json.loads(request.content))
        return httpx.Response(200, json=payload)
    monkeypatch.setattr('app.embedding.httpx.Client', lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    assert embed_batch(config, ['xin chào'])[0][0] == 1.0
    assert payloads[0] == {'model':'bge-m3:latest', 'input':['xin chào'], 'truncate':False}
    for bad in ([], [[1.0]*3], [[0.0]*1024], [[True]*1024], [['bad']*1024]):
        payload = {'embeddings': bad}
        with pytest.raises(EmbeddingError): embed_batch(config, ['xin chào'])
    def offline(request): raise httpx.ConnectError('PRIVATE_DETAIL')
    monkeypatch.setattr('app.embedding.httpx.Client', lambda **kwargs: original_client(transport=httpx.MockTransport(offline), **kwargs))
    with pytest.raises(EmbeddingError, match='Ollama') as caught: embed_batch(config, ['hello'])
    assert 'PRIVATE_DETAIL' not in str(caught.value)


def test_index_atomic_metadata_idempotent_and_cascade_delete(client, monkeypatch):
    headers, base, path, item = extracted(client)
    calls = []
    def embed(config, texts, timeout=None):
        observed = client.get(path, headers=headers).json()
        assert observed['index_status'] == 'processing' and observed['chunk_count'] == 0
        assert client.post(path + '/index', headers=headers).status_code == 409
        assert client.delete(path, headers=headers).status_code == 409
        calls.append(texts)
        return fake_embed(config, texts)
    monkeypatch.setattr('app.indexing.embed_batch', embed)
    assert client.get(path + '/chunks', headers=headers).status_code == 409
    response = client.post(path + '/index', headers=headers)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['index_status'] == 'ready' and result['chunk_count'] == 2
    assert result['embedding_model'] == 'bge-m3:latest' and result['indexed_at']
    chunks = client.get(path + '/chunks', headers=headers).json()
    assert [c['page_number'] for c in chunks] == [1,2]
    assert chunks[0]['text'] == 'First page RAG' and chunks[0]['embedding_dimensions'] == 1024
    assert 'embedding' not in chunks[0]
    assert client.get(path+'/chunks?offset=1&limit=1', headers=headers).json() == chunks[1:]
    assert client.post(path + '/index', headers=headers).json()['chunk_count'] == 2
    assert len(calls) == 1
    with client.app.state.session_factory() as session:
        vector = session.scalar(select(DocumentChunk.embedding))
        assert len(vector) == 1024 and vector[0] == 1.0
    assert client.delete(path, headers=headers).status_code == 204
    assert client.get(path, headers=headers).status_code == 404
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(DocumentChunk)) == 0
        assert session.scalar(select(func.count()).select_from(DocumentPage)) == 0
    assert not list(client.app.state.settings.storage_dir.rglob('*.*'))


def test_failure_after_batch_is_not_partial_and_retry_does_not_duplicate(client, monkeypatch):
    headers, base, path, item = extracted(client)
    client.app.state.settings.embedding_batch_size = 1
    calls = 0
    def fail(config, texts, timeout=None):
        nonlocal calls
        calls += 1
        if calls == 2: raise EmbeddingError('Ollama tắt giữa chừng')
        return fake_embed(config,texts)
    monkeypatch.setattr('app.indexing.embed_batch', fail)
    result = client.post(path + '/index', headers=headers).json()
    assert result['index_status'] == 'failed' and result['chunk_count'] == 0
    assert result['status'] == 'ready'  # Extracted text survives indexing errors.
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(DocumentChunk)) == 0
    assert len(client.get(path+'/pages',headers=headers).json()) == 2
    monkeypatch.setattr('app.indexing.embed_batch', fake_embed)
    assert client.post(path+'/index',headers=headers).json()['chunk_count'] == 2


def test_index_chunks_delete_are_owner_scoped(client, monkeypatch):
    headers, base, path, item = extracted(client)
    bob = account(client, 'bob@example.com')
    other = client.post('/workspaces',headers=bob,json={'name':'Bob'}).json()
    for root in (base, '/workspaces/'+other['id']+'/documents'):
        target = root+'/'+item['id']
        assert client.post(target+'/index',headers=bob).status_code == 404
        assert client.get(target+'/chunks',headers=bob).status_code == 404
        assert client.delete(target,headers=bob).status_code == 404
    assert client.delete(path).status_code == 401
    assert client.get(path,headers=headers).status_code == 200


def test_expired_claim_can_retry_and_stale_worker_cannot_publish(client, monkeypatch):
    headers, base, path, item = extracted(client)
    with client.app.state.session_factory() as session:
        row = session.get(Document, uuid.UUID(item['id']))
        row.index_status = 'processing'; row.index_job_id = uuid.uuid4()
        row.index_started_at = datetime.now(timezone.utc) - timedelta(minutes=16)
        session.commit()
    monkeypatch.setattr('app.indexing.embed_batch',fake_embed)
    assert client.post(path+'/index',headers=headers).json()['index_status'] == 'ready'
    with client.app.state.session_factory() as session:
        row = session.get(Document,uuid.UUID(item['id'])); row.index_status='failed'; session.commit()
    def replace_job(config,texts,timeout=None):
        with client.app.state.session_factory() as session:
            row=session.get(Document,uuid.UUID(item['id'])); row.index_job_id=uuid.uuid4(); session.commit()
        return fake_embed(config,texts)
    monkeypatch.setattr('app.indexing.embed_batch',replace_job)
    assert client.post(path+'/index',headers=headers).status_code == 409


def test_failed_delete_restores_pdf_and_preserves_rows(client,monkeypatch):
    headers, base, path, item = extracted(client)
    original = Session.commit
    def fail(self): raise SQLAlchemyError('PRIVATE_DETAILS')
    monkeypatch.setattr(Session,'commit',fail)
    result=client.delete(path,headers=headers)
    assert result.status_code == 503 and 'PRIVATE_DETAILS' not in result.text
    monkeypatch.setattr(Session,'commit',original)
    assert client.get(path,headers=headers).status_code == 200
    assert len(list(client.app.state.settings.storage_dir.rglob('*.pdf'))) == 1
    assert not list(client.app.state.settings.storage_dir.rglob('*.deleting'))


def test_database_failure_never_publishes_partial_vectors(client, monkeypatch):
    headers, base, path, item = extracted(client)
    monkeypatch.setattr('app.indexing.embed_batch', fake_embed)
    original = Session.commit
    calls = 0
    def fail_publication(self):
        nonlocal calls
        calls += 1
        if calls == 2: raise SQLAlchemyError('PRIVATE_DB')
        return original(self)
    monkeypatch.setattr(Session, 'commit', fail_publication)
    result = client.post(path+'/index', headers=headers)
    assert result.status_code == 503 and 'PRIVATE_DB' not in result.text
    assert client.get(path, headers=headers).json()['index_status'] == 'failed'
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(DocumentChunk)) == 0
    assert client.post(path+'/index', headers=headers).json()['index_status'] == 'ready'


def test_cannot_index_unparsed_document(client):
    headers, base = setup(client)
    item = upload(client, headers, base).json()
    assert client.post(base+'/'+item['id']+'/index', headers=headers).status_code == 409


@pytest.mark.skipif(not os.environ.get('TEST_DATABASE_URL'), reason='Requires PostgreSQL vector extension')
def test_postgres_vector_type_dimension_and_cosine(client, monkeypatch):
    headers, base, path, item = extracted(client)
    monkeypatch.setattr('app.indexing.embed_batch', fake_embed)
    assert client.post(path+'/index', headers=headers).json()['index_status'] == 'ready'
    with client.app.state.engine.connect() as connection:
        row = connection.execute(text('SELECT pg_typeof(embedding)::text, vector_dims(embedding), embedding <=> embedding FROM document_chunks LIMIT 1')).one()
        assert row[0] == 'vector' and row[1] == 1024 and abs(row[2]) < 1e-6
