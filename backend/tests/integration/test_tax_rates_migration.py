"""Migration 0001_create_tax_rates: spec 001 CA-4.2, CA-4.3, the database part of CA-13.1, case C-6.

Also checks the CHECK constraints of plan section 3 and that the ORM model mirrors the migration.
"""

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Base
from tests.integration.conftest import alembic_config

DEFAULT_RATES_BP = {"ES": 2100, "PT": 2300, "FR": 2000, "DE": 1900, "IT": 2200, "GB": 2000, "US": 0}

INSERT = text("INSERT INTO tax_rates (country, rate_bp) VALUES (:country, :rate_bp)")


def test_fresh_database_has_exactly_the_seven_default_rates(session: Session) -> None:
    """C-6, CA-4.3: a migrated empty database already holds the default rates, without seed."""
    rows = session.execute(text("SELECT country, rate_bp FROM tax_rates")).all()

    assert {country: rate_bp for country, rate_bp in rows} == DEFAULT_RATES_BP
    assert all(type(rate_bp) is int for _, rate_bp in rows)


def test_accepts_a_valid_new_rate(session: Session) -> None:
    """Guard: the CHECK constraints do not reject everything."""
    session.execute(INSERT, {"country": "ZZ", "rate_bp": 1500})

    assert session.execute(text("SELECT rate_bp FROM tax_rates WHERE country = 'ZZ'")).scalar_one()


@pytest.mark.parametrize(
    ("country", "rate_bp"),
    [
        pytest.param("ZZ", 10_001, id="rate-above-10000"),
        pytest.param("ZZ", -1, id="rate-negative"),
        pytest.param("ZZ", 21.5, id="rate-not-integer"),
        pytest.param("ZZ", None, id="rate-null"),
        pytest.param("es", 1000, id="country-lowercase"),
        pytest.param("ESP", 1000, id="country-three-letters"),
        pytest.param("E1", 1000, id="country-digit"),
        pytest.param("ES", 2200, id="country-duplicated"),
    ],
)
def test_database_rejects_invalid_rows(
    session: Session, country: str, rate_bp: int | float | None
) -> None:
    """CA-13.1 (database part) and plan section 3: CHECK, NOT NULL and PRIMARY KEY."""
    with pytest.raises(IntegrityError):
        session.execute(INSERT, {"country": country, "rate_bp": rate_bp})


def test_orm_model_mirrors_the_migrated_schema(migrated_engine: Engine) -> None:
    """The model in app/db/models.py must describe the same table the migration creates."""
    with migrated_engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)

    assert differences == []


def test_downgrade_removes_the_table(database_url: str, migrated_engine: Engine) -> None:
    command.downgrade(alembic_config(database_url), "base")

    assert "tax_rates" not in inspect(migrated_engine).get_table_names()
