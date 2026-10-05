"""Synchronous indexing with a persisted, recoverable claim and atomic publication."""
import logging
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, Query, Request, Response
from sqlalchemy import delete, or_, select, update
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import Session

from app.documents import router, get_document, pdf_path
from app.embedding import EmbeddingError, chunk_pages, embed_batch
from app.models import Document, DocumentChunk, DocumentPage, Workspace
from app.routes import owned_workspace
from app.schemas import ChunkOut, DocumentOut
from app.security import get_session

LEASE_SECONDS = 900
JOB_SECONDS = 600


def utcnow():
    return datetime.now(timezone.utc)


def active_job(document):
    started = document.index_started_at
    if started is not None and started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return document.index_status == 'processing' and started is not None and started > utcnow() - timedelta(seconds=LEASE_SECONDS)


@router.post('/{document_id}/index', response_model=DocumentOut)
def index_document(document_id: UUID, request: Request, workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    document = get_document(document_id, workspace, session)
    if document.status != 'ready':
        raise HTTPException(409, 'Cần trích xuất văn bản thành công trước khi tạo vector.')
    if document.index_status == 'ready':
        return document  # Repeat clicks do not generate duplicates or call Ollama again.
    job_id = uuid4()
    claimed = session.execute(update(Document).where(
        Document.id == document.id, Document.status == 'ready',
        or_(Document.index_status.in_(['pending', 'failed']),
            (Document.index_status == 'processing') & (Document.index_started_at < utcnow() - timedelta(seconds=LEASE_SECONDS))),
    ).values(index_status='processing', index_job_id=job_id, index_started_at=utcnow(), index_error=None).execution_options(synchronize_session=False))
    if claimed.rowcount != 1:
        session.rollback()
        raise HTTPException(409, 'Tài liệu đang tạo vector. Nếu server đã tắt giữa chừng, thử lại sau 15 phút.')
    session.commit()  # Polling sees processing while the slow model call runs.
    config = request.app.state.settings
    deadline = time.monotonic() + JOB_SECONDS
    failure = None
    chunks = []
    try:
        pages = session.scalars(select(DocumentPage).where(DocumentPage.document_id == document_id).order_by(DocumentPage.page_number)).all()
        chunks = chunk_pages(pages, config.max_document_chunks)
        session.rollback()  # Release DB connection during model work; pages/chunks are now in memory.
        for offset in range(0, len(chunks), config.embedding_batch_size):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EmbeddingError('Tạo vector quá 10 phút. Hãy chia nhỏ PDF rồi thử lại.')
            batch = chunks[offset:offset + config.embedding_batch_size]
            vectors = embed_batch(config, [chunk['text'] for chunk in batch], timeout=min(remaining, config.embedding_timeout_seconds))
            for chunk, vector in zip(batch, vectors, strict=True):
                chunk['embedding'] = vector
        if time.monotonic() > deadline:
            raise EmbeddingError('Tạo vector quá 10 phút. Hãy chia nhỏ PDF rồi thử lại.')
    except EmbeddingError as error:
        failure = str(error)
    except Exception:
        logging.getLogger(__name__).exception('Indexing failed for document %s', document_id)
        failure = 'Không hoàn tất tạo vector. Vui lòng thử lại.'
    try:
        session.rollback()
        document = session.scalar(select(Document).where(Document.id == document_id).with_for_update())
        if document is None or document.index_job_id != job_id:
            session.rollback()
            raise HTTPException(409, 'Lượt xử lý đã hết hiệu lực; hãy làm mới danh sách.')
        session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        document.index_error = failure
        document.index_status = 'failed' if failure else 'ready'
        document.index_job_id = None
        document.chunk_count = 0 if failure else len(chunks)
        document.indexed_at = None if failure else utcnow()
        document.embedding_model = None if failure else config.embedding_model
        if not failure:
            session.add_all(DocumentChunk(document_id=document_id, embedding_model=config.embedding_model, **chunk) for chunk in chunks)
        session.commit()  # All vectors and ready state become visible together, never half a document.
        return document
    except SQLAlchemyError:
        session.rollback()
        # Release this claim when DB recovers; otherwise its lease still enables retry.
        try:
            session.execute(update(Document).where(Document.id == document_id, Document.index_job_id == job_id).values(
                index_status='failed', index_job_id=None, index_error='Không lưu được vector vào database. Vui lòng thử lại.'))
            session.commit()
        except SQLAlchemyError:
            session.rollback()
        raise HTTPException(503, 'Không lưu được vector vào database. Làm mới danh sách rồi thử lại.') from None


@router.get('/{document_id}/chunks', response_model=list[ChunkOut])
def read_chunks(document_id: UUID, offset: int = Query(0, ge=0), limit: int = Query(5, ge=1, le=20), workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    document = get_document(document_id, workspace, session)
    if document.index_status != 'ready':
        raise HTTPException(409, 'Tài liệu chưa tạo vector thành công.')
    return session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).offset(offset).limit(limit)).all()


@router.delete('/{document_id}', status_code=204)
def delete_document(document_id: UUID, request: Request, workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    # Lock also serializes with PDF extraction and job claims.
    try:
        document = session.scalar(select(Document).where(Document.id == document_id, Document.workspace_id == workspace.id).with_for_update(nowait=True))
    except OperationalError as error:
        session.rollback()
        if getattr(error.orig, 'sqlstate', None) == '55P03':
            raise HTTPException(409, 'Tài liệu đang được xử lý. Vui lòng thử lại sau.') from None
        raise HTTPException(503, 'Không truy cập được database. Vui lòng thử lại.') from None
    if document is None:
        raise HTTPException(404, 'Không tìm thấy tài liệu.')
    if active_job(document):
        raise HTTPException(409, 'Đang tạo vector; đợi hoàn tất trước khi xóa. Nếu server dừng, thử lại sau 15 phút.')
    target = pdf_path(request.app.state.settings, workspace.id, document_id)
    # Stage file as a tombstone first. A DB failure restores it; a crash leaves a recoverable .deleting file.
    tombstone = target.with_suffix('.pdf.deleting')
    moved = False
    try:
        if target.exists():
            target.replace(tombstone)
            moved = True
        session.delete(document)  # FK CASCADE removes page text AND vectors.
        session.commit()
    except (OSError, SQLAlchemyError):
        session.rollback()
        if moved:
            try:
                tombstone.replace(target)
            except OSError:
                logging.getLogger(__name__).exception('Restore PDF tombstone failed %s', document_id)
        raise HTTPException(503, 'Chưa xóa được tài liệu. Vui lòng thử lại.') from None
    try:
        tombstone.unlink(missing_ok=True)
    except OSError:
        logging.getLogger(__name__).exception('Cannot remove PDF tombstone %s', document_id)
        # Metadata/vectors are gone. Return an honest storage-cleanup warning, not a false 204.
        raise HTTPException(503, 'Đã xóa metadata và vector; file tạm chưa dọn được. Cần kiểm tra thư mục storage.') from None
    return Response(status_code=204)
