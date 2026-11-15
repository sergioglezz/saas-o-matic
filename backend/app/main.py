"""FastAPI application: `uvicorn app.main:app` (AGENTS.md). Built by a factory so tests can
point it at a temporary database (plan 002 DT-8)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.customers import router as customers_router
from app.api.error_mapping import register_domain_error_handlers
from app.api.pricing import restore_openapi_examples
from app.api.pricing import router as pricing_router
from app.core.config import get_frontend_origin
from app.core.errors import register_error_handlers
from app.db.session import create_db_engine, create_session_factory


def create_app(database_url: str | None = None, frontend_origin: str | None = None) -> FastAPI:
    """Application bound to ``database_url`` and ``frontend_origin`` (defaults: configured)."""
    engine = create_db_engine(database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        engine.dispose()

    app = FastAPI(title="SaaS-O-Matic API", lifespan=lifespan)
    # "/pricing/quote/" is an unknown route (404), not a redirect to "/pricing/quote" (CA-6.7).
    app.router.redirect_slashes = False
    app.state.session_factory = create_session_factory(engine)
    # Only the dashboard may call the API from a browser (RF-9, plan 002 DT-7). GET is listed
    # too: a simple GET needs no permission, but its preflight would be refused (003 CA-8.2).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_origin or get_frontend_origin()],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    register_error_handlers(app)
    register_domain_error_handlers(app)
    app.include_router(pricing_router)
    app.include_router(customers_router)

    generate_openapi = app.openapi

    def openapi() -> dict[str, Any]:
        return restore_openapi_examples(generate_openapi())

    app.openapi = openapi  # type: ignore[method-assign]  # FastAPI's documented customization
    return app


app = create_app()
