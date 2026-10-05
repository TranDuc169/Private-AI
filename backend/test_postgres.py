"""Run auth/workspace tests in isolated temporary PostgreSQL schemas."""
import os
import subprocess
import sys
from pathlib import Path

from app.config import Settings

if __name__ == "__main__":
    environment = dict(os.environ, TEST_DATABASE_URL=Settings().database_url)
    raise SystemExit(subprocess.call(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_auth_workspaces.py", "tests/test_documents.py", "tests/test_pdf_migration.py"],
        cwd=Path(__file__).resolve().parent, env=environment,
    ))
