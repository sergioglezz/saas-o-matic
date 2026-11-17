"""Request-scoped dependencies: the only place where the API layer touches repositories.

Tests replace them with ``app.dependency_overrides`` (plan 002 DT-8).
"""

from collections.abc import Iterator
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from app.core.clock import utc_now
from app.repositories.customers import CustomerRepository
from app.repositories.simulations import SimulationRepository
from app.repositories.tax_rates import TaxRateRepository
from app.services.customers import CustomerHistory, CustomerStore
from app.services.pricing import TaxRateSource
from app.services.simulations import SimulationStore


def get_db_session(request: Request) -> Iterator[Session]:
    """One database session per request, closed when the response is sent."""
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    with session_factory() as session:
        yield session


def get_rate_source(session: Annotated[Session, Depends(get_db_session)]) -> TaxRateSource:
    return TaxRateRepository(session)


def get_customer_store(session: Annotated[Session, Depends(get_db_session)]) -> CustomerStore:
    return CustomerRepository(session)


def get_simulation_store(session: Annotated[Session, Depends(get_db_session)]) -> SimulationStore:
    return SimulationRepository(session)


def get_customer_history(session: Annotated[Session, Depends(get_db_session)]) -> CustomerHistory:
    """The simulations of a customer, on the same session as its store (spec 007 D-3)."""
    return SimulationRepository(session)


def get_now() -> datetime:
    """The instant of the request; tests freeze it to compare exact responses."""
    return utc_now()
