"""Verify real BGE-M3 + pgvector in a disposable schema, without touching user documents."""
import json
import math
import time
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

import app.main
from app.config import Settings
from app.db import Base
from tests.test_documents import pdf_bytes


def main():
    config = Settings()
    schema = 'test_week5_smoke_' + uuid.uuid4().hex
    admin = create_engine(config.database_url)
    with admin.begin() as connection:
        if not connection.scalar(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')")):
            raise SystemExit('Chua co pgvector. Chay Docker image moi va alembic upgrade head truoc.')
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(config.database_url, connect_args={'options': f'-csearch_path={schema},public'})
    original = app.main.make_engine
    try:
        Base.metadata.create_all(engine)
        app.main.make_engine = lambda _: engine
        with TemporaryDirectory(prefix='private-ai-week5-') as folder:
            config.storage_dir = Path(folder)
            with TestClient(app.main.create_app(config)) as client:
                credentials = {'email':'week5-test@example.com', 'password':'temporary-test-password'}
                assert client.post('/auth/register', json=credentials).status_code == 201
                headers = {'Authorization':'Bearer '+client.post('/auth/login',json=credentials).json()['access_token']}
                workspace = client.post('/workspaces',headers=headers,json={'name':'Temporary week 5 test'}).json()
                base = '/workspaces/'+workspace['id']+'/documents'
                uploaded = client.post(base,headers=headers,files={'file':('week5-test.pdf',pdf_bytes(),'application/pdf')})
                assert uploaded.status_code == 201, uploaded.text
                path = base+'/'+uploaded.json()['id']
                assert client.post(path+'/process',headers=headers).json()['status'] == 'ready'
                started = time.monotonic()
                indexed = client.post(path+'/index',headers=headers)
                assert indexed.status_code == 200, indexed.text
                result = indexed.json()
                assert result['index_status'] == 'ready', result
                assert result['chunk_count'] == 2
                chunks = client.get(path+'/chunks',headers=headers).json()
                assert [c['page_number'] for c in chunks] == [1,2]
                with engine.connect() as connection:
                    rows = connection.execute(text('SELECT pg_typeof(embedding)::text, vector_dims(embedding), vector_norm(embedding) FROM document_chunks')).all()
                    assert len(rows) == 2
                    assert all(r[0]=='vector' and r[1]==1024 and math.isclose(r[2],1.0,abs_tol=1e-5) for r in rows)
                report = {'model':config.embedding_model,'chunks':2,'dimensions':1024,'database_type':'pgvector','seconds':round(time.monotonic()-started,3)}
                assert client.delete(path,headers=headers).status_code == 204
                with engine.connect() as connection:
                    assert connection.scalar(text('SELECT count(*) FROM document_chunks')) == 0
                    assert connection.scalar(text('SELECT count(*) FROM document_pages')) == 0
                assert not list(config.storage_dir.rglob('*.pdf'))
                print(json.dumps(report))
                print('PASS: real BGE-M3 + PostgreSQL pgvector; metadata and delete cascade verified.')
    finally:
        app.main.make_engine = original
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


if __name__ == '__main__':
    main()
