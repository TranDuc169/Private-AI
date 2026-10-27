import uuid
from sqlalchemy import select, delete, func

from tests.test_auth_workspaces import client, account
from tests.test_chat import populated, post, response_body
from tests.test_retrieval import workspace, seed
from app.models import Conversation, Message, Document, DocumentChunk
from app.generation import ModelAnswer, GenerationError
from app.summaries import summary_topic, collect_topic, summarize


def test_late_generation_cannot_overwrite_newer_revision(client, monkeypatch):
    headers, wid, _ = populated(client, monkeypatch)
    monkeypatch.setattr('app.chat.generate_answer', lambda *args: ModelAnswer(**response_body()))
    initial = post(client, headers, wid).json()
    def concurrent(*args):
        from sqlalchemy import update
        with client.app.state.session_factory() as session:
            session.execute(update(Conversation).where(Conversation.id == uuid.UUID(initial['conversation_id'])).values(revision=2))
            session.commit()
        return ModelAnswer(**response_body())
    monkeypatch.setattr('app.chat.generate_answer', concurrent)
    assert post(client, headers, wid, conversation_id=initial['conversation_id'], revision=1).status_code == 409
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Message)) == 2


def test_history_roundtrip_isolated_and_revision_checked(client, monkeypatch):
    headers, wid, docid = populated(client, monkeypatch)
    monkeypatch.setattr('app.chat.generate_answer', lambda *args: ModelAnswer(**response_body()))
    result = post(client, headers, wid).json()
    cid = result['conversation_id']
    detail = f'/workspaces/{wid}/conversations/{cid}'
    saved = client.get(detail, headers=headers)
    assert saved.headers['cache-control'] == 'no-store'
    assert [m['role'] for m in saved.json()['messages']] == ['user', 'assistant']
    assert saved.json()['messages'][1]['result'] == result
    bob = account(client, 'bob@example.com')
    assert client.get(detail, headers=bob).status_code == 404
    assert client.get(detail).status_code == 401
    second = workspace(client, headers, 'Other')
    assert client.get(f'/workspaces/{second}/conversations/{cid}', headers=headers).status_code == 404
    assert post(client, headers, second, conversation_id=cid, revision=1).status_code == 404
    assert post(client, headers, wid, conversation_id=cid, revision=0).status_code == 409
    assert post(client, headers, wid, conversation_id=cid, revision=1).json()['revision'] == 2
    assert len(client.get(detail, headers=headers).json()['messages']) == 4
    source = result['sources'][0]
    source_path = f'/workspaces/{wid}/sources/{source["chunk_id"]}'
    assert client.get(source_path, headers=headers).json()['text'] == source['text']
    assert client.get(source_path, headers=bob).status_code == 404
    assert client.get(f'/workspaces/{second}/sources/{source["chunk_id"]}', headers=headers).status_code == 404
    with client.app.state.session_factory() as session:
        session.execute(delete(Document).where(Document.id == uuid.UUID(docid))); session.commit()
    assert client.get(source_path, headers=headers).status_code == 404
    assert client.get(detail, headers=headers).json()['messages'][1]['result']['sources'] == result['sources']


def test_generation_failure_does_not_save_partial_turn(client, monkeypatch):
    headers, wid, _ = populated(client, monkeypatch)
    def fail(*args): raise GenerationError('Timeout', 504)
    monkeypatch.setattr('app.chat.generate_answer', fail)
    assert post(client, headers, wid).status_code == 504
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Message)) == 0
        assert session.scalar(select(func.count()).select_from(Conversation)) == 0


def test_summary_intent_and_clarification_without_models(client, monkeypatch):
    headers = account(client); wid = workspace(client, headers)
    assert summary_topic('Tóm tắt transaction') == 'Transaction'
    assert summary_topic('tom tat JOIN') == 'SQL và JOIN'
    assert summary_topic('Tóm tắt JOIN và transaction') is None
    assert summary_topic('Transaction là gì?') is False
    def unexpected(*args): raise AssertionError('No model/retrieval needed')
    monkeypatch.setattr('app.chat.retrieve_hits', unexpected)
    result = post(client, headers, wid, 'Tóm tắt giúp tôi').json()
    assert result['status'] == 'insufficient_context' and result['kind'] == 'summary'
    assert result['sources'] == [] and 'chủ đề' in result['answer']
    empty = post(client, headers, wid, 'Tóm tắt transaction').json()
    assert empty['coverage']['selected_chunks'] == 0


def test_topic_selection_covers_pages_and_excludes_foreign_pending(client, monkeypatch):
    headers = account(client); wid = workspace(client, headers)
    other = workspace(client, headers, 'Other')
    own = seed(client, wid, 'transactions.pdf'); seed(client, other, 'secret.pdf')
    with client.app.state.session_factory() as session:
        owner_id = session.get(Document, uuid.UUID(own)).workspace_id
        from app.models import Workspace
        owner_id = session.get(Workspace, owner_id).owner_id
        source = session.scalar(select(DocumentChunk).where(DocumentChunk.document_id == uuid.UUID(own)))
        source.text = 'Transaction BEGIN COMMIT.'
        for i in range(1, 12):
            session.add(DocumentChunk(document_id=uuid.UUID(own), chunk_index=i, page_number=i+1,
                start_char=0, end_char=30, text=f'Transaction page {i+1}. COMMIT.',
                embedding=[1.0]+[0.0]*1023, embedding_model=source.embedding_model))
        session.commit()
        hits, coverage = collect_topic(session, client.app.state.settings, uuid.UUID(wid), owner_id, 'Transaction')
        assert len(hits) == 8 and len({h.page_number for h in hits}) == 8
        assert coverage['partial'] and coverage['matched_chunks'] == 12
        assert {str(h.document_id) for h in hits} == {own}
        assert hits[0].page_number == 1 and hits[-1].page_number == 12
        doc = session.get(Document, uuid.UUID(own)); doc.index_status = 'pending'; session.commit()
        hits, _ = collect_topic(session, client.app.state.settings, uuid.UUID(wid), owner_id, 'Transaction')
        assert hits == []


def test_summary_batches_remap_citations(client, monkeypatch):
    from tests.test_chat import hit
    batches = []
    def generate(config, question, hits):
        batches.append(hits)
        return ModelAnswer(answer='Ý chính [1].', source_ids=[1], insufficient_context=False)
    monkeypatch.setattr('app.summaries.generate_answer', generate)
    answer, sources = summarize(client.app.state.settings, 'Tóm tắt transaction', [hit() for _ in range(7)])
    assert list(map(len, batches)) == [4, 3]
    assert sources == [1, 5] and '[5]' in answer
