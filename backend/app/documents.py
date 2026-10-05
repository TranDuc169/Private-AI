import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Document, DocumentPage, Workspace
from app.routes import owned_workspace
from app.schemas import DocumentOut, PageOut
from app.security import get_session

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["Documents"])


def pdf_path(config, workspace_id, document_id):
    # Only server-validated UUIDs form paths. Never use the submitted filename.
    return config.storage_dir.resolve() / str(workspace_id) / f"{document_id}.pdf"


def get_document(document_id: UUID, workspace: Workspace, session: Session):
    item = session.scalar(select(Document).where(Document.id == document_id, Document.workspace_id == workspace.id))
    if item is None:
        raise HTTPException(404, "Không tìm thấy tài liệu.")
    return item


@router.post("", response_model=DocumentOut, status_code=201)
def upload_pdf(request: Request, file: UploadFile, workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    config = request.app.state.settings
    name = re.split(r"[/\\]", file.filename or "")[-1].strip()
    if not name.lower().endswith(".pdf") or len(name) > 255 or any(ord(c) < 32 for c in name):
        raise HTTPException(415, "Chọn file có đuôi .pdf và tên không quá 255 ký tự.")
    document_id = uuid4()
    target = pdf_path(config, workspace.id, document_id)
    size = 0
    saved = False
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            first = True
            while chunk := file.file.read(64 * 1024):
                if first and not chunk.startswith(b"%PDF-"):
                    raise HTTPException(415, "Nội dung file không có định dạng PDF.")
                first = False
                size += len(chunk)
                if size > config.max_upload_bytes:
                    raise HTTPException(413, f"File vượt giới hạn {config.max_upload_bytes // (1024 * 1024)} MB.")
                output.write(chunk)
        if size == 0:
            raise HTTPException(422, "File rỗng, hãy chọn PDF có nội dung.")
        document = Document(id=document_id, workspace_id=workspace.id, filename=name, size_bytes=size, status="uploaded")
        session.add(document)
        session.commit()
        saved = True
        return document
    except OSError:
        session.rollback()
        raise HTTPException(503, "Không lưu được file PDF. Kiểm tra ổ đĩa và quyền thư mục lưu trữ.")
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Workspace đã thay đổi. Hãy làm mới danh sách rồi thử lại.")
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, "Không lưu được thông tin tài liệu vào database. Vui lòng thử lại.")
    finally:
        file.file.close()
        if not saved:
            try:
                target.unlink(missing_ok=True)
            except OSError:
                logging.getLogger(__name__).exception("Cannot remove incomplete PDF %s", document_id)


@router.get("/{document_id}", response_model=DocumentOut)
def read_document(document_id: UUID, workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    return get_document(document_id, workspace, session)


@router.post("/{document_id}/process", response_model=DocumentOut)
def process_document(document_id: UUID, request: Request, workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    # Hold a row lock during extraction. A crash rolls back, leaving retry possible.
    try:
        document = session.scalar(select(Document).where(Document.id == document_id, Document.workspace_id == workspace.id).with_for_update(nowait=True))
    except OperationalError as error:
        session.rollback()
        if getattr(error.orig, "sqlstate", None) == "55P03":
            raise HTTPException(409, "Tài liệu đang được xử lý. Vui lòng thử lại sau.")
        raise HTTPException(503, "Không truy cập được database. Vui lòng thử lại.")
    if document is None:
        raise HTTPException(404, "Không tìm thấy tài liệu.")
    if document.status == "ready":
        return document
    config = request.app.state.settings
    target = pdf_path(config, workspace.id, document.id)
    if not target.is_file():
        result = {"error": "Không tìm thấy file gốc. Vui lòng tải lại tài liệu."}
    else:
        try:
            completed = subprocess.run(
                [sys.executable, str(Path(__file__).with_name("pdf_worker.py")), str(target), str(config.max_pdf_pages), str(config.max_pdf_characters)],
                capture_output=True, text=True, encoding="utf-8", timeout=config.pdf_timeout_seconds,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            result = json.loads(completed.stdout) if completed.returncode == 0 else {"error": "Tiến trình đọc PDF gặp lỗi. Vui lòng thử lại."}
        except subprocess.TimeoutExpired:
            result = {"error": "Đọc PDF quá thời gian cho phép. Hãy chia nhỏ file hoặc thử PDF khác."}
        except (OSError, ValueError):
            result = {"error": "Không chạy được tiến trình đọc PDF. Vui lòng thử lại."}
    session.execute(delete(DocumentPage).where(DocumentPage.document_id == document.id))
    document.page_count = result.get("page_count")
    document.error_message = result.get("error")
    document.status = "failed" if document.error_message else "ready"
    if document.status == "ready":
        session.add_all(DocumentPage(document_id=document.id, **page) for page in result["pages"])
    session.commit()
    return document


@router.get("/{document_id}/pages", response_model=list[PageOut])
def read_pages(document_id: UUID, offset: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=20), workspace: Workspace = Depends(owned_workspace), session: Session = Depends(get_session)):
    document = get_document(document_id, workspace, session)
    if document.status != "ready":
        raise HTTPException(409, "Tài liệu chưa trích xuất văn bản thành công.")
    return session.scalars(select(DocumentPage).where(DocumentPage.document_id == document.id).order_by(DocumentPage.page_number).offset(offset).limit(limit)).all()
