import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, text, inspect
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db import Base
from app.main import create_app
from app.models import Conversation, Document, User

SECRET = "test-only-secret-at-least-32-characters"


@pytest.fixture
def client(monkeypatch, tmp_path):
    # Optional PostgreSQL run uses a unique schema, never application tables.
    url = os.environ.get("TEST_DATABASE_URL")
    schema = "test_private_ai_" + uuid.uuid4().hex
    if url:
        admin = create_engine(url)
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(url, connect_args={"options": f"-csearch_path={schema},public"})
    else:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        @event.listens_for(engine, "connect")
        def foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")
    # checkfirst=True sees same-named public tables through search_path and skips
    # creating our tables. Force creation in this NEW schema, then verify isolation.
    Base.metadata.create_all(engine, checkfirst=False)
    if url:
        assert set(Base.metadata.tables) <= set(inspect(engine).get_table_names(schema=schema))
    monkeypatch.setattr("app.main.make_engine", lambda _: engine)
    settings = Settings(database_url="postgresql+psycopg://unused", jwt_secret=SECRET, storage_dir=tmp_path / "storage", max_upload_bytes=1024 * 1024, max_pdf_pages=3, _env_file=None)
    try:
        with TestClient(create_app(settings)) as test_client:
            yield test_client
    finally:
        engine.dispose()
        if url:
            with admin.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()


def account(client, email="alice@example.com"):
    body = {"email": email, "password": "correct-password-123"}
    response = client.post("/auth/register", json=body)
    assert response.status_code == 201
    assert set(response.json()) == {"id", "email"}
    login = client.post("/auth/login", json=body)
    assert login.status_code == 200
    assert login.headers["cache-control"] == "no-store"
    return {"Authorization": "Bearer " + login.json()["access_token"]}


def test_register_hash_normalization_and_invalid_login(client):
    headers = account(client, "Alice@example.com")
    assert client.get("/auth/me", headers=headers).json()["email"] == "alice@example.com"
    duplicate = client.post("/auth/register", json={"email": "ALICE@example.com", "password": "different-password"})
    assert duplicate.status_code == 409
    with client.app.state.session_factory() as session:
        user = session.scalar(select(User))
        assert user.password_hash.startswith("$argon2id$")
        assert "correct-password" not in user.password_hash
    for email in ("alice@example.com", "unknown@example.com"):
        result = client.post("/auth/login", json={"email": email, "password": "wrong-password"})
        assert result.status_code == 401
        assert result.json()["detail"] == "Email hoặc mật khẩu không đúng."
    assert client.post("/auth/register", json={"email": "bad", "password": "short"}).status_code == 422


def test_missing_forged_expired_and_deleted_user_tokens(client):
    assert client.get("/workspaces").status_code == 401
    assert client.get("/workspaces", headers={"Authorization": "Bearer nonsense"}).status_code == 401
    headers = account(client)
    user_id = client.get("/auth/me", headers=headers).json()["id"]
    now = datetime.now(timezone.utc)
    claims = {"sub": user_id, "iat": now - timedelta(hours=2), "exp": now - timedelta(hours=1), "iss": "private-ai", "aud": "private-ai-web"}
    expired = jwt.encode(claims, SECRET, algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": "Bearer " + expired}).status_code == 401
    claims["exp"] = now + timedelta(minutes=10)
    forged = jwt.encode(claims, "wrong-secret-with-at-least-32-characters", algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": "Bearer " + forged}).status_code == 401
    with client.app.state.session_factory() as session:
        session.delete(session.get(User, uuid.UUID(user_id)))
        session.commit()
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_workspace_crud_and_owner_is_never_client_supplied(client):
    headers = account(client)
    assert client.get("/workspaces", headers=headers).json() == []
    assert client.post("/workspaces", headers=headers, json={"name": "   "}).status_code == 422
    assert client.post("/workspaces", headers=headers, json={"name": "test", "owner_id": str(uuid.uuid4())}).status_code == 422
    result = client.post("/workspaces", headers=headers, json={"name": "  My workspace  "})
    assert result.status_code == 201
    workspace = result.json()
    assert workspace["name"] == "My workspace"
    path = "/workspaces/" + workspace["id"]
    assert client.get(path, headers=headers).status_code == 200
    assert client.patch(path, headers=headers, json={"name": "Renamed"}).json()["name"] == "Renamed"
    assert client.get(path + "/documents", headers=headers).json() == []
    assert client.get(path + "/conversations", headers=headers).json() == []
    assert client.delete(path, headers=headers).status_code == 204
    assert client.get(path, headers=headers).status_code == 404


def test_two_accounts_cannot_read_rename_delete_or_list_foreign_data(client):
    alice = account(client)
    bob = account(client, "bob@example.com")
    a = client.post("/workspaces", headers=alice, json={"name": "Alice"}).json()
    b = client.post("/workspaces", headers=bob, json={"name": "Bob"}).json()
    path = "/workspaces/" + a["id"]
    assert [item["id"] for item in client.get("/workspaces", headers=bob).json()] == [b["id"]]
    for suffix in ("", "/documents", "/conversations"):
        assert client.get(path + suffix, headers=bob).status_code == 404
    assert client.patch(path, headers=bob, json={"name": "stolen"}).status_code == 404
    assert client.delete(path, headers=bob).status_code == 404
    assert client.get(path, headers=alice).json()["name"] == "Alice"


def test_document_conversation_lists_are_workspace_scoped_and_block_delete(client):
    headers = account(client)
    a = client.post("/workspaces", headers=headers, json={"name": "A"}).json()
    b = client.post("/workspaces", headers=headers, json={"name": "B"}).json()
    with client.app.state.session_factory() as session:
        session.add_all([Document(workspace_id=uuid.UUID(a["id"]), filename="private.pdf"), Conversation(workspace_id=uuid.UUID(a["id"]), title="Private chat")])
        session.commit()
    for suffix, field, expected in (("documents", "filename", "private.pdf"), ("conversations", "title", "Private chat")):
        data = client.get(f'/workspaces/{a["id"]}/{suffix}', headers=headers).json()
        assert len(data) == 1 and data[0][field] == expected
        assert client.get(f'/workspaces/{b["id"]}/{suffix}', headers=headers).json() == []
    assert client.delete('/workspaces/' + a["id"], headers=headers).status_code == 409


def test_cors_auth_preflight(client):
    response = client.options("/workspaces", headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,content-type"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_secret_is_required():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Settings(database_url="postgresql+psycopg://unused", jwt_secret="short", _env_file=None)
