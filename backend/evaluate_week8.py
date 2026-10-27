"""Small live PostgreSQL/Ollama smoke test in an isolated disposable schema."""
import argparse
import json
import time
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
import app.main
from app.config import Settings
from app.db import Base
from evaluate_retrieval import public_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise SystemExit('Use a new output filename; evidence is not overwritten.')
    config = Settings()
    admin = create_engine(config.database_url)
    before = public_snapshot(admin)
    schema = 'test_week8_live_' + uuid.uuid4().hex
    original = app.main.make_engine
    engine = None
    report = dict(mode='real PostgreSQL + Ollama, isolated TestClient API',
                  model=config.chat_model, embedding_model=config.embedding_model, cases=[],
                  human_review='pending', public_data_unchanged=None)
    try:
        with admin.begin() as c: c.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(config.database_url, connect_args={'options': f'-csearch_path={schema},public'})
        Base.metadata.create_all(engine, checkfirst=False)
        assert set(Base.metadata.tables) <= set(inspect(engine).get_table_names(schema=schema))
        app.main.make_engine = lambda _: engine
        with TemporaryDirectory(prefix='week8-') as folder:
            config.storage_dir = Path(folder)/'storage'
            with TestClient(app.main.create_app(config)) as client:
                credentials = dict(email='week8-test@example.com', password=uuid.uuid4().hex)
                assert client.post('/auth/register', json=credentials).status_code == 201
                headers = {'Authorization': 'Bearer '+client.post('/auth/login', json=credentials).json()['access_token']}
                wid = client.post('/workspaces', headers=headers, json={'name': 'Week8 live test'}).json()['id']
                base = f'/workspaces/{wid}'
                pdf = Path(__file__).resolve().parents[1]/'docs/course/pdfs/04-transaction.pdf'
                uploaded = client.post(base+'/documents', headers=headers, files={'file': (pdf.name, pdf.read_bytes(), 'application/pdf')})
                assert uploaded.status_code == 201, uploaded.text
                doc = base+'/documents/'+uploaded.json()['id']
                assert client.post(doc+'/process', headers=headers).json()['status'] == 'ready'
                assert client.post(doc+'/index', headers=headers).json()['index_status'] == 'ready'
                cid, revision = None, 0
                for question in ('COMMIT và ROLLBACK khác nhau thế nào?', 'Tóm tắt chủ đề transaction', 'Lịch thi môn CSDL của trường tôi ngày nào?'):
                    started = time.perf_counter()
                    response = client.post(base+'/chat', headers=headers, json=dict(question=question, conversation_id=cid, revision=revision))
                    record = dict(question=question, http_status=response.status_code, response=response.json(), seconds=round(time.perf_counter()-started, 3))
                    report['cases'].append(record)
                    print(response.status_code, record['seconds'], flush=True)
                    assert response.status_code == 200, response.text
                    cid, revision = response.json()['conversation_id'], response.json()['revision']
                    saved = client.get(base+'/conversations/'+cid, headers=headers)
                    assert saved.json()['messages'][-1]['result'] == response.json()
                    for source in response.json()['sources']:
                        current = client.get(base+'/sources/'+source['chunk_id'], headers=headers)
                        assert current.status_code == 200 and current.json()['text'] == source['text']
                report['saved_messages'] = len(saved.json()['messages'])
                assert report['saved_messages'] == 6
                report['source_and_history_roundtrip'] = 'passed'
    finally:
        app.main.make_engine = original
        if engine: engine.dispose()
        with admin.begin() as c: c.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        report['public_data_unchanged'] = public_snapshot(admin) == before
        admin.dispose()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    assert report['public_data_unchanged'], 'Public data changed; inspect concurrent activity.'


if __name__ == '__main__': main()
