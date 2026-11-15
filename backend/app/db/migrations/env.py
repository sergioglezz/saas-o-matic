"""Alembic environment: applies the migrations in ``versions/`` to the configured database."""

from logging.config import fileConfig

from alembic import context

from app.core.config import get_database_url
from app.db.models import Base
from app.db.session import create_db_engine

config = context.config
if config.config_file_name is not None:
    # Keep loggers created before this point (for example pytest's) working.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _database_url() -> str:
    # Tests pass their own URL through the Alembic config; otherwise use the app setting.
    return config.get_main_option("sqlalchemy.url") or get_database_url()


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_db_engine(_database_url())
    try:
        with engine.connect() as connection:
            # Batch mode lets future migrations alter tables, which SQLite cannot do in place.
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
