"""Integrated learning flow plus an owner-scope audit of every workspace route."""
import uuid
from sqlalchemy import select
from fastapi.routing import APIRoute
from tests.test_auth_workspaces import client, account
from tests.test_retrieval import workspace, seed
from tests.test_plans import ready
from tests.test_quizzes import make
from tests.test_chat import post
from app.quiz_bank import BANK
from app.models import DocumentChunk, Quiz, QuizAttempt, Conversation
from app.routes import owned_workspace


def setup_flow(client,monkeypatch):
    h,w=ready(client,monkeypatch)
    for key,_,_,_,anchor in BANK:
        if key=='sql':seed(client,w,anchor)
    plan=post(client,h,w,'Roadmap SQL; mới bắt đầu; 4 buổi; 45 phút/buổi').json()
    return h,w,plan


def test_end_to_end_plan_quiz_progress_reload(client,monkeypatch):
    h,w,plan=setup_flow(client,monkeypatch);path=f'/workspaces/{w}'
    initial=client.get(path+'/progress',headers=h)
    assert initial.headers['cache-control']=='no-store'
    assert initial.json()['checklist']==dict(completed=0,total=0) # drafts excluded
    pid=plan['roadmap_id']
    assert client.post(path+f'/plans/{pid}/confirm',headers=h,json={'revision':0}).status_code==200
    assert client.patch(path+f'/plans/{pid}/steps/sql',headers=h,json={'revision':1,'done':True}).status_code==200
    quiz=make(client,h,w)
    assert client.get(path+'/progress',headers=h).json()['topics'][1]['attempts']==0
    assert client.post(path+f'/quizzes/{quiz["quiz_id"]}/submit',headers=h,json={'answers':[2,0]}).status_code==200
    data=client.get(path+'/progress',headers=h).json()
    assert data['checklist']==dict(completed=1,total=2)
    assert data['topics'][1]==dict(key='sql',title='SQL và JOIN',attempts=1,correct=1,total=2)
    assert data['recent_results'][0]['conversation_id']==quiz['conversation_id']
    assert data['recent_plans'][0]['conversation_id']==plan['conversation_id']
    assert client.get(path+'/progress',headers=h).json()==data
    assert all(set(r)=={'quiz_id','conversation_id','topic_key','score','total','submitted_at'} for r in data['recent_results'])
    other=workspace(client,h,'Other');bob=account(client,'bob@example.com')
    assert client.get(path+'/progress',headers=bob).status_code==404
    assert client.get(path+'/progress').status_code==401
    assert client.get(f'/workspaces/{other}/progress',headers=h).json()['checklist']['total']==0
    assert client.patch(path+f'/plans/{pid}/steps/sql',headers=h,json={'revision':2,'done':False}).status_code==200
    assert client.get(path+'/progress',headers=h).json()['checklist']['completed']==0


def test_recent_limit_does_not_limit_totals_or_expose_keys(client):
    h=account(client);w=workspace(client,h)
    with client.app.state.session_factory() as s:
        c=Conversation(workspace_id=uuid.UUID(w),title='Many');s.add(c);s.flush()
        for _ in range(25):
            q=Quiz(workspace_id=uuid.UUID(w),conversation_id=c.id,status='approved',spec=dict(topic_key='sql',questions=[{'correct':0},{'correct':1}]))
            s.add(q);s.flush();s.add(QuizAttempt(quiz_id=q.id,answers=[0,0],score=1))
        s.commit()
    response=client.get(f'/workspaces/{w}/progress',headers=h);data=response.json()
    assert len(data['recent_results'])==20
    assert data['topics'][1]['attempts']==25 and data['topics'][1]['total']==50
    assert '"answers"' not in response.text and '"questions"' not in response.text


def test_every_workspace_route_declares_authentication(client):
    operations=[operation for path,methods in client.app.openapi()['paths'].items()
                if '/workspaces/{workspace_id}' in path for method,operation in methods.items()
                if method in ('get','post','patch','delete')]
    assert len(operations)>=20
    for operation in operations: assert operation.get('security'),operation['operationId']


def test_foreign_workspace_all_routes_and_foreign_child_ids(client,monkeypatch):
    h,w,plan=setup_flow(client,monkeypatch);quiz=make(client,h,w)
    bob=account(client,'bob@example.com');other=workspace(client,h,'Other')
    with client.app.state.session_factory() as s:
        chunk=s.scalar(select(DocumentChunk));doc,chunk_id=str(chunk.document_id),str(chunk.id)
    # All user data route families, including mutating operations, must reject
    # a foreign parent before touching files/models/database state.
    calls=[('GET','',None),('PATCH','',{'name':'No'}),('DELETE','',None),('GET','/progress',None),
      ('GET','/documents',None),('POST','/documents','file'),('GET','/conversations',None),
      ('POST','/retrieve',{'question':'SQL','top_k':5}),('POST','/chat',{'question':'Quiz SQL JOIN'}),
      ('GET',f'/conversations/{quiz["conversation_id"]}',None),('GET',f'/sources/{chunk_id}',None),
      ('GET',f'/documents/{doc}',None),('POST',f'/documents/{doc}/process',None),
      ('POST',f'/documents/{doc}/index',None),('GET',f'/documents/{doc}/pages',None),
      ('GET',f'/documents/{doc}/chunks',None),('DELETE',f'/documents/{doc}',None),
      ('GET',f'/plans/{plan["roadmap_id"]}',None),('POST',f'/plans/{plan["roadmap_id"]}/confirm',{'revision':0}),
      ('PATCH',f'/plans/{plan["roadmap_id"]}/steps/sql',{'revision':0,'done':True}),
      ('GET',f'/quizzes/{quiz["quiz_id"]}',None),('POST',f'/quizzes/{quiz["quiz_id"]}/submit',{'answers':[2,3]})]
    for method,suffix,body in calls:
        kwargs={'files':{'file':('demo.pdf',b'%PDF-demo','application/pdf')}} if body=='file' else {'json':body} if body is not None else {}
        assert client.request(method,f'/workspaces/{w}'+suffix,headers=bob,**kwargs).status_code==404,(method,suffix)
        assert client.request(method,f'/workspaces/{w}'+suffix,**kwargs).status_code==401,(method,suffix)
        if any(suffix.startswith(x) for x in ('/documents/','/plans/','/quizzes/','/sources/','/conversations/')):
            assert client.request(method,f'/workspaces/{other}'+suffix,headers=h,**kwargs).status_code==404,(method,suffix)
    assert client.get(f'/workspaces/{w}/plans/{plan["roadmap_id"]}',headers=h).json()['status']=='draft'
    assert client.get(f'/workspaces/{w}/quizzes/{quiz["quiz_id"]}',headers=h).json()['result'] is None


def test_final_evaluation_set_is_frozen_and_separate():
    import hashlib,json
    from pathlib import Path
    root=Path(__file__).parents[2]
    file=root/'docs/evaluation/final-v1.json'
    data=json.loads(file.read_text(encoding='utf-8'))
    lock=json.loads(file.with_suffix('.lock.json').read_text(encoding='utf-8'))
    old=json.loads((root/'docs/evaluation/week7.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(file.read_bytes()).hexdigest()==lock['sha256']
    assert hashlib.sha256((root/'docs/course/manifest.json').read_bytes()).hexdigest()==lock['corpus_manifest_sha256']
    assert len(data['cases'])==40 and len({c['id'] for c in data['cases']})==40
    assert not {c['question'] for c in data['cases']} & {c['question'] for c in old['cases']}
    corpus=json.loads((root/'docs/course/corpus.json').read_text(encoding='utf-8'))
    files={d['filename']:len(d['pages']) for d in corpus['documents']}
    for c in data['cases']:
        if c['expected_file']:
            assert c['expected_file'] in files and 1<=c['expected_page']<=files[c['expected_file']]
            assert c['expected_status']=='answered'
        else:assert c['expected_status']=='insufficient_context'
        assert c['reference']
