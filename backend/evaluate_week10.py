"""Week 10: real PDFs/embeddings and Qwen, isolated database; never user rows."""
import argparse
import json
import time
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text, select
from sqlalchemy.pool import StaticPool
import app.main
from app.config import Settings
from app.db import Base
from app.models import Quiz
from app.planning import CURRICULUM
from evaluate_retrieval import public_snapshot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['postgres','sqlite'],default='postgres')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise SystemExit('Choose a new evidence filename; cannot overwrite.')
    config=Settings(); schema='test_week10_'+uuid.uuid4().hex
    admin=create_engine(config.database_url,connect_args={'connect_timeout':5}) if args.mode=='postgres' else None
    before=public_snapshot(admin) if admin is not None else None
    original=app.main.make_engine; engine=None
    report=dict(mode=args.mode,real_embeddings=True,real_qwen=True,cases=[],drafts=[],public_data_unchanged=None)
    try:
        if admin is not None:
            with admin.begin() as c:c.execute(text(f'CREATE SCHEMA "{schema}"'))
            engine=create_engine(config.database_url,connect_args={'options':f'-csearch_path={schema},public','connect_timeout':5})
        else:engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
        Base.metadata.create_all(engine,checkfirst=False)
        assert set(Base.metadata.tables)<=set(inspect(engine).get_table_names(schema=schema if admin is not None else None))
        app.main.make_engine=lambda _:engine
        with TemporaryDirectory(prefix='week10-') as folder:
            config.storage_dir=Path(folder)/'storage'
            with TestClient(app.main.create_app(config)) as client:
                credentials=dict(email='week10-demo@example.com',password=uuid.uuid4().hex)
                assert client.post('/auth/register',json=credentials).status_code==201
                h={'Authorization':'Bearer '+client.post('/auth/login',json=credentials).json()['access_token']}
                wid=client.post('/workspaces',headers=h,json={'name':'Week10 isolated'}).json()['id']; base=f'/workspaces/{wid}'
                for pdf in sorted((Path(__file__).resolve().parents[1]/'docs/course/pdfs').glob('*.pdf')):
                    res=client.post(base+'/documents',headers=h,files={'file':(pdf.name,pdf.read_bytes(),'application/pdf')})
                    assert res.status_code==201,res.text
                    doc=base+'/documents/'+res.json()['id']
                    assert client.post(doc+'/process',headers=h).json()['status']=='ready'
                    assert client.post(doc+'/index',headers=h).json()['index_status']=='ready'
                for key,(title,_) in CURRICULUM.items():
                    started=time.perf_counter()
                    created=client.post(base+'/chat',headers=h,json={'question':'Quiz '+title})
                    record=dict(topic=key,chat=created.json());report['cases'].append(record)
                    assert created.status_code==200 and created.json()['quiz_id'],created.text
                    path=base+'/quizzes/'+created.json()['quiz_id']
                    public=client.get(path,headers=h).json(); record['before_submit']=public
                    assert public['result'] is None and all(set(q)=={'question','choices'} for q in public['questions'])
                    # Deliberately choose A for all questions. Server must grade independently.
                    submitted=client.post(path+'/submit',headers=h,json={'answers':[0]*len(public['questions'])})
                    assert submitted.status_code==200,submitted.text
                    record['after_submit']=submitted.json()
                    assert client.get(path,headers=h).json()==submitted.json()
                    for source in submitted.json()['result']['sources']:
                        assert client.get(base+'/sources/'+source['chunk_id'],headers=h).status_code==200
                    record['seconds']=round(time.perf_counter()-started,3)
                    print(key,'bank, score',submitted.json()['result']['score'],flush=True)
                # One model-generated example is deliberately never approved/graded.
                started=time.perf_counter()
                response=client.post(base+'/chat',headers=h,json={'question':'Sinh mới quiz SQL JOIN'})
                record=dict(http_status=response.status_code,response=response.json(),seconds=round(time.perf_counter()-started,3));report['drafts'].append(record)
                if response.status_code==200 and response.json().get('quiz_id'):
                    qid=uuid.UUID(response.json()['quiz_id'])
                    with client.app.state.session_factory() as session:
                        record['review_only_private_spec']=session.get(Quiz,qid).spec
                    assert client.post(base+'/quizzes/'+str(qid)+'/submit',headers=h,json={'answers':[0,0,0]}).status_code==409
                    record['grading_blocked']=True
                else: record['rejected_by_schema_or_source_check']=True
                print('draft',response.status_code,flush=True)
                report['bank_roundtrip_passed']=True
    finally:
        app.main.make_engine=original
        if engine:engine.dispose()
        if admin is not None:
            with admin.begin() as c:c.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
            report['public_data_unchanged']=public_snapshot(admin)==before
            admin.dispose()
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert report['public_data_unchanged'] is not False


if __name__=='__main__':main()
