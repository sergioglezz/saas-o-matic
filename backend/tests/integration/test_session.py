"""Database settings and connections: 00-spec-first sections 5 and 8.5, plan section 2."""

from pathlib import Path

import pytest
from sqlalchemy import make_url, text

from app.core.config import DEFAULT_DATABASE_URL, get_database_url
from app.db.session import create_db_engine, create_session_factory


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_database_url_defaults_to_local_sqlite_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert get_database_url() == DEFAULT_DATABASE_URL == "sqlite:///./saas_o_matic.db"


def test_database_url_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./other.db")

    assert get_database_url() == "sqlite:///./other.db"


def test_engine_uses_the_configured_url_by_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    url = _sqlite_url(tmp_path / "configured.db")
    monkeypatch.setenv("DATABASE_URL", url)

    engine = create_db_engine()
    try:
        # Compare URL objects: rendering escapes "C:" as "C%3A" on Windows.
        assert engine.url == make_url(url)
    finally:
        engine.dispose()


def test_every_new_connection_enables_foreign_keys(tmp_path: Path) -> None:
    """00-spec-first section 8.5: PRAGMA foreign_keys=ON on every connection."""
    engine = create_db_engine(_sqlite_url(tmp_path / "fk.db"))
    try:
        for _ in range(2):
            with engine.connect() as connection:
                assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
            engine.dispose()  # the next iteration opens a brand-new DBAPI connection
    finally:
        engine.dispose()


def test_sessions_also_have_foreign_keys_enabled(tmp_path: Path) -> None:
    engine = create_db_engine(_sqlite_url(tmp_path / "session.db"))
    try:
        with create_session_factory(engine)() as session:
            assert session.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    finally:
        engine.dispose()
