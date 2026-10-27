import json
from pathlib import Path
import httpx
import pytest
from sqlalchemy import select, func, delete
from tests.test_auth_workspaces import client, account
from tests.test_retrieval import workspace, seed
from tests.test_chat import post, hit
from app.models import Quiz, QuizAttempt, Document, DocumentChunk
from app.quizzes import validate_draft, generate_draft
from app.generation import GenerationError
from app.quiz_bank import BANK


def ready(client, topic='sql'):
    headers=account(client); wid=workspace(client,headers)
    for key,_,_,_,anchor in BANK:
        if key==topic: seed(client,wid,anchor)
    return headers,wid


def make(client,h,w,question='Quiz SQL JOIN'):
    response=post(client,h,w,question)
    assert response.status_code==200,response.text
    assert response.json()['quiz_id'],response.text
    return response.json()


def test_bank_anchors_exist_in_original_corpus():
    corpus=json.loads((Path(__file__).parents[2]/'docs/course/corpus.json').read_text(encoding='utf-8'))
    text='\n'.join(p['text'] for d in corpus['documents'] for p in d['pages'])
    assert len(BANK)==10
    for _,q,choices,correct,anchor in BANK:
        assert anchor in text and len(set(choices))==4 and 0<=correct<4


def test_private_keys_scoring_reload_and_idempotent_submit(client):
    h,w=ready(client); created=make(client,h,w); path=f'/workspaces/{w}/quizzes/{created["quiz_id"]}'
    assert created['sources']==[] and created['kind']=='quiz'
    before=client.get(path,headers=h); assert before.headers['cache-control']=='no-store'
    assert before.json()['result'] is None
    assert all(set(q)=={'question','choices'} for q in before.json()['questions'])
    history=client.get(f'/workspaces/{w}/conversations/{created["conversation_id"]}',headers=h).text
    for field in ['"correct"','"explanation"','"evidence"']: assert field not in history and field not in before.text
    assert client.post(path+'/submit',headers=h,json={'answers':[2]}).status_code==422
    assert client.post(path+'/submit',headers=h,json={'answers':[2,True]}).status_code==422
    assert client.post(path+'/submit',headers=h,json={'answers':[2,9]}).status_code==422
    assert client.post(path+'/submit',headers=h,json={'answers':[2,0],'score':2}).status_code==422
    result=client.post(path+'/submit',headers=h,json={'answers':[2,0]})
    assert result.status_code==200,result.text
    assert result.json()['result']['score']==1 and result.json()['result']['total']==2
    assert client.get(path,headers=h).json()['result']==result.json()['result']
    assert client.post(path+'/submit',headers=h,json={'answers':[2,0]}).json()['result']==result.json()['result']
    assert client.post(path+'/submit',headers=h,json={'answers':[2,3]}).status_code==409
    with client.app.state.session_factory() as s: assert s.scalar(select(func.count()).select_from(QuizAttempt))==1


def test_quiz_isolation_all_endpoints(client):
    h,w=ready(client); created=make(client,h,w); qid=created['quiz_id']
    other=workspace(client,h,'Other'); bob=account(client,'bob@example.com')
    for auth,wid in [(bob,w),(h,other)]:
        path=f'/workspaces/{wid}/quizzes/{qid}'
        assert client.get(path,headers=auth).status_code==404
        assert client.post(path+'/submit',headers=auth,json={'answers':[2,3]}).status_code==404
    assert client.get(f'/workspaces/{w}/quizzes/{qid}').status_code==401


def test_missing_topic_sources_and_draft_not_gradable(client,monkeypatch):
    h,w=ready(client)
    assert post(client,h,w,'Quiz').json()['quiz_id'] is None
    assert post(client,h,w,'Quiz transaction').json()['quiz_id'] is None
    monkeypatch.setattr('app.quizzes.generate_draft',lambda *a:[dict(question='Câu hỏi bản nháp?',choices=['A','B','C','D'],correct=0,explanation='Giải thích nháp',evidence='nguồn nháp',source_id=1)])
    draft=make(client,h,w,'Sinh mới quiz SQL JOIN')
    path=f'/workspaces/{w}/quizzes/{draft["quiz_id"]}'
    assert client.get(path,headers=h).json()['status']=='draft'
    assert client.post(path+'/submit',headers=h,json={'answers':[0]}).status_code==409


def test_generation_failure_and_deleted_source_do_not_save_quiz(client,monkeypatch):
    h,w=ready(client)
    def bad(*a): raise GenerationError('invalid')
    monkeypatch.setattr('app.quizzes.generate_draft',bad)
    assert post(client,h,w,'Sinh mới quiz SQL JOIN').status_code==502
    def deleted(*a):
        with client.app.state.session_factory() as s:
            s.execute(delete(DocumentChunk));s.commit()
        return []
    monkeypatch.setattr('app.quizzes.generate_draft',deleted)
    assert post(client,h,w,'Sinh mới quiz SQL JOIN').status_code==409
    with client.app.state.session_factory() as s: assert s.scalar(select(func.count()).select_from(Quiz))==0


def raw_draft():
    return dict(questions=[dict(question=f'Câu hỏi trắc nghiệm số {i}?',choices=['A','B','C','D'],correct=0,
        explanation='Khóa chính không null.',source_id=1,evidence='PRIMARY KEY is unique and not null.') for i in range(3)])


@pytest.mark.parametrize('change',['source','quote','duplicate','choices','boolean','extra','copied_question'])
def test_reject_malformed_drafts(change):
    body=raw_draft();q=body['questions'][0]
    if change=='source':q['source_id']=2
    if change=='quote':q['evidence']='invented unsupported quote'
    if change=='duplicate':body['questions'][1]=q
    if change=='choices':q['choices']=['A',' A ','C','D']
    if change=='boolean':q['correct']=True
    if change=='extra':q['score']=100
    if change=='copied_question':q['choices'][0]=body['questions'][1]['question']
    with pytest.raises(ValueError): validate_draft(body,[hit()])


@pytest.mark.parametrize('mode',['valid','length','timeout','http','invalid'])
def test_ollama_contract(client,monkeypatch,mode):
    original=httpx.Client
    def handler(request):
        payload=json.loads(request.content)
        assert payload['think'] is False and payload['format']['type']=='object'
        if mode=='timeout':raise httpx.ReadTimeout('secret')
        return httpx.Response(503 if mode=='http' else 200,json=dict(done=True,done_reason='length' if mode=='length' else 'stop',message=dict(content=json.dumps({} if mode=='invalid' else {f'q{i+1}':dict(q,choices=dict(zip('ABCD',q['choices']))) for i,q in enumerate(raw_draft()['questions'])}))))
    monkeypatch.setattr('app.quizzes.httpx.Client',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    if mode=='valid':assert len(generate_draft(client.app.state.settings,'SQL',[hit()]))==3
    else:
        with pytest.raises(GenerationError):generate_draft(client.app.state.settings,'SQL',[hit()])


def test_pdf_linebreaks_do_not_break_evidence_match(client):
    h=account(client);w=workspace(client,h)
    for key,_,_,_,anchor in BANK:
        if key=='sql':seed(client,w,anchor.replace(' ', '\n'))
    assert make(client,h,w)['quiz_id']


def test_related_plan_and_stale_conversation_do_not_leak_or_duplicate(client,monkeypatch):
    from tests.test_plans import ready as plan_ready
    h,w=plan_ready(client,monkeypatch)
    for key,_,_,_,anchor in BANK:
        if key=='sql':seed(client,w,anchor)
    plan=post(client,h,w,'Roadmap SQL; mới bắt đầu; 4 buổi; 45 phút/buổi').json()
    assert client.post(f'/workspaces/{w}/plans/{plan["roadmap_id"]}/confirm',headers=h,json={'revision':0}).status_code==200
    created=make(client,h,w)
    public=client.get(f'/workspaces/{w}/quizzes/{created["quiz_id"]}',headers=h).json()
    assert public['related_plan']==dict(conversation_id=plan['conversation_id'],plan_id=plan['roadmap_id'],step_key='sql')
    assert post(client,h,w,'Quiz SQL JOIN',conversation_id=created['conversation_id'],revision=0).status_code==409
    with client.app.state.session_factory() as s:assert s.scalar(select(func.count()).select_from(Quiz))==1


def test_saved_quiz_still_grades_after_source_deleted(client):
    h,w=ready(client);created=make(client,h,w)
    with client.app.state.session_factory() as s:
        s.execute(delete(DocumentChunk));s.commit()
    response=client.post(f'/workspaces/{w}/quizzes/{created["quiz_id"]}/submit',headers=h,json={'answers':[2,3]})
    assert response.status_code==200 and response.json()['result']['score']==2
    source=response.json()['result']['sources'][0]
    assert client.get(f'/workspaces/{w}/sources/{source["chunk_id"]}',headers=h).status_code==404
    assert source['text']


def test_many_topic_mentions_do_not_displace_bank_evidence(client):
    h,w=ready(client)
    for i in range(20):seed(client,w,f'SQL mention without actual quiz evidence {i}')
    assert make(client,h,w)['quiz_id']
