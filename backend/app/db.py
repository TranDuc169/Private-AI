from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str):
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_timeout=3,
        connect_args={"connect_timeout": 3, "options": "-c statement_timeout=3000"},
    )


def make_session_factory(engine):
    # For future workspace/document APIs; health uses a short read-only connection.
    return sessionmaker(bind=engine, expire_on_commit=False)
