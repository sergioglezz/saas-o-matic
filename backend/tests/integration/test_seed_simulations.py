"""Demo simulations of the seed (level D), spec 004 RF-8: cases SE-1 to SE-6. Task T-12.

The seed goes through the same schema, service and calculation as POST /simulations (CA-8.3),
and looks for each demo customer by its tax id (CA-8.2, plan DT-13).
"""

import dataclasses
from datetime import UTC, datetime

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.db.seed import DEMO_CUSTOMERS, DEMO_SIMULATIONS, main, seed_customers, seed_simulations
from app.domain.customers import Customer, NewCustomer
from app.domain.simulations import NewSimulation
from app.repositories.customers import CustomerRepository
from app.repositories.simulations import SimulationRepository
from app.repositories.tax_rates import TaxRateRepository
from app.services.pricing import quote
from app.services.simulations import save_simulation

NOW = datetime(2026, 11, 16, 10, 0, 0, tzinfo=UTC)
ACME = "B12345674"
# Spec table 6.9: tax id, active users, storage, API calls and the expected total.
TABLE_6_9 = [
    (ACME, 15, 200, 50_000, 16_940),
    (ACME, 60, 500, 250_000, 56_870),
    ("PT123456789", 1, 10, 1000, 1230),
    ("DE123456789", 11, 100, 20_000, 12_852),
    ("GB123456789", 100, 1000, 1_000_000, 80_400),
    ("US123456789", 51, 300, 100_000, 42_500),
]
SIMULATION_ROWS = (
    "SELECT c.tax_id, s.active_users, s.storage_gb, s.api_calls_per_month, s.total_cents "
    "FROM simulations s JOIN customers c ON c.id = s.customer_id ORDER BY s.id"
)


def _rows(session: Session, sql: str) -> list[tuple[object, ...]]:
    return [tuple(row) for row in session.execute(text(sql)).all()]


def _count(session: Session, table: str) -> int:
    count: int = session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
    return count


def _customer(session: Session, tax_id: str) -> Customer:
    customer = CustomerRepository(session).find_by_tax_id(tax_id)
    assert customer is not None
    return customer


def test_demo_simulations_are_the_ones_of_table_6_9() -> None:
    """CA-8.1: the seed data is exactly table 6.9, three tiers and a country at 0 %."""
    assert [row[:4] for row in TABLE_6_9] == [tuple(row) for row in DEMO_SIMULATIONS]
    assert {row[0] for row in TABLE_6_9} <= {raw["tax_id"] for raw in DEMO_CUSTOMERS}


def test_se_1_seed_creates_the_six_simulations(session: Session) -> None:
    """SE-1, CA-8.1: 10 customers and the 6 simulations of table 6.9, with their totals."""
    seed_customers(session, NOW)

    created = seed_simulations(session, NOW)

    assert created == 6
    assert _count(session, "customers") == 10
    assert _rows(session, SIMULATION_ROWS) == TABLE_6_9


def test_se_2_seed_can_run_twice_without_duplicating(session: Session) -> None:
    """SE-2, CA-8.2: the second run creates nothing and does not fail."""
    seed_customers(session, NOW)
    seed_simulations(session, NOW)

    assert seed_simulations(session, NOW) == 0
    assert _count(session, "simulations") == 6


def test_se_3_seed_completes_a_database_seeded_by_spec_003(session: Session) -> None:
    """SE-3, CA-8.2: with the 10 demo customers and no simulations, it creates the 6 only."""
    seed_customers(session, NOW)
    customers_before = _rows(session, "SELECT * FROM customers ORDER BY id")

    assert seed_simulations(session, NOW) == 6
    assert _rows(session, "SELECT * FROM customers ORDER BY id") == customers_before


def test_se_4_a_customer_with_simulations_keeps_only_its_own(session: Session) -> None:
    """SE-4, CA-8.2, CA-8.4: Acme keeps its own simulation; the other 4 get theirs."""
    seed_customers(session, NOW)
    acme = _customer(session, ACME)
    own = save_simulation(
        NewSimulation(acme.id, 7, 1, 1),
        CustomerRepository(session),
        SimulationRepository(session),
        TaxRateRepository(session),
        NOW,
    )

    assert seed_simulations(session, NOW) == 4

    acme_page = SimulationRepository(session).list_for_customer(acme.id, 50, 0)
    assert acme_page.items == (own,)
    assert _count(session, "simulations") == 5


def test_se_5_every_demo_simulation_is_its_quote(session: Session) -> None:
    """SE-5, CA-8.3, RNF-2: each one has the amounts of the quote for its users and country."""
    seed_customers(session, NOW)
    seed_simulations(session, NOW)
    rates = TaxRateRepository(session)

    for tax_id in {row[0] for row in TABLE_6_9}:
        customer = _customer(session, tax_id)
        page = SimulationRepository(session).list_for_customer(customer.id, 50, 0)
        for simulation in page.items:
            expected = quote(simulation.active_users, customer.country, rates)
            assert simulation.tiers == expected.tiers
            assert (simulation.tax_rate_bp, simulation.total_cents) == (
                expected.tax_rate_bp,
                expected.total_cents,
            )


def test_se_6_seed_changes_neither_rates_nor_customers(session: Session) -> None:
    """SE-6, CA-8.4: the same rates and customers before and after the demo simulations."""
    seed_customers(session, NOW)
    before = (
        _rows(session, "SELECT country, rate_bp FROM tax_rates ORDER BY country"),
        _rows(session, "SELECT * FROM customers ORDER BY id"),
    )

    seed_simulations(session, NOW)

    after = (
        _rows(session, "SELECT country, rate_bp FROM tax_rates ORDER BY country"),
        _rows(session, "SELECT * FROM customers ORDER BY id"),
    )
    assert after == before


def test_seed_skips_a_demo_customer_that_does_not_exist(session: Session) -> None:
    """CA-8.2: without the demo customers there is nobody to simulate for; nothing fails."""
    assert seed_simulations(session, NOW) == 0
    assert _count(session, "simulations") == 0


def test_find_by_tax_id_reads_the_exact_customer(session: Session) -> None:
    """CA-8.2, plan DT-13: the seed finds a customer by its normalized tax id, exactly."""
    repository = CustomerRepository(session)
    new = NewCustomer("Acme Telecom S.L.", ACME, "compras@acme.example", "ES", "business")
    saved = repository.add(new, "2026-11-16T10:00:00Z")
    repository.add(dataclasses.replace(new, tax_id="B1234567"), "2026-11-16T10:00:00Z")

    assert repository.find_by_tax_id(ACME) == saved
    assert repository.find_by_tax_id("B123456") is None  # a fragment is not a match


def test_command_reports_the_simulations_it_created(
    database_url: str,
    migrated_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CA-8.1, CA-8.2: `python -m app.db.seed` loads the 6 simulations and says so."""
    monkeypatch.setenv("DATABASE_URL", database_url)

    main()
    first_run = capsys.readouterr().out
    main()
    second_run = capsys.readouterr().out

    assert "Simulaciones de demostración: 6 creadas" in first_run
    assert "Simulaciones de demostración: 0 creadas" in second_run
    with migrated_engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM simulations")).scalar_one() == 6
