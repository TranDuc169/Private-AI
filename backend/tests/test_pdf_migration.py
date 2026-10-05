import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text

from app.db import Base


@pytest.mark.skipif(not os.environ.get('TEST_DATABASE_URL'), reason='Requires explicit PostgreSQL test URL')
def test_migration_preserves_old_data_and_matches_models(monkeypatch):
    url = os.environ['TEST_DATABASE_URL']
    schema = 'test_pdf_migration_' + uuid.uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={'options': f'-csearch_path={schema},public'})
    monkeypatch.setattr('app.db.make_engine', lambda _: engine)
    monkeypatch.setenv('JWT_SECRET', 'test-migration-only-secret-at-least-32-characters')
    monkeypatch.setenv('DATABASE_URL', url)
    config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    user_id, workspace_id, doc_id = [uuid.uuid4() for _ in range(3)]
    try:
        command.upgrade(config, '0001_initial')
        with engine.begin() as connection:
            connection.execute(text('INSERT INTO users (id,email,password_hash) VALUES (:id,:email,:hash)'), {'id': user_id, 'email': 'legacy@example.com', 'hash': 'test-only'})
            connection.execute(text('INSERT INTO workspaces (id,owner_id,name) VALUES (:id,:owner,:name)'), {'id': workspace_id, 'owner': user_id, 'name': 'Legacy'})
            connection.execute(text('INSERT INTO documents (id,workspace_id,filename) VALUES (:id,:workspace,:name)'), {'id': doc_id, 'workspace': workspace_id, 'name': 'old.pdf'})
        command.upgrade(config, '0002_pdf_documents')
        ready_id = uuid.uuid4()
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO documents (id,workspace_id,filename,status,size_bytes,page_count) VALUES (:id,:workspace,'week4.pdf','ready',123,1)"), {'id': ready_id, 'workspace': workspace_id})
            connection.execute(text("INSERT INTO document_pages (document_id,page_number,text) VALUES (:id,1,'Existing week 4 text')"), {'id': ready_id})
        command.upgrade(config, 'head')
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT count(*) FROM users')) == 1
            assert connection.scalar(text('SELECT count(*) FROM workspaces')) == 1
            row = connection.execute(text('SELECT id,filename,status,error_message FROM documents WHERE id=:id'), {'id':doc_id}).one()
            assert row.id == doc_id and row.filename == 'old.pdf' and row.status == 'failed'
            assert 'chưa có file' in row.error_message
            ready = connection.execute(text('SELECT status,index_status,chunk_count FROM documents WHERE id=:id'), {'id':ready_id}).one()
            assert tuple(ready) == ('ready','pending',0)
            assert connection.scalar(text('SELECT text FROM document_pages WHERE document_id=:id'), {'id':ready_id}) == 'Existing week 4 text'
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '0003_document_vectors'
            assert compare_metadata(MigrationContext.configure(connection, opts={'compare_type': True}), Base.metadata) == []
        command.upgrade(config, 'head')  # Safe repeated upgrade.
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()
