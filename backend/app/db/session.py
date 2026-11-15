"""Database engine and session factories: the only place that knows how to connect to SQLite."""

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from app.core.config import get_database_url


def create_db_engine(url: str | None = None) -> Engine:
    """Engine for ``url`` (by default the configured one) with foreign keys always on."""
    engine = create_engine(url if url is not None else get_database_url())
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def _enable_foreign_keys(dbapi_connection: DBAPIConnection, _record: ConnectionPoolEntry) -> None:
    # SQLite ignores foreign keys unless each connection turns them on (00-spec-first 8.5).
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
