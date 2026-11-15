"""Request-scoped dependencies: the only place where the API layer touches repositories.

Tests replace them with ``app.dependency_overrides`` (plan 002 DT-8).
"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from app.repositories.tax_rates import TaxRateRepository
from app.services.pricing import TaxRateSource


def get_db_session(request: Request) -> Iterator[Session]:
    """One database session per request, closed when the response is sent."""
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    with session_factory() as session:
        yield session


def get_rate_source(session: Annotated[Session, Depends(get_db_session)]) -> TaxRateSource:
    return TaxRateRepository(session)
