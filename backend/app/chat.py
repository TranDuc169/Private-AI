"""Stateless, workspace-scoped RAG. Conversation persistence is a later milestone."""
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.generation import GenerationError, generate_answer
from app.models import Document, DocumentChunk, Workspace
from app.retrieval import candidate_filters, retrieve_hits
from app.routes import owned_workspace
from app.schemas import RetrievalHit
from app.security import get_session
from uuid import UUID

router = APIRouter(prefix='/workspaces/{workspace_id}', tags=['Learning chat'])


class ChatInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=2000)


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


@router.post('/chat', response_model=ChatOut)
def chat(data: ChatInput, request: Request, response: Response,
         workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    response.headers['Cache-Control'] = 'no-store'
    started = time.perf_counter()
    config = request.app.state.settings
    workspace_id, owner_id = workspace.id, workspace.owner_id
    # One generation pipeline at a time per process: do not queue unbounded GPU work.
    slot = request.app.state.chat_slot
    if not slot.acquire(blocking=False):
        raise HTTPException(429, 'Model đang xử lý câu hỏi khác. Vui lòng thử lại sau.', headers={'Retry-After': '5'})
    try:
        hits = retrieve_hits(session, config, workspace_id, owner_id, data.question, 5)
        sources = []
        if not hits:
            status = 'no_documents'
            answer = 'Workspace chưa có đoạn tài liệu sẵn sàng. Hãy upload PDF và tạo vector trong Tài liệu trước.'
        else:
            result = generate_answer(config, data.question, hits)
            # Re-check after the model call: a document may have been deleted/reindexed meanwhile.
            current_ids = set(session.scalars(select(DocumentChunk.id).join(Document).join(Workspace)
                .where(*candidate_filters(workspace_id, owner_id, config.embedding_model),
                       DocumentChunk.id.in_([h.chunk_id for h in hits]))))
            session.rollback()
            if current_ids != {h.chunk_id for h in hits}:
                raise HTTPException(409, 'Tài liệu đã thay đổi trong lúc trả lời. Vui lòng gửi lại câu hỏi.')
            status = 'insufficient_context' if result.insufficient_context else 'answered'
            answer = result.answer
            sources = [ChatSource(**hits[i-1].model_dump(), source_id=i) for i in result.source_ids]
        return ChatOut(workspace_id=workspace_id, question=data.question, status=status,
                       answer=answer, sources=sources, model=config.chat_model,
                       elapsed_ms=round((time.perf_counter()-started)*1000))
    except GenerationError as error:
        raise HTTPException(error.status_code, str(error)) from None
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, 'Không kiểm tra được nguồn trong database. Vui lòng thử lại.') from None
    finally:
        slot.release()
