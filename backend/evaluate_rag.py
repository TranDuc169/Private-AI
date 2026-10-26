"""Evaluate real local models; --mode postgres also verifies upload/index/chat end to end.

Default model mode is explicit: PDF extraction and cosine ranking in memory, NO
PostgreSQL or production API verification. Outputs include full answers for review.
"""
import argparse
import hashlib
import json
import math
import platform
import time
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from pypdf import PdfReader
from sqlalchemy import create_engine, inspect, text
from fastapi.testclient import TestClient

import app.main
from app.config import Settings
from app.db import Base
from app.embedding import chunk_pages, embed_batch
from app.generation import generate_answer, GenerationError, SYSTEM_PROMPT
from app.schemas import RetrievalHit
from evaluate_retrieval import public_snapshot
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['models','postgres'],default='models')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--limit',type=int,default=20)
    parser.add_argument('--start',type=int,default=0,help='Zero-based offset for a follow-up run; preserve earlier output.')
    parser.add_argument('--only',help='Comma-separated case IDs for a targeted follow-up, e.g. q05,q10')
    args=parser.parse_args()
    if not 0 <= args.start < 20 or not 1 <= args.limit <= 20:
        raise SystemExit('start must be 0..19 and limit must be 1..20')
    if args.output.exists(): raise SystemExit('Output already exists; use a new filename to preserve evidence.')
    config=Settings(); corpus=json.loads((ROOT/'docs/course/manifest.json').read_text(encoding='utf-8'))
    cases=json.loads((ROOT/'docs/evaluation/week7.json').read_text(encoding='utf-8'))['cases'][args.start:args.start+args.limit]
    if args.only:
        requested=set(args.only.split(','))
        if not requested <= {c['id'] for c in cases}: raise SystemExit('Unknown case ID in selected range')
        cases=[c for c in cases if c['id'] in requested]
    report={'mode':args.mode,'chat_model':config.chat_model,'embedding_model':config.embedding_model,
            'prompt_sha256':hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
            'configuration':{'num_ctx':8192,'num_predict':config.chat_num_predict,'temperature':0,'think':False},
            'platform':platform.platform(),'python':platform.python_version(),
            'corpus_version':corpus['version'],'human_review':'pending; source matches are not correctness scores',
            'cases':[],'public_data_unchanged':None}
    with httpx.Client(timeout=5,trust_env=False) as http:
        report['ollama_version']=http.get(config.ollama_base_url+'/api/version').json()
        report['model_inventory']=http.get(config.ollama_base_url+'/api/tags').json()
    chunks=[];admin=engine=None;schema=None;before=None;original=app.main.make_engine
    def save():
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    try:
        with TemporaryDirectory(prefix='week7-rag-') as folder:
            config.storage_dir=Path(folder)/'storage'
            if args.mode=='postgres':
                admin=create_engine(config.database_url);before=public_snapshot(admin)
                schema='test_week7_eval_'+uuid.uuid4().hex
                with admin.begin() as c:c.execute(text(f'CREATE SCHEMA "{schema}"'))
                engine=create_engine(config.database_url,connect_args={'options':f'-csearch_path={schema},public'})
                Base.metadata.create_all(engine,checkfirst=False)
                assert set(Base.metadata.tables)<=set(inspect(engine).get_table_names(schema=schema))
                app.main.make_engine=lambda _:engine
            with TestClient(app.main.create_app(config)) if args.mode=='postgres' else _NoClient() as client:
                if client:
                    credentials={'email':'week7-eval@example.com','password':uuid.uuid4().hex}
                    assert client.post('/auth/register',json=credentials).status_code==201
                    headers={'Authorization':'Bearer '+client.post('/auth/login',json=credentials).json()['access_token']}
                    wid=client.post('/workspaces',headers=headers,json={'name':'Demo Cơ sở dữ liệu'}).json()['id']
                    path=f'/workspaces/{wid}'
                for document in corpus['documents']:
                    pdf=ROOT/'docs/course'/document['path'];raw=pdf.read_bytes()
                    assert hashlib.sha256(raw).hexdigest()==document['sha256']
                    if client:
                        response=client.post(path+'/documents',headers=headers,files={'file':(pdf.name,raw,'application/pdf')})
                        assert response.status_code==201,response.text
                        docid=response.json()['id']
                        processed=client.post(path+f'/documents/{docid}/process',headers=headers)
                        assert processed.status_code==200 and processed.json()['status']=='ready',processed.text
                        result=client.post(path+f'/documents/{docid}/index',headers=headers)
                        assert result.status_code==200 and result.json()['index_status']=='ready',result.text
                    else:
                        pages=[SimpleNamespace(page_number=i+1,text=p.extract_text()) for i,p in enumerate(PdfReader(pdf).pages)]
                        parts=chunk_pages(pages);vectors=[]
                        for start in range(0,len(parts),config.embedding_batch_size):
                            vectors.extend(embed_batch(config,[p['text'] for p in parts[start:start+config.embedding_batch_size]]))
                        docid=uuid.uuid4()
                        chunks.extend((RetrievalHit(chunk_id=uuid.uuid4(),document_id=docid,filename=pdf.name,score=0,
                                                    **part),vector) for part,vector in zip(parts,vectors))
                for case in cases:
                    started=time.perf_counter();record=dict(case)
                    try:
                        if client:
                            retrieved=client.post(path+'/retrieve',headers=headers,json={'question':case['question'],'top_k':5})
                            assert retrieved.status_code==200,retrieved.text
                            hits=[RetrievalHit(**h) for h in retrieved.json()['results']]
                            response=client.post(path+'/chat',headers=headers,json={'question':case['question']})
                            record['http_status']=response.status_code
                            record['response']=response.json()
                        else:
                            q=embed_batch(config,[case['question']])[0]
                            ranked=sorted(((math.fsum(a*b for a,b in zip(q,v)),h) for h,v in chunks),key=lambda x:x[0],reverse=True)[:5]
                            hits=[h.model_copy(update={'score':score}) for score,h in ranked]
                            answer=generate_answer(config,case['question'],hits)
                            record['response']={'status':'insufficient_context' if answer.insufficient_context else 'answered',
                                                'answer':answer.answer,'sources':[{'source_id':i,**hits[i-1].model_dump(mode='json')} for i in answer.source_ids]}
                        record['retrieval']=[{'filename':h.filename,'page':h.page_number,'score':h.score} for h in hits]
                        record['expected_source_rank']=next((i+1 for i,h in enumerate(hits)
                            if h.filename==case['expected_file'] and h.page_number==case['expected_page']),None)
                    except GenerationError as error:
                        record.update(error=str(error),error_code=error.code,http_status=error.status_code,diagnostics=error.diagnostics)
                    record['elapsed_seconds']=round(time.perf_counter()-started,3)
                    record['review']={'answer_correct':None,'sources_support_claims':None,'notes':''}
                    report['cases'].append(record);save()
                    print(case['id'],record.get('response',{}).get('status',record.get('http_status')),record['elapsed_seconds'],flush=True)
    finally:
        app.main.make_engine=original
        if engine: engine.dispose()
        if admin:
            if schema:
                with admin.begin() as c:c.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
            if before is not None:
                report['public_data_unchanged']=public_snapshot(admin)==before
            admin.dispose()
        report['completed_cases']=len(report['cases']);save()
    if report['public_data_unchanged'] is False: raise SystemExit('Public data changed during evaluation; investigate.')


class _NoClient:
    def __enter__(self): return None
    def __exit__(self,*args): return False


if __name__=='__main__': main()
