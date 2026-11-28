"""Read-only verification against the real configured PostgreSQL database."""
from sqlalchemy import inspect, text
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.db import Base
from app import models

from app.config import Settings
from app.db import make_engine

engine = make_engine(Settings().database_url)
try:
    with engine.connect() as connection:
        print("SELECT 1:", connection.execute(text("SELECT 1")).scalar_one())
        print("Database:", connection.execute(text("SELECT current_database()")).scalar_one())
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        config = Config(str(Path(__file__).resolve().parent / 'alembic.ini'))
        heads = ScriptDirectory.from_config(config).get_heads()
        if [revision] != heads:
            raise RuntimeError(f'Migration {revision} does not match repository heads {heads}')
        expected = set(Base.metadata.tables)
        actual = set(inspect(connection).get_table_names())
        assert expected <= actual, f"Missing tables: {expected - actual}"
        print("pgvector:", connection.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")).scalar_one())
        print("Migration:", revision)
        print("Tables:", ", ".join(sorted(expected)))
        print("PASS: PostgreSQL query and current repository migration verified.")
finally:
    engine.dispose()
