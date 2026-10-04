from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.main import create_app


def make_app():
    return create_app(Settings(database_url="postgresql+psycopg://unused:unused@localhost/unused", jwt_secret="test-only-secret-at-least-32-characters"))


def test_health_executes_database_query():
    with TestClient(make_app()) as client:
        engine = MagicMock()
        connection = engine.connect.return_value.__enter__.return_value
        connection.execute.return_value.scalar_one.return_value = 1
        client.app.state.engine = engine
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "up"}
        assert str(connection.execute.call_args.args[0]) == "SELECT 1"


def test_database_failure_returns_503_without_secrets():
    with TestClient(make_app()) as client:
        engine = MagicMock()
        engine.connect.side_effect = OperationalError("SELECT 1", {}, Exception("SECRET_PASSWORD"))
        client.app.state.engine = engine
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json() == {"status": "degraded", "database": "down"}
        assert "SECRET_PASSWORD" not in response.text


def test_cors_allows_frontend_but_not_unknown_origins():
    with TestClient(make_app()) as client:
        headers = {"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "GET"}
        assert client.options("/health", headers=headers).headers["access-control-allow-origin"] == headers["Origin"]
        headers["Origin"] = "https://unknown.example"
        assert "access-control-allow-origin" not in client.options("/health", headers=headers).headers
