"""Database engine and session factories: the only place that knows how to connect to SQLite."""

import sqlite3

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from app.core.config import get_database_url


def create_db_engine(url: str | None = None) -> Engine:
    """Engine for ``url`` (by default the configured one) with foreign keys always on."""
    engine = create_engine(url if url is not None else get_database_url())
    event.listen(engine, "connect", _configure_connection)
    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def _configure_connection(dbapi_connection: DBAPIConnection, _record: ConnectionPoolEntry) -> None:
    # SQLite ignores foreign keys unless each connection turns them on (00-spec-first 8.5).
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    # SQLite's lower() only knows ASCII, so "COMPAÑÍA" would never match "compañía". The
    # customer search and its ordering use Python's casefold instead (spec 003 CA-5.3).
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.create_function("casefold", 1, _casefold, deterministic=True)


def _casefold(value: str | None) -> str | None:
    return value.casefold() if value is not None else None
