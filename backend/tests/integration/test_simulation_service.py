"""Simulation service (level D), spec 004 RF-1, RF-3 and RF-4; plan DT-1 to DT-3. Task T-04.

Runs with the real repositories on a migrated temporary database and the default tax rates.
"""

import dataclasses
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.customers import Customer, NewCustomer
from app.domain.errors import (
    CustomerNotFoundError,
    InvalidApiCallsError,
    InvalidStorageError,
    InvalidUsersError,
    UnsupportedCustomerCountryError,
)
from app.domain.simulations import NewSimulation, Simulation
from app.repositories.customers import CustomerRepository
from app.repositories.simulations import SimulationRepository
from app.repositories.tax_rates import TaxRateRepository
from app.services.pricing import quote, set_tax_rate
from app.services.simulations import list_simulations, save_simulation

NOW = datetime(2026, 11, 16, 10, 0, 0, tzinfo=UTC)
ACME = NewCustomer(
    company_name="Acme Telecom S.L.",
    tax_id="B12345674",
    contact_email="compras@acme.example",
    country="ES",
    plan="business",
)
# Customers 1 (ES), 2 (PT) and 3 (US) of the spec's starting table.
CUSTOMERS = (
    ACME,
    dataclasses.replace(
        ACME, company_name="Lusitânia Cloud Lda", tax_id="PT123456789", country="PT"
    ),
    dataclasses.replace(ACME, company_name="Liberty Mesh Inc.", tax_id="US123456789", country="US"),
)
SI_1 = NewSimulation(customer_id=1, active_users=15, storage_gb=200, api_calls_per_month=50_000)


class Stores:
    """The three real repositories over one session."""

    def __init__(self, session: Session) -> None:
        self.customers = CustomerRepository(session)
        self.simulations = SimulationRepository(session)
        self.rates = TaxRateRepository(session)

    def save(self, new: NewSimulation) -> Simulation:
        return save_simulation(new, self.customers, self.simulations, self.rates, NOW)

    def history(self, customer_id: int) -> list[Simulation]:
        return list(list_simulations(customer_id, 50, 0, self.simulations).items)


def _count(session: Session, table: str) -> int:
    count: int = session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
    return count


@pytest.fixture
def stores(session: Session) -> Stores:
    result = Stores(session)
    for customer in CUSTOMERS:
        result.customers.add(customer, "2026-11-13T10:00:00Z")
    return result


@pytest.mark.parametrize(
    ("customer_id", "users"),
    [
        pytest.param(1, 15, id="SI-1-ES"),
        pytest.param(2, 1, id="SI-3-PT"),
        pytest.param(3, 15, id="SI-5-US"),
    ],
)
def test_amounts_are_the_quote_for_the_customer_country(
    stores: Stores, customer_id: int, users: int
) -> None:
    """CA-4.1, CA-3.3, plan DT-1: the snapshot is the quote of 001 for the customer's country."""
    new = dataclasses.replace(SI_1, customer_id=customer_id, active_users=users)
    country = CUSTOMERS[customer_id - 1].country

    saved = save_simulation(new, stores.customers, stores.simulations, stores.rates, NOW)
    expected = quote(users, country, stores.rates)

    assert (saved.tiers, saved.subtotal_cents, saved.tax_rate_bp) == (
        expected.tiers,
        expected.subtotal_cents,
        expected.tax_rate_bp,
    )
    assert (saved.tax_cents, saved.total_cents) == (expected.tax_cents, expected.total_cents)
    assert (saved.active_users, saved.created_at) == (users, "2026-11-16T10:00:00Z")


@pytest.mark.parametrize(
    ("storage_gb", "api_calls_per_month"),
    [pytest.param(0, 0, id="zero"), pytest.param(1_000_000, 1_000_000_000, id="max")],
)
def test_storage_and_api_calls_do_not_change_any_amount(
    stores: Stores, storage_gb: int, api_calls_per_month: int
) -> None:
    """CA-4.6, SN-2 (RN-9): same users and customer, same amounts."""
    baseline = save_simulation(SI_1, stores.customers, stores.simulations, stores.rates, NOW)
    new = dataclasses.replace(SI_1, storage_gb=storage_gb, api_calls_per_month=api_calls_per_month)

    other = save_simulation(new, stores.customers, stores.simulations, stores.rates, NOW)

    assert (other.tiers, other.total_cents) == (baseline.tiers, baseline.total_cents)


def test_unknown_customer_saves_nothing(stores: Stores, session: Session) -> None:
    """CA-3.1, CA-1.4: an id with no customer raises CustomerNotFoundError."""
    with pytest.raises(CustomerNotFoundError):
        stores.save(dataclasses.replace(SI_1, customer_id=999))

    assert _count(session, "simulations") == 0


def test_country_without_rate_saves_nothing(stores: Stores, session: Session) -> None:
    """CA-3.4, SC-3, plan DT-3: the error names the customer, not a country field."""
    stores.rates.delete("PT")

    with pytest.raises(UnsupportedCustomerCountryError) as raised:
        stores.save(dataclasses.replace(SI_1, customer_id=2, active_users=1))

    assert raised.value.customer_id == 2
    assert _count(session, "simulations") == 0


@pytest.mark.parametrize(
    ("changes", "error_type"),
    [
        pytest.param({"active_users": -1}, InvalidUsersError, id="users"),
        pytest.param({"storage_gb": -1}, InvalidStorageError, id="storage"),
        pytest.param({"api_calls_per_month": 1_000_000_001}, InvalidApiCallsError, id="api-calls"),
        pytest.param({"storage_gb": -1, "customer_id": 999}, InvalidStorageError, id="before-404"),
    ],
)
def test_service_validates_the_input_by_itself(
    stores: Stores, session: Session, changes: dict[str, int], error_type: type[Exception]
) -> None:
    """Plan DT-2: the rules hold whoever calls the service; validation goes before the
    customer lookup (CA-3.2)."""
    with pytest.raises(error_type):
        stores.save(dataclasses.replace(SI_1, **changes))

    assert _count(session, "simulations") == 0


def test_a_saved_simulation_keeps_its_rate_after_a_rate_change(stores: Stores) -> None:
    """CA-4.3, SN-3, SN-4: the history keeps 2100; a new simulation uses 2150."""
    stores.save(SI_1)
    set_tax_rate("ES", 2150, stores.rates)

    newer = save_simulation(SI_1, stores.customers, stores.simulations, stores.rates, NOW)
    older = list_simulations(1, 50, 0, stores.simulations).items[-1]

    assert (older.tax_rate_bp, older.tax_cents, older.total_cents) == (2100, 2940, 16_940)
    assert (newer.tax_rate_bp, newer.tax_cents, newer.total_cents) == (2150, 3010, 17_010)


def test_history_survives_the_country_losing_its_rate(stores: Stores) -> None:
    """CA-4.4, SN-5: the PT simulation is still listed after removing the PT rate."""
    saved = stores.save(dataclasses.replace(SI_1, customer_id=2, active_users=1))
    stores.rates.delete("PT")

    assert stores.history(2) == [saved]


def test_saving_changes_neither_the_customer_nor_the_rates(
    stores: Stores, session: Session
) -> None:
    """CA-1.6: only the simulation tables change."""
    rates = session.execute(text("SELECT country, rate_bp FROM tax_rates ORDER BY 1")).all()
    customer_before: Customer | None = stores.customers.get(1)

    stores.save(SI_1)

    assert stores.customers.get(1) == customer_before
    assert session.execute(text("SELECT country, rate_bp FROM tax_rates ORDER BY 1")).all() == rates


def test_list_simulations_pages_the_store(stores: Stores) -> None:
    """CA-5.3: the service passes limit and offset to the store and returns its page."""
    for users in (15, 60, 0):
        stores.save(dataclasses.replace(SI_1, active_users=users))

    page = list_simulations(1, 1, 1, stores.simulations)

    assert [simulation.active_users for simulation in page.items] == [60]
    assert page.total == 3
