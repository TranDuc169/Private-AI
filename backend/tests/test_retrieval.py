import os
import uuid
import pytest
from sqlalchemy import func, select

from app.embedding import EmbeddingError
from app.models import Document, DocumentChunk, Conversation, Message
from tests.test_auth_workspaces import client, account

postgres = pytest.mark.skipif(not os.environ.get('TEST_DATABASE_URL'), reason='Retrieval needs real PostgreSQL/pgvector')


def workspace(client, headers, name='Retrieval'):
    return client.post('/workspaces', headers=headers, json={'name':name}).json()['id']


def seed(client, wid, name, numbers=(1.0,0.0), status='ready', model='bge-m3:latest', parse='ready', chunk_model=None):
    with client.app.state.session_factory() as session:
        doc = Document(workspace_id=uuid.UUID(wid),filename=name,status=parse,index_status=status,
                       page_count=1,chunk_count=1,embedding_model=model)
        session.add(doc); session.flush()
        chunk=DocumentChunk(document_id=doc.id,chunk_index=0,page_number=1,start_char=0,end_char=len(name),
                            text=name,embedding=list(numbers)+[0.0]*(1024-len(numbers)),embedding_model=chunk_model or model)
        session.add(chunk); session.commit()
        return str(doc.id)


def query(client, headers, wid, **values):
    return client.post(f'/workspaces/{wid}/retrieve',headers=headers,json={'question':'Câu hỏi thử','top_k':5,**values})


def test_auth_validation_empty_workspace_does_not_call_ollama(client,monkeypatch):
    alice=account(client); wid=workspace(client,alice)
    bob=account(client,'bob@example.com')
    def unexpected(*args,**kwargs): raise AssertionError('Must not call Ollama')
    monkeypatch.setattr('app.retrieval.embed_batch',unexpected)
    assert query(client,{},wid).status_code==401
    assert query(client,bob,wid).status_code==404
    assert query(client,alice,str(uuid.uuid4())).status_code==404
    for values in [{'question':'  '},{'question':'x'*2001},{'top_k':0},{'top_k':11},{'top_k':True},{'top_k':'5'},{'owner_id':'fake'}]:
        assert query(client,alice,wid,**values).status_code==422
    response=query(client,alice,wid,question='  Câu hỏi  ')
    assert response.status_code==200 and response.json()['results']==[]
    assert response.json()['question']=='Câu hỏi'
    assert response.headers['cache-control']=='no-store'


@postgres
def test_filter_workspace_before_top_k_and_exclude_unready_or_wrong_model(client,monkeypatch):
    alice=account(client); target=workspace(client,alice); other=workspace(client,alice,'Other')
    bob=account(client,'bob@example.com'); foreign=workspace(client,bob,'Private')
    expected=seed(client,target,'own.pdf',(0.8,0.6))
    seed(client,other,'same-user-other-workspace.pdf')
    seed(client,foreign,'other-user-secret.pdf')
    for state in ['pending','processing','failed']:
        seed(client,target,state+'.pdf',status=state)
    seed(client,target,'parse-failed.pdf',parse='failed')
    seed(client,target,'wrong-model.pdf',model='different-model')
    seed(client,target,'wrong-chunk-model.pdf',chunk_model='different-model')
    monkeypatch.setattr('app.retrieval.embed_batch',lambda config,texts:[[1.0]+[0.0]*1023])
    response=query(client,alice,target,top_k=1)
    assert response.status_code==200,response.text
    hits=response.json()['results']
    assert len(hits)==1 and hits[0]['document_id']==expected
    assert hits[0]['score']==pytest.approx(0.8,abs=1e-5)
    assert hits[0]['page_number']==1 and hits[0]['text']=='own.pdf'
    assert not {'embedding','password_hash','owner_id'} & set(hits[0])
    assert len(query(client,alice,target,top_k=10).json()['results'])==1
    assert query(client,bob,target).status_code==404


@postgres
def test_ranking_top_k_stable_ties_and_delete_removes_results(client,monkeypatch):
    headers=account(client); wid=workspace(client,headers)
    best=seed(client,wid,'best.pdf',(1,0))
    seed(client,wid,'second.pdf',(0.8,0.6)); seed(client,wid,'third.pdf',(0,1))
    monkeypatch.setattr('app.retrieval.embed_batch',lambda config,texts:[[1.0]+[0.0]*1023])
    hits=query(client,headers,wid,top_k=2).json()['results']
    assert [h['filename'] for h in hits]==['best.pdf','second.pdf']
    assert query(client,headers,wid,top_k=2).json()['results']==hits
    assert client.delete(f'/workspaces/{wid}/documents/{best}',headers=headers).status_code==204
    assert query(client,headers,wid,top_k=1).json()['results'][0]['filename']=='second.pdf'
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Conversation))==0
        assert session.scalar(select(func.count()).select_from(Message))==0


@postgres
def test_ollama_failure_returns_actionable_503_and_retry_works(client,monkeypatch):
    headers=account(client); wid=workspace(client,headers);seed(client,wid,'ready.pdf')
    def offline(*args): raise EmbeddingError('Không kết nối được Ollama.')
    monkeypatch.setattr('app.retrieval.embed_batch',offline)
    response=query(client,headers,wid)
    assert response.status_code==503 and 'Ollama' in response.json()['detail']
    monkeypatch.setattr('app.retrieval.embed_batch',lambda config,texts:[[1.0]+[0.0]*1023])
    assert query(client,headers,wid).json()['results'][0]['filename']=='ready.pdf'


@postgres
def test_document_deleted_during_embedding_cannot_leak_stale_text(client,monkeypatch):
    headers=account(client); wid=workspace(client,headers);doc_id=seed(client,wid,'delete-me.pdf')
    def embed(config,texts):
        assert client.delete(f'/workspaces/{wid}/documents/{doc_id}',headers=headers).status_code==204
        return [[1.0]+[0.0]*1023]
    monkeypatch.setattr('app.retrieval.embed_batch',embed)
    assert query(client,headers,wid).json()['results']==[]
