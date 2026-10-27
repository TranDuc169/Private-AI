"""Workspace-authorized history and live source lookup."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Conversation, Message, Document, DocumentChunk, Workspace
from app.routes import owned_workspace
from app.security import get_session

router = APIRouter(prefix='/workspaces/{workspace_id}', tags=['History and sources'])


def get_conversation(session, workspace_id, conversation_id):
    conversation = session.scalar(select(Conversation).where(
        Conversation.id == conversation_id, Conversation.workspace_id == workspace_id))
    if conversation is None:
        raise HTTPException(404, 'Không tìm thấy hội thoại trong workspace này.')
    return conversation


@router.get('/conversations/{conversation_id}')
def read_conversation(conversation_id: UUID, response: Response,
                      workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    response.headers['Cache-Control'] = 'no-store'
    conversation = get_conversation(session, workspace.id, conversation_id)
    messages = session.scalars(select(Message).where(Message.conversation_id == conversation.id)
        .order_by(Message.position.asc().nulls_first(), Message.created_at, Message.id)).all()
    return dict(id=conversation.id, title=conversation.title, revision=conversation.revision,
                workspace_id=workspace.id, messages=[dict(id=m.id, role=m.role, content=m.content,
                    created_at=m.created_at, result=m.payload) for m in messages])


@router.get('/sources/{chunk_id}')
def read_source(chunk_id: UUID, response: Response, workspace: Workspace = Depends(owned_workspace),
                session: Session = Depends(get_session)):
    response.headers['Cache-Control'] = 'no-store'
    row = session.execute(select(DocumentChunk, Document.filename).join(Document).where(
        DocumentChunk.id == chunk_id, Document.workspace_id == workspace.id,
        Document.status == 'ready', Document.index_status == 'ready')).first()
    if row is None:
        raise HTTPException(404, 'Đoạn nguồn không còn sẵn sàng hoặc đã bị xóa/tạo vector lại.')
    chunk, filename = row
    return dict(chunk_id=chunk.id, document_id=chunk.document_id, filename=filename,
                page_number=chunk.page_number, text=chunk.text, chunk_index=chunk.chunk_index)
