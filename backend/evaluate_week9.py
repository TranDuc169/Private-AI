"""Small live PostgreSQL/Ollama smoke test in an isolated disposable schema."""
import argparse
import json
import time
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool
import app.main
import app.planning
from app.generation import GenerationError
from app.config import Settings
from app.db import Base
from evaluate_retrieval import public_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['postgres','sqlite'], default='postgres')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise SystemExit('Use a new output filename; evidence is not overwritten.')
    config = Settings()
    admin = create_engine(config.database_url, connect_args={'connect_timeout':5}) if args.mode == 'postgres' else None
    before = public_snapshot(admin) if admin is not None else None
    schema = 'test_week9_live_' + uuid.uuid4().hex
    original = app.main.make_engine
    engine = None
    report = dict(mode=args.mode+' + real BGE-M3/Qwen, isolated TestClient API',
                  model=config.chat_model, embedding_model=config.embedding_model, cases=[],
                  human_review='pending', public_data_unchanged=None)
    real_generate = app.planning.generate_plan
    def checked_generate(*values):
        try: return real_generate(*values)
        except GenerationError as error:
            report.setdefault('model_errors', []).append(error.diagnostics)
            raise
    app.planning.generate_plan = checked_generate
    try:
        if admin is not None:
            with admin.begin() as c: c.execute(text(f'CREATE SCHEMA "{schema}"'))
            engine = create_engine(config.database_url, connect_args={'options': f'-csearch_path={schema},public'})
        else:
            engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
        Base.metadata.create_all(engine, checkfirst=False)
        assert set(Base.metadata.tables) <= set(inspect(engine).get_table_names(schema=schema if admin is not None else None))
        app.main.make_engine = lambda _: engine
        with TemporaryDirectory(prefix='week9-') as folder:
            config.storage_dir = Path(folder)/'storage'
            with TestClient(app.main.create_app(config)) as client:
                credentials = dict(email='week9-test@example.com', password=uuid.uuid4().hex)
                assert client.post('/auth/register', json=credentials).status_code == 201
                headers = {'Authorization': 'Bearer '+client.post('/auth/login', json=credentials).json()['access_token']}
                wid = client.post('/workspaces', headers=headers, json={'name': 'Week9 live test'}).json()['id']
                base = f'/workspaces/{wid}'
                for pdf in sorted((Path(__file__).resolve().parents[1]/'docs/course/pdfs').glob('*.pdf')):
                    uploaded = client.post(base+'/documents', headers=headers, files={'file': (pdf.name, pdf.read_bytes(), 'application/pdf')})
                    assert uploaded.status_code == 201, uploaded.text
                    doc = base+'/documents/'+uploaded.json()['id']
                    assert client.post(doc+'/process', headers=headers).json()['status'] == 'ready'
                    assert client.post(doc+'/index', headers=headers).json()['index_status'] == 'ready'
                cid, revision = None, 0
                for question in ('Lập roadmap SQL JOIN; mới bắt đầu; 4 buổi; 45 phút/buổi', 'Lập roadmap ERD chuẩn hóa; đã biết cơ bản; 3 buổi; 40 phút/buổi', 'Lập roadmap index; đã biết cơ bản; 4 buổi; 45 phút/buổi'):
                    started = time.perf_counter()
                    response = client.post(base+'/chat', headers=headers, json=dict(question=question, conversation_id=cid, revision=revision))
                    record = dict(question=question, http_status=response.status_code, response=response.json(), seconds=round(time.perf_counter()-started, 3))
                    report['cases'].append(record)
                    print(response.status_code, record['seconds'], flush=True)
                    assert response.status_code == 200, response.text
                    cid, revision = response.json()['conversation_id'], response.json()['revision']
                    saved = client.get(base+'/conversations/'+cid, headers=headers)
                    assert saved.json()['messages'][-1]['result'] == response.json()
                    pid = response.json()['roadmap_id']
                    assert pid, response.text
                    plan_path = base+'/plans/'+pid
                    plan = client.get(plan_path, headers=headers).json()
                    record['plan'] = plan
                    assert plan['spec']['planned_minutes'] <= plan['spec']['budget_minutes']
                    assert client.post(plan_path+'/confirm', headers=headers, json={'revision':0}).status_code == 200
                    key = plan['spec']['steps'][0]['key']
                    assert client.patch(plan_path+'/steps/'+key, headers=headers, json={'revision':1,'done':True}).status_code == 200
                    assert client.get(plan_path, headers=headers).json()['progress'][key] is True
                    record['confirmed_and_progress_reloaded'] = True
                    for source in response.json()['sources']:
                        current = client.get(base+'/sources/'+source['chunk_id'], headers=headers)
                        assert current.status_code == 200 and current.json()['text'] == source['text']
                report['saved_messages'] = len(saved.json()['messages'])
                assert report['saved_messages'] == 6
                report['source_and_history_roundtrip'] = 'passed'
                small = client.post(base+'/chat', headers=headers, json={'question':'Roadmap SQL; mới bắt đầu; 1 buổi; 15 phút/buổi'})
                assert small.status_code == 200 and small.json()['roadmap_id'] is None
                report['infeasible_budget'] = small.json()

    finally:
        app.main.make_engine = original
        app.planning.generate_plan = real_generate
        if engine: engine.dispose()
        if admin is not None:
            with admin.begin() as c: c.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
            report['public_data_unchanged'] = public_snapshot(admin) == before
            admin.dispose()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    assert report['public_data_unchanged'] is not False, 'Public data changed; inspect concurrent activity.'


if __name__ == '__main__': main()
