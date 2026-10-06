"""Exact cosine retrieval within the authenticated user's selected workspace."""
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.embedding import EmbeddingError, embed_batch
from app.models import Document, DocumentChunk, Workspace
from app.routes import owned_workspace
from app.schemas import RetrievalInput, RetrievalOut, RetrievalHit
from app.security import get_session

router = APIRouter(prefix='/workspaces/{workspace_id}', tags=['Retrieval'])


def candidate_filters(workspace_id, owner_id, model):
    return (
        Document.workspace_id == workspace_id,
        Workspace.owner_id == owner_id,
        Document.status == 'ready',
        Document.index_status == 'ready',
        Document.embedding_model == model,
        DocumentChunk.embedding_model == model,
    )


def search_statement(workspace_id, owner_id, model, vector, top_k):
    distance = DocumentChunk.embedding.cosine_distance(vector)
    # WHERE restricts candidates BEFORE ORDER BY/LIMIT. Never fetch global Top-K
    # and remove foreign documents afterwards: that can miss valid local hits.
    return (select(
        DocumentChunk.id.label('chunk_id'), Document.id.label('document_id'),
        Document.filename, DocumentChunk.page_number, DocumentChunk.chunk_index,
        DocumentChunk.start_char, DocumentChunk.end_char, DocumentChunk.text,
        distance.label('distance'),
    ).join(Document, Document.id == DocumentChunk.document_id)
      .join(Workspace, Workspace.id == Document.workspace_id)
      .where(*candidate_filters(workspace_id, owner_id, model))
      .order_by(distance, Document.id, DocumentChunk.chunk_index).limit(top_k))


@router.post('/retrieve', response_model=RetrievalOut)
def retrieve(data: RetrievalInput, request: Request, response: Response,
             workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    response.headers['Cache-Control'] = 'no-store'
    started = time.perf_counter()
    config = request.app.state.settings
    workspace_id, owner_id = workspace.id, workspace.owner_id
    results = []
    try:
        available = session.scalar(select(DocumentChunk.id).join(Document).join(Workspace)
            .where(*candidate_filters(workspace_id, owner_id, config.embedding_model)).limit(1))
        session.rollback()  # Do not hold a database connection while Ollama runs.
        if available is not None:
            if session.get_bind().dialect.name != 'postgresql':
                raise HTTPException(503, 'Truy xuất cần PostgreSQL với pgvector.')
            vector = embed_batch(config, [data.question])[0]
            rows = session.execute(search_statement(workspace_id, owner_id, config.embedding_model, vector, data.top_k)).mappings()
            for row in rows:
                values = dict(row)
                distance = values.pop('distance')
                # Numerical roundoff may put cosine a fraction beyond [-1, 1].
                values['score'] = round(max(-1.0, min(1.0, 1.0 - distance)), 6)
                results.append(RetrievalHit(**values))
    except EmbeddingError as error:
        raise HTTPException(503, str(error)) from None
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, 'Không truy xuất được database. Kiểm tra PostgreSQL/pgvector rồi thử lại.') from None
    return RetrievalOut(workspace_id=workspace_id, question=data.question, top_k=data.top_k,
        embedding_model=config.embedding_model, elapsed_ms=round((time.perf_counter()-started)*1000), results=results)
