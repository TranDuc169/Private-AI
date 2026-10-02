"""Read-only verification against the real configured PostgreSQL database."""
from sqlalchemy import inspect, text

from app.config import Settings
from app.db import make_engine

engine = make_engine(Settings().database_url)
try:
    with engine.connect() as connection:
        print("SELECT 1:", connection.execute(text("SELECT 1")).scalar_one())
        print("Database:", connection.execute(text("SELECT current_database()")).scalar_one())
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert revision == "0001_initial", f"Unexpected migration: {revision}"
        expected = {"users", "workspaces", "documents", "conversations", "messages"}
        actual = set(inspect(connection).get_table_names())
        assert expected <= actual, f"Missing tables: {expected - actual}"
        print("Migration:", revision)
        print("Tables:", ", ".join(sorted(expected)))
        print("PASS: PostgreSQL query and initial migration verified.")
finally:
    engine.dispose()
