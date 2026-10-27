import json
from collections import defaultdict
import httpx
import pytest
from sqlalchemy import select, func
from tests.test_auth_workspaces import client, account
from tests.test_retrieval import workspace, seed
from tests.test_chat import post, hit
from app.models import StudyPlan
from app.planning import parse_request, ordered_steps, allocate, DraftPlan, DraftStep, generate_plan
from app.generation import GenerationError

@pytest.mark.parametrize('goal', ['relations','sql','erd','transaction','index','all'])
@pytest.mark.parametrize('level', ['beginner','basic'])
def test_graph_and_schedule(goal,level):
    req=dict(goal=goal,level=level,sessions=5,minutes_per_session=45)
    steps,_=allocate(req,ordered_steps(req));seen=set();sessions=defaultdict(int)
    for step in steps:
        assert set(step['prerequisites']) <= seen
        seen.add(step['key'])
        assert sum(x['minutes'] for x in step['schedule']) == step['minutes'] >= 20
        for x in step['schedule']:
            assert 1 <= x['session'] <= 5
            sessions[x['session']] += x['minutes']
    assert max(sessions.values()) <= 45
    assert sum(s['minutes'] for s in steps) <= 225

def test_missing_inputs_and_short_budget():
    req,missing=parse_request('Lập roadmap học SQL JOIN')
    assert req['goal']=='sql' and len(missing)==3
    assert not parse_request('mới bắt đầu; 4 buổi; 45 phút/buổi',req)[1]
    assert parse_request('roadmap SQL 0 buổi 999 phút/buổi')[1]
    assert allocate(dict(sessions=1,minutes_per_session=15),['relations','sql'])[0] is None

def ready(client,monkeypatch):
    h=account(client);w=workspace(client,h)
    seed(client,w,'Quan hệ ràng buộc PRIMARY KEY FOREIGN KEY.')
    seed(client,w,'SQL JOIN SELECT bảng.')
    monkeypatch.setattr('app.planning.generate_plan',lambda config,steps,hits:DraftPlan(steps=[DraftStep(key=s['key'],objective='Hiểu nội dung nguồn.',activity='Đọc và giải thích ví dụ.',source_ids=s['source_ids']) for s in steps]))
    return h,w

def test_confirmation_progress_reload_and_isolation(client,monkeypatch):
    h,w=ready(client,monkeypatch)
    first=post(client,h,w,'Lập roadmap SQL JOIN').json()
    assert first['roadmap_id'] is None
    result=post(client,h,w,'mới bắt đầu; 4 buổi; 45 phút/buổi',conversation_id=first['conversation_id'],revision=first['revision'])
    assert result.status_code==200,result.text
    pid=result.json()['roadmap_id'];assert pid
    path=f'/workspaces/{w}/plans/{pid}'
    plan=client.get(path,headers=h).json()
    assert plan['status']=='draft' and len(plan['spec']['steps'])==2
    assert client.patch(path+'/steps/sql',headers=h,json={'revision':0,'done':True}).status_code==409
    bob=account(client,'bob@example.com');other=workspace(client,h,'Other')
    for fh,p in [(bob,path),(h,f'/workspaces/{other}/plans/{pid}')]:
        assert client.get(p,headers=fh).status_code==404
        assert client.post(p+'/confirm',headers=fh,json={'revision':0}).status_code==404
        assert client.patch(p+'/steps/sql',headers=fh,json={'revision':0,'done':True}).status_code==404
    assert client.get(path).status_code==401
    assert client.post(path+'/confirm',headers=h,json={'revision':0}).json()['revision']==1
    assert client.patch(path+'/steps/sql',headers=h,json={'revision':1,'done':True}).json()['progress']['sql'] is True
    assert client.patch(path+'/steps/sql',headers=h,json={'revision':1,'done':False}).status_code==409
    assert client.patch(path+'/steps/sql',headers=h,json={'revision':2,'done':'yes'}).status_code==422
    assert client.patch(path+'/steps/missing',headers=h,json={'revision':2,'done':True}).status_code==404
    assert client.get(path,headers=h).json()['progress']['sql'] is True
    history=client.get(f'/workspaces/{w}/conversations/{first["conversation_id"]}',headers=h).json()
    assert history['messages'][-1]['result']['roadmap_id']==pid
    assert client.patch(path+'/steps/sql',headers=h,json={'revision':2,'done':False}).json()['progress']['sql'] is False

def test_no_plan_without_budget_sources_or_valid_model(client,monkeypatch):
    h,w=ready(client,monkeypatch)
    assert post(client,h,w,'Roadmap SQL; mới bắt đầu; 1 buổi; 15 phút/buổi').json()['roadmap_id'] is None
    assert post(client,h,w,'Roadmap transaction; mới bắt đầu; 4 buổi; 45 phút/buổi').json()['roadmap_id'] is None
    def bad(*args):raise GenerationError('Invalid schema')
    monkeypatch.setattr('app.planning.generate_plan',bad)
    assert post(client,h,w,'Roadmap SQL; mới bắt đầu; 4 buổi; 45 phút/buổi').status_code==502
    with client.app.state.session_factory() as s:assert s.scalar(select(func.count()).select_from(StudyPlan))==0

@pytest.mark.parametrize('change',['foreign_source','missing_step','extra_field','length','timeout'])
def test_model_contract_rejects_invalid_plans(client,monkeypatch,change):
    body=dict(steps=[dict(key='sql',objective='Hiểu phép JOIN.',activity='Đọc và giải thích JOIN.',source_ids=[1])])
    if change=='foreign_source':body['steps'][0]['source_ids']=[2]
    if change=='missing_step':body['steps'][0]['key']='other'
    if change=='extra_field':body['steps'][0]['minutes']=999
    original=httpx.Client
    def handle(request):
        if change=='timeout':raise httpx.ReadTimeout('private detail')
        return httpx.Response(200,json={'done':True,'done_reason':'length' if change=='length' else 'stop','message':{'content':json.dumps({x['key']:{k:v for k,v in x.items() if k!='key'} for x in body['steps']})}})
    monkeypatch.setattr('app.planning.httpx.Client',lambda **kwargs:original(transport=httpx.MockTransport(handle),**kwargs))
    with pytest.raises(GenerationError):generate_plan(client.app.state.settings,[{'key':'sql','source_ids':[1]}],[hit()])

def test_model_order_is_normalized_but_sources_stay_with_each_step(client,monkeypatch):
    body={'steps':[{'key':'sql','objective':'Hiểu phép nối.', 'activity':'Đọc ví dụ SQL JOIN.', 'source_ids':[2]},
                   {'key':'relations','objective':'Hiểu khóa chính.', 'activity':'Đọc ràng buộc khóa.', 'source_ids':[1]}]}
    original=httpx.Client
    transport=httpx.MockTransport(lambda req:httpx.Response(200,json={'done':True,'message':{'content':json.dumps({x['key']:{k:v for k,v in x.items() if k!='key'} for x in body['steps']})}}))
    monkeypatch.setattr('app.planning.httpx.Client',lambda **kwargs:original(transport=transport,**kwargs))
    result=generate_plan(client.app.state.settings,[{'key':'relations','source_ids':[1]},{'key':'sql','source_ids':[2]}],[hit(),hit()])
    assert [s.key for s in result.steps]==['relations','sql']
    assert result.steps[1].source_ids==[2]

@pytest.mark.parametrize('value',['-1 buổi','1.5 buổi','0 buổi','99 buổi'])
def test_invalid_session_count_does_not_silently_become_valid(value):
    _,missing=parse_request('Roadmap SQL; mới bắt đầu; '+value+'; 45 phút/buổi')
    assert any('số buổi' in item for item in missing)
