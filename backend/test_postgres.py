"""Run auth/workspace tests in isolated temporary PostgreSQL schemas."""
import os
import subprocess
import sys
from pathlib import Path

from app.config import Settings
from sqlalchemy import create_engine, text

if __name__ == "__main__":
    engine = create_engine(Settings().database_url)
    with engine.connect() as connection:
        if not connection.scalar(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')")):
            raise SystemExit('Chua co pgvector. Chay Docker image moi va alembic upgrade head truoc.')
    engine.dispose()
    environment = dict(os.environ, TEST_DATABASE_URL=Settings().database_url)
    raise SystemExit(subprocess.call(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_auth_workspaces.py", "tests/test_documents.py", "tests/test_pdf_migration.py", "tests/test_indexing.py", *sys.argv[1:]],
        cwd=Path(__file__).resolve().parent, env=environment,
    ))
