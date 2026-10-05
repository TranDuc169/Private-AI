from alembic import context
from app.config import Settings
from app.db import Base, make_engine
from app import models  # noqa: F401 -- register every table with Base.metadata

target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(
        url=Settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(Settings().database_url)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata, compare_type=True,
                              version_table_schema=context.config.attributes.get("version_table_schema"))
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()
