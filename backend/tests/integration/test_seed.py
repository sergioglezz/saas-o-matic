"""Demo data seed (level D), spec 003 RF-10: cases SE-1 to SE-5.

The seed goes through the same schema and service as POST /customers (CA-10.3).
"""

import dataclasses
from datetime import UTC, datetime

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.db.seed import DEMO_CUSTOMERS, main, seed_customers
from app.domain.tax_id import validate_tax_id
from app.repositories.customers import CustomerRepository
from app.repositories.tax_rates import TaxRateRepository
from app.schemas.customers import CustomerCreate
from app.services.customers import register_customer

NOW = datetime(2026, 11, 13, 10, 0, 0, tzinfo=UTC)
SUPPORTED_COUNTRIES = {"ES", "PT", "FR", "DE", "IT", "GB", "US"}


def _rows(session: Session, sql: str) -> list[tuple[object, ...]]:
    return [tuple(row) for row in session.execute(text(sql)).all()]


def test_seed_creates_ten_customers_covering_countries_and_plans(session: Session) -> None:
    """SE-1, CA-10.1: 10 customers, the 7 supported countries and the 3 plans."""
    created = seed_customers(session, NOW)

    rows = _rows(session, "SELECT country, plan, created_at FROM customers")
    assert created == 10 == len(rows)
    assert {country for country, _, _ in rows} == SUPPORTED_COUNTRIES
    assert {plan for _, plan, _ in rows} == {"starter", "business", "enterprise"}
    assert {created_at for _, _, created_at in rows} == {"2026-11-13T10:00:00Z"}


def test_seed_can_run_twice_without_duplicating(session: Session) -> None:
    """SE-2, CA-10.2: the second run creates nothing and does not fail."""
    seed_customers(session, NOW)
    before = _rows(session, "SELECT * FROM customers ORDER BY id")

    assert seed_customers(session, NOW) == 0
    assert _rows(session, "SELECT * FROM customers ORDER BY id") == before


@pytest.mark.parametrize("raw", [pytest.param(raw, id=raw["tax_id"]) for raw in DEMO_CUSTOMERS])
def test_every_demo_customer_passes_the_registration_rules(raw: dict[str, str]) -> None:
    """SE-3, CA-10.3, RNF-5: valid, already normalized, and obviously invented."""
    request = CustomerCreate.model_validate(raw)

    assert request.model_dump() == raw  # stored exactly as written in the seed
    assert validate_tax_id(raw["tax_id"], raw["country"]) == raw["tax_id"]
    assert raw["contact_email"].endswith(".example")


def test_demo_tax_ids_are_all_different() -> None:
    """CA-10.1: ten customers means ten different identifiers."""
    assert len({raw["tax_id"] for raw in DEMO_CUSTOMERS}) == len(DEMO_CUSTOMERS) == 10


def test_seed_respects_a_customer_that_already_uses_a_demo_tax_id(session: Session) -> None:
    """SE-4, CA-10.2, CA-10.4: it is left as it is and the other nine are created."""
    first = CustomerCreate.model_validate(DEMO_CUSTOMERS[0]).to_new_customer()
    mine = dataclasses.replace(first, company_name="Mi cliente real")
    registered = register_customer(
        mine, CustomerRepository(session), TaxRateRepository(session), NOW
    )

    assert seed_customers(session, NOW) == 9

    assert CustomerRepository(session).get(registered.id) == registered
    assert len(_rows(session, "SELECT id FROM customers")) == 10


def test_seed_does_not_touch_the_tax_rates(session: Session) -> None:
    """SE-5, CA-10.4: the same seven rates before and after."""
    before = _rows(session, "SELECT country, rate_bp FROM tax_rates ORDER BY country")

    seed_customers(session, NOW)

    assert _rows(session, "SELECT country, rate_bp FROM tax_rates ORDER BY country") == before
    assert len(before) == 7


def test_command_reports_what_it_created(
    database_url: str,
    migrated_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CA-10.1, CA-10.2: `python -m app.db.seed` uses the configured database and says so."""
    monkeypatch.setenv("DATABASE_URL", database_url)

    main()
    first_run = capsys.readouterr().out
    main()
    second_run = capsys.readouterr().out

    assert "10 creados, 0 ya existían" in first_run
    assert "0 creados, 10 ya existían" in second_run
    with migrated_engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM customers")).scalar_one() == 10
