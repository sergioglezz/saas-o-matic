"""Migration 0003_create_simulations (level D), spec 004 RF-7. Task T-02.

Cases DB-1, DB-3 to DB-9, DB-12 and DB-13: the database defends its own rules, also against a
write that skips the API (CA-7.2, CA-7.3).
"""

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Base
from tests.conftest import alembic_config

SIMULATION_COLUMNS = (
    "customer_id",
    "active_users",
    "storage_gb",
    "api_calls_per_month",
    "subtotal_cents",
    "tax_rate_bp",
    "tax_cents",
    "total_cents",
    "created_at",
)
TIER_COLUMNS = (
    "simulation_id",
    "tier",
    "from_users",
    "to_users",
    "units",
    "unit_price_cents",
    "amount_cents",
)
INSERT_CUSTOMER = text(
    "INSERT INTO customers (company_name, tax_id, contact_email, country, plan, created_at) "
    "VALUES ('Acme Telecom S.L.', 'B12345674', 'compras@acme.example', 'ES', 'business', "
    "'2026-11-13T10:00:00Z')"
)
INSERT_SIMULATION = text(
    f"INSERT INTO simulations ({', '.join(SIMULATION_COLUMNS)}) "
    f"VALUES ({', '.join(f':{column}' for column in SIMULATION_COLUMNS)})"
)
INSERT_TIER = text(
    f"INSERT INTO simulation_tiers ({', '.join(TIER_COLUMNS)}) "
    f"VALUES ({', '.join(f':{column}' for column in TIER_COLUMNS)})"
)
# SI-1 of the spec: 15 users of a Spanish customer.
VALID_SIMULATION: dict[str, object] = {
    "customer_id": 1,
    "active_users": 15,
    "storage_gb": 200,
    "api_calls_per_month": 50_000,
    "subtotal_cents": 14_000,
    "tax_rate_bp": 2100,
    "tax_cents": 2940,
    "total_cents": 16_940,
    "created_at": "2026-11-16T10:00:00Z",
}
VALID_TIER: dict[str, object] = {
    "simulation_id": 1,
    "tier": 1,
    "from_users": 1,
    "to_users": 10,
    "units": 10,
    "unit_price_cents": 1000,
    "amount_cents": 10_000,
}


def _count(session: Session, table: str) -> int:
    count: int = session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
    return count


@pytest.fixture
def customer(session: Session) -> None:
    session.execute(INSERT_CUSTOMER)


@pytest.fixture
def simulation(session: Session, customer: None) -> None:
    session.execute(INSERT_SIMULATION, VALID_SIMULATION)


def test_fresh_database_has_both_tables_empty(session: Session) -> None:
    """DB-1, CA-7.1: the two tables exist after preparing the database and hold no rows."""
    inspector = inspect(session.get_bind())

    simulation_columns = {column["name"] for column in inspector.get_columns("simulations")}
    tier_columns = {column["name"] for column in inspector.get_columns("simulation_tiers")}

    assert simulation_columns == {"id", *SIMULATION_COLUMNS}
    assert tier_columns == set(TIER_COLUMNS)
    assert _count(session, "simulations") == _count(session, "simulation_tiers") == 0


def test_accepts_a_valid_simulation_and_its_tiers(session: Session, simulation: None) -> None:
    """Guard: the constraints do not reject everything. CA-4.2: the open tier has no end."""
    session.execute(INSERT_TIER, VALID_TIER)
    session.execute(INSERT_TIER, {**VALID_TIER, "tier": 3, "from_users": 51, "to_users": None})

    assert session.execute(text("SELECT id, total_cents FROM simulations")).all() == [(1, 16_940)]
    assert _count(session, "simulation_tiers") == 2


@pytest.mark.parametrize(
    ("column", "maximum"),
    [("active_users", 100_000), ("storage_gb", 1_000_000), ("api_calls_per_month", 1_000_000_000)],
)
def test_usage_limits_themselves_are_accepted(
    session: Session, customer: None, column: str, maximum: int
) -> None:
    """CA-7.2: 0 and the maximum of RF-2 are valid (boundaries of DB-4)."""
    session.execute(INSERT_SIMULATION, {**VALID_SIMULATION, column: 0})
    session.execute(INSERT_SIMULATION, {**VALID_SIMULATION, column: maximum})

    assert _count(session, "simulations") == 2


def test_rejects_a_simulation_of_an_unknown_customer(session: Session) -> None:
    """DB-3, CA-7.2: customer_id must name an existing customer."""
    with pytest.raises(IntegrityError, match="FOREIGN KEY constraint failed"):
        session.execute(INSERT_SIMULATION, {**VALID_SIMULATION, "customer_id": 99})


def test_rejects_a_tier_of_an_unknown_simulation(session: Session) -> None:
    """DB-3, CA-7.2: simulation_id must name an existing simulation."""
    with pytest.raises(IntegrityError, match="FOREIGN KEY constraint failed"):
        session.execute(INSERT_TIER, {**VALID_TIER, "simulation_id": 99})


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"active_users": -1}, id="DB-4-active-users-negative"),
        pytest.param({"active_users": 100_001}, id="DB-4-active-users-above-max"),
        pytest.param({"storage_gb": -1}, id="DB-4-storage-negative"),
        pytest.param({"storage_gb": 1_000_001}, id="DB-4-storage-above-max"),
        pytest.param({"api_calls_per_month": -1}, id="DB-4-api-calls-negative"),
        pytest.param({"api_calls_per_month": 1_000_000_001}, id="DB-4-api-calls-above-max"),
        pytest.param({"active_users": 1.5}, id="DB-5-active-users-decimal"),
        pytest.param({"storage_gb": 1.5}, id="DB-5-storage-decimal"),
        pytest.param({"api_calls_per_month": 1.5}, id="DB-5-api-calls-decimal"),
        pytest.param({"total_cents": 16_941}, id="DB-6-total-is-not-the-sum"),
        pytest.param(
            {"subtotal_cents": -1, "tax_cents": 0, "total_cents": -1}, id="DB-6-negative-subtotal"
        ),
        pytest.param(
            {"subtotal_cents": 1, "tax_cents": -1, "total_cents": 0}, id="DB-6-negative-tax"
        ),
        pytest.param(
            {"subtotal_cents": 0.5, "tax_cents": 0, "total_cents": 0.5}, id="DB-6-decimal-amount"
        ),
        pytest.param({"tax_rate_bp": 10_001}, id="DB-6-tax-rate-above-100-percent"),
        pytest.param({"tax_rate_bp": -1}, id="DB-6-tax-rate-negative"),
        *[pytest.param({column: None}, id=f"DB-8-{column}-null") for column in SIMULATION_COLUMNS],
    ],
)
def test_database_rejects_invalid_simulations(
    session: Session, customer: None, changes: dict[str, object]
) -> None:
    """DB-4 to DB-6 and DB-8, CA-7.2: CHECK and NOT NULL reject the row by themselves."""
    with pytest.raises(IntegrityError):
        session.execute(INSERT_SIMULATION, {**VALID_SIMULATION, **changes})


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"tier": 0}, id="DB-7-tier-0"),
        pytest.param({"tier": 4}, id="DB-7-tier-4"),
        pytest.param({"from_users": 0}, id="from-users-0"),
        pytest.param({"to_users": 10.5}, id="to-users-decimal"),
        pytest.param({"units": -1}, id="negative-units"),
        pytest.param({"unit_price_cents": -1}, id="negative-unit-price"),
        pytest.param({"amount_cents": -1}, id="negative-amount"),
        pytest.param({"amount_cents": 0.5}, id="decimal-amount"),
        *[
            pytest.param({column: None}, id=f"DB-8-{column}-null")
            for column in TIER_COLUMNS
            if column != "to_users"
        ],
    ],
)
def test_database_rejects_invalid_tiers(
    session: Session, simulation: None, changes: dict[str, object]
) -> None:
    """DB-7, DB-8, CA-7.2: a tier outside 1..3, a negative or decimal amount, or a NULL."""
    with pytest.raises(IntegrityError):
        session.execute(INSERT_TIER, {**VALID_TIER, **changes})


def test_database_rejects_the_same_tier_twice(session: Session, simulation: None) -> None:
    """DB-7, CA-7.2: (simulation_id, tier) is the primary key."""
    session.execute(INSERT_TIER, VALID_TIER)

    with pytest.raises(IntegrityError, match="UNIQUE constraint failed"):
        session.execute(INSERT_TIER, VALID_TIER)


def test_database_rejects_deleting_a_customer_with_simulations(
    session: Session, simulation: None
) -> None:
    """DB-9, CA-7.3: the customer and its simulations stay."""
    # Committed first: the rollback after the failed delete must not undo the fixture rows.
    session.commit()

    with pytest.raises(IntegrityError, match="FOREIGN KEY constraint failed"):
        session.execute(text("DELETE FROM customers WHERE id = 1"))
    session.rollback()

    assert _count(session, "customers") == _count(session, "simulations") == 1


def test_history_index_exists(migrated_engine: Engine) -> None:
    """CA-7.5 (00-spec-first 8.5): the history is indexed by customer and instant."""
    indexes = {
        index["name"]: index for index in inspect(migrated_engine).get_indexes("simulations")
    }

    index = indexes["ix_simulations_customer_id_created_at"]
    assert index["column_names"] == ["customer_id", "created_at"]


def test_downgrade_removes_simulations_and_keeps_the_rest(
    database_url: str, migrated_engine: Engine, session: Session, simulation: None
) -> None:
    """DB-12, CA-7.4: customers keep their rows and tax_rates its 7 rates."""
    session.execute(INSERT_TIER, VALID_TIER)
    # Alembic uses its own connection: the rows must be committed or SQLite stays locked.
    session.commit()

    command.downgrade(alembic_config(database_url), "0002")

    tables = inspect(migrated_engine).get_table_names()
    assert "simulations" not in tables
    assert "simulation_tiers" not in tables
    with migrated_engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM customers")).scalar_one() == 1
        assert connection.execute(text("SELECT count(*) FROM tax_rates")).scalar_one() == 7


def test_orm_models_mirror_the_migrated_schema(migrated_engine: Engine) -> None:
    """DB-13, CA-7.1: app/db/models.py describes exactly what the migrations create."""
    with migrated_engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)

    assert differences == []
    assert {"simulations", "simulation_tiers"} <= set(Base.metadata.tables)
