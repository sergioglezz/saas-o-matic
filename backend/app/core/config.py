"""Runtime settings read from environment variables, with no extra dependency (constitution 1)."""

import os

DEFAULT_DATABASE_URL = "sqlite:///./saas_o_matic.db"
DEFAULT_FRONTEND_ORIGIN = "http://localhost:4200"


def get_database_url() -> str:
    """Database URL from ``DATABASE_URL``, or a local SQLite file in the current directory.

    Read on every call instead of at import time so tests can change it per test.
    """
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_frontend_origin() -> str:
    """The only browser origin allowed by CORS (spec 002 RF-9), from ``FRONTEND_ORIGIN``."""
    return os.environ.get("FRONTEND_ORIGIN", DEFAULT_FRONTEND_ORIGIN)
