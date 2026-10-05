from io import BytesIO
import subprocess
import os
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models import Document

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from tests.test_auth_workspaces import client, account  # shared isolated DB fixture


def pdf_bytes(texts=("First page RAG", "Second page text"), encrypted=False):
    writer = PdfWriter()
    for value in texts:
        page = writer.add_blank_page(width=300, height=300)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(f'BT /F1 12 Tf 30 200 Td ({value}) Tj ET'.encode('ascii'))
        page[NameObject('/Contents')] = writer._add_object(stream)
    if encrypted:
        writer.encrypt('private-password')
    output = BytesIO(); writer.write(output)
    return output.getvalue()


def setup(client):
    headers = account(client)
    workspace = client.post('/workspaces', headers=headers, json={'name': 'PDF'}).json()
    return headers, '/workspaces/' + workspace['id'] + '/documents'


def upload(client, headers, base, data=None, name='sample.pdf'):
    return client.post(base, headers=headers, files={'file': (name, data if data is not None else pdf_bytes(), 'application/pdf')})


def test_upload_process_page_numbers_and_idempotent_retry(client):
    headers, base = setup(client)
    result = upload(client, headers, base)
    assert result.status_code == 201
    item = result.json()
    assert item['status'] == 'uploaded' and item['size_bytes'] > 0
    assert 'storage_dir' not in item
    path = base + '/' + item['id']
    assert client.get(path + '/pages', headers=headers).status_code == 409
    processed = client.post(path + '/process', headers=headers)
    assert processed.status_code == 200 and processed.json()['status'] == 'ready'
    assert processed.json()['page_count'] == 2
    pages = client.get(path + '/pages', headers=headers).json()
    assert [p['page_number'] for p in pages] == [1, 2]
    assert pages[0]['text'] == 'First page RAG'
    assert client.get(path + '/pages?offset=1&limit=1', headers=headers).json() == pages[1:]
    assert client.get(path + '/pages?offset=-1', headers=headers).status_code == 422
    assert client.post(path + '/process', headers=headers).json()['status'] == 'ready'
    assert len(client.get(path + '/pages', headers=headers).json()) == 2


def test_foreign_workspace_and_document_access_is_denied(client):
    alice, base = setup(client)
    item = upload(client, alice, base).json()
    bob = account(client, 'bob@example.com')
    own = client.post('/workspaces', headers=bob, json={'name': 'Bob'}).json()
    own_base = '/workspaces/' + own['id'] + '/documents'
    assert upload(client, bob, base).status_code == 404
    for root in (base, own_base):
        path = root + '/' + item['id']
        assert client.get(path, headers=bob).status_code == 404
        assert client.get(path + '/pages', headers=bob).status_code == 404
        assert client.post(path + '/process', headers=bob).status_code == 404
    assert client.get(own_base, headers=bob).json() == []
    assert client.post(base, files={'file': ('x.pdf', pdf_bytes())}).status_code == 401


def test_validation_and_size_limits_clean_up_partial_files(client):
    headers, base = setup(client)
    for name, data, status in [('x.txt', b'hello', 415), ('fake.pdf', b'not PDF', 415), ('empty.pdf', b'', 422), ('large.pdf', b'%PDF-' + b'x' * (1024 * 1024), 413)]:
        assert upload(client, headers, base, data, name).status_code == status
    assert upload(client, headers, base, b'%PDF-' + b'x' * (1200 * 1024)).status_code == 413
    assert client.get(base, headers=headers).json() == []
    assert list(client.app.state.settings.storage_dir.rglob('*.pdf')) == []


def test_filename_is_display_only_and_duplicates_never_overwrite(client):
    headers, base = setup(client)
    first = upload(client, headers, base, name='../../outside.pdf').json()
    second = upload(client, headers, base, name='outside.pdf').json()
    assert first['filename'] == 'outside.pdf'
    assert first['id'] != second['id']
    files = list(client.app.state.settings.storage_dir.rglob('*.pdf'))
    assert len(files) == 2
    assert {p.stem for p in files} == {first['id'], second['id']}


def test_corrupt_encrypted_scan_and_page_limit_show_failed_status(client):
    headers, base = setup(client)
    for data, expected in [(b'%PDF-1.7\nbroken', 'Không đọc được'), (pdf_bytes(encrypted=True), 'mật khẩu'), (pdf_bytes(('',)), 'OCR'), (pdf_bytes(('a','b','c','d')), 'trang')]:
        item = upload(client, headers, base, data).json()
        path = base + '/' + item['id']
        result = client.post(path + '/process', headers=headers).json()
        assert result['status'] == 'failed'
        assert expected in result['error_message']
        assert client.get(path + '/pages', headers=headers).status_code == 409


def test_timeout_and_missing_file_are_retryable_failures(client, monkeypatch):
    headers, base = setup(client)
    item = upload(client, headers, base).json()
    path = base + '/' + item['id']
    original = subprocess.run
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired('pdf', 1)
    monkeypatch.setattr('app.documents.subprocess.run', timeout)
    result = client.post(path + '/process', headers=headers).json()
    assert result['status'] == 'failed' and 'thời gian' in result['error_message']
    monkeypatch.setattr('app.documents.subprocess.run', original)
    assert client.post(path + '/process', headers=headers).json()['status'] == 'ready'
    missing = upload(client, headers, base).json()
    file = next(client.app.state.settings.storage_dir.rglob(missing['id'] + '.pdf'))
    file.unlink()
    result = client.post(base + '/' + missing['id'] + '/process', headers=headers).json()
    assert result['status'] == 'failed' and 'file gốc' in result['error_message']


def test_multipart_stream_without_content_length_is_bounded(client):
    headers, base = setup(client)
    headers['Content-Type'] = 'multipart/form-data; boundary=sample-boundary'
    def chunks():
        yield b'--sample-boundary\r\nContent-Disposition: form-data; name="file"; filename="large.pdf"\r\nContent-Type: application/pdf\r\n\r\n%PDF-'
        for _ in range(20):
            yield b'x' * 65536
        yield b'\r\n--sample-boundary--\r\n'
    result = client.post(base, headers=headers, content=chunks())
    assert result.status_code == 413
    assert client.get(base, headers=headers).json() == []


def test_pdf_character_limit(client):
    headers, base = setup(client)
    client.app.state.settings.max_pdf_characters = 5
    item = upload(client, headers, base).json()
    result = client.post(base + '/' + item['id'] + '/process', headers=headers).json()
    assert result['status'] == 'failed' and 'giới hạn' in result['error_message']


def test_database_upload_failure_does_not_leave_file_or_expose_error(client, monkeypatch):
    headers, base = setup(client)
    def fail_commit(self):
        raise SQLAlchemyError('PRIVATE_DATABASE_DETAIL')
    monkeypatch.setattr(Session, 'commit', fail_commit)
    result = upload(client, headers, base)
    assert result.status_code == 503
    assert 'PRIVATE_DATABASE_DETAIL' not in result.text
    assert list(client.app.state.settings.storage_dir.rglob('*.pdf')) == []
    assert client.get(base, headers=headers).json() == []


@pytest.mark.skipif(not os.environ.get('TEST_DATABASE_URL'), reason='Row locks require PostgreSQL')
def test_concurrent_process_returns_conflict_without_overwriting(client):
    headers, base = setup(client)
    item = upload(client, headers, base).json()
    path = base + '/' + item['id']
    with client.app.state.session_factory() as locking_session:
        locking_session.scalar(select(Document).where(Document.id == uuid.UUID(item['id'])).with_for_update())
        assert client.post(path + '/process', headers=headers).status_code == 409
        locking_session.rollback()
    assert client.post(path + '/process', headers=headers).json()['status'] == 'ready'
