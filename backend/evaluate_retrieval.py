"""Live week-6 retrieval evaluation; synthetic data in a verified disposable schema."""
import hashlib
import json
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

import app.main
from app.config import Settings
from app.db import Base
from app.models import Document, DocumentPage


def public_snapshot(engine):
    with engine.connect() as connection:
        return {table: hashlib.sha256('\n'.join(sorted(connection.execute(text(
            f'SELECT row_to_json(t)::text FROM public.{table} t')).scalars())).encode()).hexdigest()
            for table in ('users','workspaces','documents','document_pages','document_chunks','conversations','messages','alembic_version')}


def main():
    config=Settings()
    dataset=json.loads((Path(__file__).resolve().parents[1]/'docs/evaluation/week6.json').read_text(encoding='utf-8'))
    schema='test_week6_eval_'+uuid.uuid4().hex
    admin=create_engine(config.database_url)
    before=public_snapshot(admin)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine=create_engine(config.database_url,connect_args={'options':f'-csearch_path={schema},public'})
    original=app.main.make_engine
    report={}
    try:
        Base.metadata.create_all(engine,checkfirst=False)
        assert set(Base.metadata.tables)<=set(inspect(engine).get_table_names(schema=schema))
        app.main.make_engine=lambda _:engine
        with TemporaryDirectory(prefix='private-ai-week6-') as folder:
            config.storage_dir=Path(folder)
            with TestClient(app.main.create_app(config)) as client:
                def account(email):
                    data={'email':email,'password':'week6-evaluation-only-password'}
                    assert client.post('/auth/register',json=data).status_code==201
                    return {'Authorization':'Bearer '+client.post('/auth/login',json=data).json()['access_token']}
                owner=account('week6-owner@example.com')
                def workspace(headers,name):
                    return client.post('/workspaces',headers=headers,json={'name':name}).json()['id']
                target=workspace(owner,'Đánh giá retrieval')
                other=workspace(owner,'Workspace khác')
                empty=workspace(owner,'Chưa có tài liệu')
                def seed(wid,filename,pages):
                    with client.app.state.session_factory() as session:
                        document=Document(workspace_id=uuid.UUID(wid),filename=filename,status='ready',page_count=len(pages))
                        session.add(document);session.flush()
                        session.add_all(DocumentPage(document_id=document.id,page_number=i+1,text=value) for i,value in enumerate(pages))
                        session.commit();docid=str(document.id)
                    result=client.post(f'/workspaces/{wid}/documents/{docid}/index',headers=owner)
                    assert result.status_code==200 and result.json()['index_status']=='ready',result.text
                    return docid
                allowed={seed(target,d['filename'],d['pages']) for d in dataset['documents']}
                seed(other,'foreign-exact-query.pdf',[dataset['cases'][0]['question']])
                cases=[]
                for case in dataset['cases']:
                    response=client.post(f'/workspaces/{target}/retrieve',headers=owner,json={'question':case['question'],'top_k':3})
                    assert response.status_code==200,response.text
                    result=response.json()
                    assert all(hit['document_id'] in allowed for hit in result['results'])
                    rank=next((i+1 for i,h in enumerate(result['results']) if h['filename']==case['expected_filename'] and h['page_number']==case['expected_page']),None)
                    cases.append({'id':case['id'],'question':case['question'],'expected_filename':case['expected_filename'],
                        'expected_page':case['expected_page'],'rank':rank,'elapsed_ms':result['elapsed_ms'],
                        'hits':[{'filename':h['filename'],'page_number':h['page_number'],'score':h['score']} for h in result['results']]})
                bob=account('week6-other@example.com')
                assert client.post(f'/workspaces/{target}/retrieve',headers=bob,json={'question':'test'}).status_code==404
                assert client.post(f'/workspaces/{empty}/retrieve',headers=owner,json={'question':'test'}).json()['results']==[]
                answerable=[c for c in cases if c['expected_filename'] is not None]
                report={'model':config.embedding_model,'database':'PostgreSQL/pgvector','top_k':3,'answerable_questions':len(answerable),
                    'hit_at_1':sum(c['rank']==1 for c in answerable)/len(answerable),
                    'hit_at_3':sum(c['rank'] is not None for c in answerable)/len(answerable),
                    'mrr_at_3':sum(1/c['rank'] if c['rank'] else 0 for c in answerable)/len(answerable),
                    'workspace_isolation':'PASS','foreign_owner':'404','empty_workspace':'empty results','cases':cases,
                    'limitations':'Small synthetic set; no LLM, no relevance threshold. Out-of-scope questions can still return nearest chunks.'}
    finally:
        app.main.make_engine=original
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        unchanged=public_snapshot(admin)==before
        admin.dispose()
        assert unchanged,'Application data changed during evaluation; inspect before proceeding.'
    report['public_data_unchanged']=True
    print(json.dumps(report,ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()
