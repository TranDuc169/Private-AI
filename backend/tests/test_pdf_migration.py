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
    engine = create_engine(url, connect_args={'options': f'-csearch_path={schema}'})
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
        command.upgrade(config, 'head')
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT count(*) FROM users')) == 1
            assert connection.scalar(text('SELECT count(*) FROM workspaces')) == 1
            row = connection.execute(text('SELECT id,filename,status,error_message FROM documents')).one()
            assert row.id == doc_id and row.filename == 'old.pdf' and row.status == 'failed'
            assert 'chưa có file' in row.error_message
            assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '0002_pdf_documents'
            assert compare_metadata(MigrationContext.configure(connection, opts={'compare_type': True}), Base.metadata) == []
        command.upgrade(config, 'head')  # Safe repeated upgrade.
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()
