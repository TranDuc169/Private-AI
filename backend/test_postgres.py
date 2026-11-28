"""Run auth/workspace tests in isolated temporary PostgreSQL schemas."""
import os
import sys
from pathlib import Path
import pytest

from app.config import Settings
from sqlalchemy import create_engine, text

if __name__ == "__main__":
    engine = create_engine(Settings().database_url)
    with engine.connect() as connection:
        if not connection.scalar(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')")):
            raise SystemExit('Chua co pgvector. Chay Docker image moi va alembic upgrade head truoc.')
    engine.dispose()
    os.environ['TEST_DATABASE_URL'] = Settings().database_url
    os.chdir(Path(__file__).resolve().parent)
    raise SystemExit(pytest.main(['-q', '-p', 'no:cacheprovider', 'tests', *sys.argv[1:]]))
