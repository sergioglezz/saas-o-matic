"""Deleting a customer with its history (level D), spec 007: cases BR-8 and BR-11.

Covers CA-1.1, CA-1.2, CA-1.4 and CA-1.8 at the service and repository level. Task T-01.
"""

import dataclasses

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import create_session_factory
from app.domain.customers import NewCustomer
from app.domain.errors import CustomerNotFoundError
from app.domain.pricing import build_quote
from app.domain.simulations import NewSimulation
from app.repositories.customers import CustomerRepository
from app.repositories.simulations import SimulationRepository
from app.services.customers import delete_customer

AT = "2026-11-16T10:00:00Z"
ACME = NewCustomer(
    company_name="Acme Telecom S.L.",
    tax_id="B12345674",
    contact_email="compras@acme.example",
    country="ES",
    plan="business",
)
LUSITANIA = dataclasses.replace(ACME, company_name="Lusitânia Cloud Lda", tax_id="PT123456789")


def _count(session: Session, sql: str) -> int:
    count: int = session.execute(text(sql)).scalar_one()
    return count


def _simulate(simulations: SimulationRepository, customer_id: int, users: int) -> None:
    new = NewSimulation(
        customer_id=customer_id, active_users=users, storage_gb=0, api_calls_per_month=0
    )
    simulations.add(new, build_quote(users, 2100), AT)


@pytest.fixture
def stores(session: Session) -> tuple[CustomerRepository, SimulationRepository]:
    """Acme (id 1) with 2 simulations and Lusitânia (id 2) with 1."""
    customers = CustomerRepository(session)
    simulations = SimulationRepository(session)
    customers.add(ACME, AT)
    customers.add(LUSITANIA, AT)
    _simulate(simulations, 1, 15)
    _simulate(simulations, 1, 60)
    _simulate(simulations, 2, 5)
    return customers, simulations


def test_deleting_removes_the_customer_and_its_whole_history(
    stores: tuple[CustomerRepository, SimulationRepository], session: Session
) -> None:
    """CA-1.1 and CA-1.4: Acme, its 2 simulations and their 6 tiers go; Lusitânia stays."""
    customers, simulations = stores

    removed = delete_customer(1, customers, simulations)

    assert removed == 2
    assert customers.get(1) is None
    assert _count(session, "SELECT count(*) FROM simulations WHERE customer_id = 1") == 0
    assert _count(session, "SELECT count(*) FROM simulation_tiers") == 3
    assert customers.get(2) is not None
    assert _count(session, "SELECT count(*) FROM simulations WHERE customer_id = 2") == 1


def test_a_customer_without_history_is_deleted_too(session: Session) -> None:
    """CA-1.1: nothing to remove from the history."""
    customers, simulations = CustomerRepository(session), SimulationRepository(session)
    customers.add(ACME, AT)

    assert delete_customer(1, customers, simulations) == 0
    assert customers.get(1) is None


def test_an_unknown_customer_raises_and_deletes_nothing(
    stores: tuple[CustomerRepository, SimulationRepository], session: Session
) -> None:
    """CA-1.3 at the service level."""
    customers, simulations = stores

    with pytest.raises(CustomerNotFoundError):
        delete_customer(999, customers, simulations)

    assert _count(session, "SELECT count(*) FROM customers") == 2
    assert _count(session, "SELECT count(*) FROM simulations") == 3


def test_br8_a_failure_deleting_the_customer_keeps_its_history(
    stores: tuple[CustomerRepository, SimulationRepository],
    session: Session,
    migrated_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """BR-8, CA-1.2: the simulations are only gone if the customer is gone, in one transaction."""
    customers, simulations = stores

    def failing_commit() -> None:
        raise RuntimeError("disk full")

    monkeypatch.setattr(session, "commit", failing_commit)
    with pytest.raises(RuntimeError):
        delete_customer(1, customers, simulations)

    with create_session_factory(migrated_engine)() as other:
        assert _count(other, "SELECT count(*) FROM customers WHERE id = 1") == 1
        assert _count(other, "SELECT count(*) FROM simulations WHERE customer_id = 1") == 2
        assert _count(other, "SELECT count(*) FROM simulation_tiers") == 9


def test_br11_the_database_still_rejects_deleting_a_customer_with_history(
    stores: tuple[CustomerRepository, SimulationRepository], session: Session
) -> None:
    """BR-11, CA-1.8 (spec 004 CA-7.3): only the service deletes the history first."""
    with pytest.raises(IntegrityError):
        session.execute(text("DELETE FROM customers WHERE id = 1"))
        session.commit()
    session.rollback()

    assert _count(session, "SELECT count(*) FROM customers WHERE id = 1") == 1
