"""Workspace-scoped RAG with atomic, revision-checked conversation turns."""
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.generation import GenerationError, generate_answer
from app.models import Document, DocumentChunk, Workspace, Conversation, Message, StudyPlan, StudyStep, Quiz
from app.retrieval import candidate_filters, retrieve_hits
from app.routes import owned_workspace
from app.history import get_conversation
from app.quizzes import is_quiz_request, prepare_quiz
from app.planning import is_plan_request, parse_request, prepare_plan
from app.summaries import summary_topic, collect_topic, summarize, TOPICS
from app.schemas import RetrievalHit
from app.security import get_session
from uuid import UUID

router = APIRouter(prefix='/workspaces/{workspace_id}', tags=['Learning chat'])


class ChatInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None
    revision: int = Field(default=0, ge=0, strict=True)


class ChatSource(RetrievalHit):
    source_id: int


class ChatOut(BaseModel):
    workspace_id: UUID
    question: str
    status: Literal['answered', 'insufficient_context', 'no_documents']
    answer: str
    sources: list[ChatSource]
    model: str
    elapsed_ms: int
    conversation_id: UUID
    revision: int
    kind: Literal["answer", "summary", "roadmap", "quiz"] = "answer"
    coverage: dict | None = None
    quiz_id: UUID | None = None
    roadmap_id: UUID | None = None
    planning_request: dict | None = None


@router.post('/chat', response_model=ChatOut)
def chat(data: ChatInput, request: Request, response: Response,
         workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    response.headers['Cache-Control'] = 'no-store'
    started = time.perf_counter()
    config = request.app.state.settings
    workspace_id, owner_id = workspace.id, workspace.owner_id
    previous_plan = None
    if data.conversation_id:
        conversation = get_conversation(session, workspace_id, data.conversation_id)
        if conversation.revision != data.revision:
            raise HTTPException(409, 'Hội thoại đã thay đổi. Mở lại lịch sử trước khi gửi tiếp.')
        if conversation.revision >= 50:
            raise HTTPException(409, 'Hội thoại đã đủ 50 lượt. Hãy tạo hội thoại mới.')
        last = session.scalar(select(Message).where(Message.conversation_id == data.conversation_id,
            Message.role == 'assistant').order_by(Message.position.desc().nulls_last(), Message.created_at.desc()).limit(1))
        if last and last.payload and last.payload.get('kind') == 'roadmap' and not last.payload.get('roadmap_id'):
            previous_plan = last.payload.get('planning_request')
    elif data.revision != 0:
        raise HTTPException(422, 'Hội thoại mới phải có revision bằng 0.')
    session.rollback()
    # One generation pipeline at a time per process: do not queue unbounded GPU work.
    slot = request.app.state.chat_slot
    if not slot.acquire(blocking=False):
        raise HTTPException(429, 'Model đang xử lý câu hỏi khác. Vui lòng thử lại sau.', headers={'Retry-After': '5'})
    try:
        plan_spec, planning_request, quiz_spec = None, None, None
        plan_mode = is_plan_request(data.question) or (previous_plan is not None and parse_request(data.question, previous_plan)[0] != previous_plan)
        if is_quiz_request(data.question):
            quiz_spec, hits, answer = prepare_quiz(session, config, workspace_id, owner_id, data.question)
            kind, coverage = 'quiz', None
            status = 'answered' if quiz_spec else 'insufficient_context'
            # Private quiz sources/keys must never enter the chat/history payload.
            sources = []
            if hits:
                current = set(session.scalars(select(DocumentChunk.id).join(Document).join(Workspace).where(
                    *candidate_filters(workspace_id, owner_id, config.embedding_model), DocumentChunk.id.in_([h.chunk_id for h in hits]))))
                session.rollback()
                if current != {h.chunk_id for h in hits}:
                    raise HTTPException(409, 'Nguồn đã thay đổi trong lúc tạo quiz. Hãy gửi lại.')
        elif plan_mode:
            plan_spec, hits, planning_request, answer = prepare_plan(session, config, workspace_id, owner_id, data.question, previous_plan)
            kind, coverage = 'roadmap', None
            status = 'answered' if plan_spec else 'insufficient_context'
            sources = [ChatSource(**h.model_dump(), source_id=i) for i,h in enumerate(hits, 1)]
            if hits:
                current = set(session.scalars(select(DocumentChunk.id).join(Document).join(Workspace).where(
                    *candidate_filters(workspace_id, owner_id, config.embedding_model), DocumentChunk.id.in_([h.chunk_id for h in hits]))))
                session.rollback()
                if current != {h.chunk_id for h in hits}:
                    raise HTTPException(409, 'Nguồn đã thay đổi trong lúc tạo kế hoạch. Hãy gửi lại.')
        else:
            topic = summary_topic(data.question)
            coverage = None
            kind = 'answer' if topic is False else 'summary'
            if topic:
                hits, coverage = collect_topic(session, config, workspace_id, owner_id, topic)
            elif topic is False:
                hits = retrieve_hits(session, config, workspace_id, owner_id, data.question, 5)
            else:
                hits = []
            sources = []
            if topic is None:
                status = 'insufficient_context'
                answer = 'Bạn muốn tóm tắt chủ đề nào? Hãy chọn một chủ đề trong câu hỏi: ' + '; '.join(TOPICS) + '.'
            elif not hits:
                status = 'insufficient_context' if topic else 'no_documents'
                answer = ('Chưa tìm thấy đoạn phù hợp chủ đề. Hãy bổ sung PDF hoặc hỏi rõ hơn.' if topic else 'Workspace chưa có đoạn tài liệu sẵn sàng. Hãy upload PDF và tạo vector trong Tài liệu trước.')
            else:
                if topic:
                    answer, source_ids = summarize(config, data.question, hits)
                    status = 'answered' if source_ids else 'insufficient_context'
                else:
                    result = generate_answer(config, data.question, hits)
                    status = 'insufficient_context' if result.insufficient_context else 'answered'
                    answer, source_ids = result.answer, result.source_ids
                # Re-check after the model call: a document may have been deleted/reindexed meanwhile.
                current_ids = set(session.scalars(select(DocumentChunk.id).join(Document).join(Workspace)
                    .where(*candidate_filters(workspace_id, owner_id, config.embedding_model),
                           DocumentChunk.id.in_([h.chunk_id for h in hits]))))
                session.rollback()
                if current_ids != {h.chunk_id for h in hits}:
                    raise HTTPException(409, 'Tài liệu đã thay đổi trong lúc trả lời. Vui lòng gửi lại câu hỏi.')
                sources = [ChatSource(**hits[i-1].model_dump(), source_id=i) for i in source_ids]
        # Persist the question/answer pair together, only after successful generation.
        # CAS prevents late/concurrent requests appending onto an out-of-date transcript.
        if data.conversation_id:
            changed = session.execute(update(Conversation).where(
                Conversation.id == data.conversation_id, Conversation.workspace_id == workspace_id,
                Conversation.revision == data.revision).values(revision=data.revision+1))
            if changed.rowcount != 1:
                session.rollback()
                raise HTTPException(409, 'Hội thoại đã thay đổi. Mở lại lịch sử trước khi gửi tiếp.')
            conversation_id = data.conversation_id
        else:
            conversation = Conversation(workspace_id=workspace_id, title=data.question[:200], revision=1)
            session.add(conversation); session.flush()
            conversation_id = conversation.id
        quiz_id = None
        if quiz_spec:
            quiz_spec['sources'] = [ChatSource(**h.model_dump(), source_id=i).model_dump(mode='json') for i,h in enumerate(hits,1)]
            quiz = Quiz(workspace_id=workspace_id, conversation_id=conversation_id, status=quiz_spec['status'], spec=quiz_spec)
            session.add(quiz); session.flush(); quiz_id = quiz.id
        roadmap_id = None
        if plan_spec:
            plan_spec['sources'] = [source.model_dump(mode='json') for source in sources]
            plan = StudyPlan(workspace_id=workspace_id, conversation_id=conversation_id, spec=plan_spec, status='draft', revision=0)
            session.add(plan); session.flush(); roadmap_id = plan.id
            session.add_all([StudyStep(plan_id=plan.id, step_key=step['key'], done=False) for step in plan_spec['steps']])
        output = ChatOut(workspace_id=workspace_id, question=data.question, status=status,
            answer=answer, sources=sources, model=('Bộ demo ' + quiz_spec['bank_version'] if quiz_spec and quiz_spec.get('bank_version') else config.chat_model), kind=kind, coverage=coverage,
            conversation_id=conversation_id, revision=data.revision+1, quiz_id=quiz_id, roadmap_id=roadmap_id, planning_request=planning_request,
            elapsed_ms=round((time.perf_counter()-started)*1000))
        session.add_all([
            Message(conversation_id=conversation_id, role='user', content=data.question, position=data.revision*2),
            Message(conversation_id=conversation_id, role='assistant', content=answer,
                    position=data.revision*2+1, payload=output.model_dump(mode='json'))])
        session.commit()
        return output
    except GenerationError as error:
        raise HTTPException(error.status_code, str(error)) from None
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, 'Không lưu được hội thoại hoặc kiểm tra nguồn trong database. Vui lòng thử lại.') from None
    finally:
        slot.release()
