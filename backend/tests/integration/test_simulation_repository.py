"""Simulation repository (level D), spec 004: cases DB-2, DB-10 and DB-11, and the history order.

Covers CA-1.2, CA-1.5, CA-4.2, CA-4.5, CA-5.2 and the data side of CA-5.3. Task T-03.
"""

import dataclasses

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import create_session_factory
from app.domain.customers import NewCustomer
from app.domain.pricing import PriceQuote, build_quote
from app.domain.simulations import NewSimulation, Simulation
from app.repositories.customers import CustomerRepository
from app.repositories.simulations import SimulationRepository

AT_10_00 = "2026-11-16T10:00:00Z"
AT_10_05 = "2026-11-16T10:05:00Z"
ACME = NewCustomer(
    company_name="Acme Telecom S.L.",
    tax_id="B12345674",
    contact_email="compras@acme.example",
    country="ES",
    plan="business",
)
LUSITANIA = dataclasses.replace(ACME, company_name="Lusitânia Cloud Lda", tax_id="PT123456789")
SI_1 = NewSimulation(customer_id=1, active_users=15, storage_gb=200, api_calls_per_month=50_000)
SI_1_PRICE = build_quote(15, 2100)


def _count(session: Session, table: str) -> int:
    count: int = session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
    return count


def _with_users(users: int, customer_id: int = 1) -> tuple[NewSimulation, PriceQuote]:
    new = dataclasses.replace(SI_1, customer_id=customer_id, active_users=users)
    return new, build_quote(users, 2100)


@pytest.fixture
def repository(session: Session) -> SimulationRepository:
    customers = CustomerRepository(session)
    customers.add(ACME, AT_10_00)
    customers.add(LUSITANIA, AT_10_00)
    return SimulationRepository(session)


def test_add_returns_the_saved_snapshot(repository: SimulationRepository) -> None:
    """DB-2, CA-1.2, CA-4.2: id 1, the input, every amount, the tier limits and the instant."""
    saved = repository.add(SI_1, SI_1_PRICE, AT_10_00)

    assert saved == Simulation(
        id=1,
        customer_id=1,
        active_users=15,
        storage_gb=200,
        api_calls_per_month=50_000,
        currency="EUR",
        tiers=SI_1_PRICE.tiers,
        subtotal_cents=14_000,
        tax_rate_bp=2100,
        tax_cents=2940,
        total_cents=16_940,
        created_at=AT_10_00,
    )
    assert saved.tiers[2].to_users is None


def test_history_reads_back_exactly_what_was_saved(repository: SimulationRepository) -> None:
    """DB-2, CA-1.3: the history returns the same object that add returned."""
    saved = repository.add(SI_1, SI_1_PRICE, AT_10_00)

    page = repository.list_for_customer(1, limit=50, offset=0)

    assert page.items == (saved,)
    assert page.total == 1


def test_add_is_already_committed_for_other_sessions(
    repository: SimulationRepository, migrated_engine: Engine
) -> None:
    """Plan DT-4 (003 DT-5): saving is complete when add returns, tiers included."""
    repository.add(SI_1, SI_1_PRICE, AT_10_00)

    with create_session_factory(migrated_engine)() as another_session:
        assert _count(another_session, "simulations") == 1
        assert _count(another_session, "simulation_tiers") == 3


def test_a_failed_save_leaves_nothing(repository: SimulationRepository, session: Session) -> None:
    """DB-10, CA-1.5: the second tier breaks a constraint, so neither the simulation nor any
    tier is left, and the repository keeps working."""
    first, second, third = SI_1_PRICE.tiers
    broken = dataclasses.replace(
        SI_1_PRICE, tiers=(first, dataclasses.replace(second, tier=4), third)
    )

    with pytest.raises(IntegrityError):
        repository.add(SI_1, broken, AT_10_00)

    assert _count(session, "simulations") == _count(session, "simulation_tiers") == 0
    repository.add(SI_1, SI_1_PRICE, AT_10_00)
    assert (_count(session, "simulations"), _count(session, "simulation_tiers")) == (1, 3)


def test_an_id_is_never_reused(repository: SimulationRepository, session: Session) -> None:
    """DB-11, CA-1.2: after deleting the last simulation, the next one does not take its id."""
    repository.add(SI_1, SI_1_PRICE, AT_10_00)
    session.execute(text("DELETE FROM simulation_tiers"))
    session.execute(text("DELETE FROM simulations"))
    session.commit()

    assert repository.add(SI_1, SI_1_PRICE, AT_10_00).id == 2


def test_history_is_newest_first_and_by_id_within_the_same_instant(
    repository: SimulationRepository,
) -> None:
    """CA-5.2, spec decision D-9: the data of table 6.5 gives ids 3, 2, 1 for customer 1."""
    repository.add(*_with_users(15), AT_10_00)
    repository.add(*_with_users(60), AT_10_05)
    repository.add(*_with_users(0), AT_10_05)
    repository.add(*_with_users(1, customer_id=2), AT_10_05)

    page = repository.list_for_customer(1, limit=50, offset=0)

    assert [simulation.id for simulation in page.items] == [3, 2, 1]
    assert page.total == 3


@pytest.mark.parametrize(
    ("limit", "offset", "expected_ids"),
    [
        pytest.param(2, 0, [3, 2], id="HI-4"),
        pytest.param(2, 2, [1], id="HI-5"),
        pytest.param(50, 3, [], id="HI-6"),
    ],
)
def test_history_pages_and_counts_without_the_page(
    repository: SimulationRepository, limit: int, offset: int, expected_ids: list[int]
) -> None:
    """CA-5.3: limit and offset cut the ordered list; total counts every simulation."""
    for users, created_at in ((15, AT_10_00), (60, AT_10_05), (0, AT_10_05)):
        repository.add(*_with_users(users), created_at)

    page = repository.list_for_customer(1, limit=limit, offset=offset)

    assert [simulation.id for simulation in page.items] == expected_ids
    assert page.total == 3


def test_history_of_a_customer_without_simulations_is_empty(
    repository: SimulationRepository,
) -> None:
    """CA-5.4: only the simulations of that customer count."""
    repository.add(SI_1, SI_1_PRICE, AT_10_00)

    page = repository.list_for_customer(2, limit=50, offset=0)

    assert page.items == ()
    assert page.total == 0


def test_history_returns_the_stored_values_without_recalculating(
    repository: SimulationRepository, session: Session
) -> None:
    """CA-4.5, plan DT-6: what is read is what was stored, even if it no longer matches the
    current tiers. A unit price changed in the database comes back as it is."""
    repository.add(SI_1, SI_1_PRICE, AT_10_00)
    session.execute(text("UPDATE simulation_tiers SET unit_price_cents = 999 WHERE tier = 3"))
    session.commit()

    tiers = repository.list_for_customer(1, limit=50, offset=0).items[0].tiers

    assert [line.unit_price_cents for line in tiers] == [1000, 800, 999]
