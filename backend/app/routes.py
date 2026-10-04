from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Conversation, Document, User, Workspace
from app.schemas import Credentials, UserOut, TokenOut, WorkspaceInput, WorkspaceOut, DocumentOut, ConversationOut
from app.security import current_user, dummy_hash, get_session, issue_token, password_hash

router = APIRouter()


@router.post("/auth/register", response_model=UserOut, status_code=201)
def register(data: Credentials, session: Session = Depends(get_session)):
    user = User(email=str(data.email), password_hash=password_hash.hash(data.password))
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Email đã được sử dụng.")
    return user


@router.post("/auth/login", response_model=TokenOut)
def login(data: Credentials, request: Request, response: Response, session: Session = Depends(get_session)):
    user = session.scalar(select(User).where(User.email == str(data.email)))
    valid = password_hash.verify(data.password, user.password_hash if user else dummy_hash)
    if user is None or not valid:
        raise HTTPException(401, "Email hoặc mật khẩu không đúng.", headers={"WWW-Authenticate": "Bearer"})
    response.headers["Cache-Control"] = "no-store"
    config = request.app.state.settings
    return TokenOut(access_token=issue_token(user, config), expires_in=config.access_token_minutes * 60, user=UserOut.model_validate(user))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


def owned_workspace(workspace_id: UUID, user: User = Depends(current_user), session: Session = Depends(get_session)):
    workspace = session.scalar(select(Workspace).where(Workspace.id == workspace_id, Workspace.owner_id == user.id))
    if workspace is None:
        # Same response for missing and foreign IDs: do not reveal other users' data.
        raise HTTPException(404, "Không tìm thấy workspace.")
    return workspace


@router.get("/workspaces", response_model=list[WorkspaceOut])
def list_workspaces(user: User = Depends(current_user), session: Session = Depends(get_session)):
    return session.scalars(select(Workspace).where(Workspace.owner_id == user.id).order_by(Workspace.created_at, Workspace.id)).all()


@router.post("/workspaces", response_model=WorkspaceOut, status_code=201)
def create_workspace(data: WorkspaceInput, user: User = Depends(current_user), session: Session = Depends(get_session)):
    workspace = Workspace(name=data.name, owner_id=user.id)
    session.add(workspace)
    session.commit()
    return workspace


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceOut)
def read_workspace(workspace: Workspace = Depends(owned_workspace)):
    return workspace


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceOut)
def rename_workspace(data: WorkspaceInput, workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    workspace.name = data.name
    session.commit()
    return workspace


@router.delete("/workspaces/{workspace_id}", status_code=204)
def delete_workspace(workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    for model in (Document, Conversation):
        if session.scalar(select(func.count()).select_from(model).where(model.workspace_id == workspace.id)):
            raise HTTPException(409, "Workspace còn tài liệu hoặc hội thoại, chưa thể xóa.")
    session.delete(workspace)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Workspace còn dữ liệu, chưa thể xóa.")


@router.get("/workspaces/{workspace_id}/documents", response_model=list[DocumentOut])
def list_documents(workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    return session.scalars(select(Document).where(Document.workspace_id == workspace.id).order_by(Document.created_at, Document.id)).all()


@router.get("/workspaces/{workspace_id}/conversations", response_model=list[ConversationOut])
def list_conversations(workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    return session.scalars(select(Conversation).where(Conversation.workspace_id == workspace.id).order_by(Conversation.created_at, Conversation.id)).all()
