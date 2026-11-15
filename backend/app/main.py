"""FastAPI application: `uvicorn app.main:app` (AGENTS.md). Built by a factory so tests can
point it at a temporary database (plan 002 DT-8)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.errors import register_error_handlers
from app.db.session import create_db_engine, create_session_factory


def create_app(database_url: str | None = None) -> FastAPI:
    """Application bound to ``database_url`` (by default the configured one)."""
    engine = create_db_engine(database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        engine.dispose()

    app = FastAPI(title="SaaS-O-Matic API", lifespan=lifespan)
    # "/pricing/quote/" is an unknown route (404), not a redirect to "/pricing/quote" (CA-6.7).
    app.router.redirect_slashes = False
    app.state.session_factory = create_session_factory(engine)
    register_error_handlers(app)
    return app


app = create_app()
