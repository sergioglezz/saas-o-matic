"""Migration 0002_create_customers (level D), spec 003 RF-9: cases DB-1, DB-3 to DB-6, DB-8, DB-9.

The database defends its own rules, also against a write that skips the API (CA-9.2).
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

COLUMNS = ("company_name", "tax_id", "contact_email", "country", "plan", "created_at")
INSERT = text(
    "INSERT INTO customers (company_name, tax_id, contact_email, country, plan, created_at) "
    "VALUES (:company_name, :tax_id, :contact_email, :country, :plan, :created_at)"
)
VALID_ROW: dict[str, object] = {
    "company_name": "Acme Telecom S.L.",
    "tax_id": "B12345674",
    "contact_email": "compras@acme.example",
    "country": "ES",
    "plan": "business",
    "created_at": "2026-11-13T10:00:00Z",
}


def test_fresh_database_has_an_empty_customers_table(session: Session) -> None:
    """DB-1, CA-9.1: the table exists after preparing the database and holds no customer."""
    columns = {column["name"] for column in inspect(session.get_bind()).get_columns("customers")}

    assert columns == {"id", *COLUMNS}
    assert session.execute(text("SELECT count(*) FROM customers")).scalar_one() == 0


def test_accepts_a_valid_row_and_numbers_it(session: Session) -> None:
    """Guard: the constraints do not reject everything. CA-9.1: the id is assigned."""
    session.execute(INSERT, VALID_ROW)

    assert session.execute(text("SELECT id, plan FROM customers")).all() == [(1, "business")]


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"plan": "gold"}, id="DB-3-plan-not-in-the-list"),
        pytest.param({"plan": "Business"}, id="DB-3-plan-with-another-case"),
        pytest.param({"country": "es"}, id="DB-4-country-lowercase"),
        pytest.param({"country": "ESP"}, id="DB-4-country-three-letters"),
        pytest.param({"company_name": ""}, id="DB-5-company-name-empty"),
        pytest.param({"company_name": "x" * 121}, id="DB-5-company-name-121-characters"),
        *[pytest.param({column: None}, id=f"DB-6-{column}-null") for column in COLUMNS],
    ],
)
def test_database_rejects_invalid_rows(session: Session, changes: dict[str, object]) -> None:
    """DB-3 to DB-6, CA-9.2: CHECK and NOT NULL reject the row by themselves."""
    with pytest.raises(IntegrityError):
        session.execute(INSERT, {**VALID_ROW, **changes})


def test_company_name_of_120_characters_is_accepted(session: Session) -> None:
    """CA-9.2: the limit itself is valid (boundary of DB-5)."""
    session.execute(INSERT, {**VALID_ROW, "company_name": "x" * 120})

    assert session.execute(text("SELECT length(company_name) FROM customers")).scalar_one() == 120


def test_database_rejects_a_repeated_tax_id(session: Session) -> None:
    """CA-9.2, CA-4.4: the uniqueness of tax_id is a constraint of the table."""
    session.execute(INSERT, VALID_ROW)

    with pytest.raises(IntegrityError, match=r"UNIQUE constraint failed: customers\.tax_id"):
        session.execute(INSERT, {**VALID_ROW, "company_name": "Otra empresa"})


def test_company_name_is_indexed(migrated_engine: Engine) -> None:
    """00-spec-first 8.5: company_name has an index (spec decision D-11)."""
    indexes = {index["name"]: index for index in inspect(migrated_engine).get_indexes("customers")}

    assert indexes["ix_customers_company_name"]["column_names"] == ["company_name"]


def test_downgrade_removes_customers_and_keeps_tax_rates(
    database_url: str, migrated_engine: Engine
) -> None:
    """DB-8, CA-9.3: undoing this migration leaves the tax rates of 0001 untouched."""
    command.downgrade(alembic_config(database_url), "0001")

    assert "customers" not in inspect(migrated_engine).get_table_names()
    with migrated_engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM tax_rates")).scalar_one() == 7


def test_orm_models_mirror_the_migrated_schema(migrated_engine: Engine) -> None:
    """DB-9, CA-9.1: app/db/models.py describes exactly what the migrations create."""
    with migrated_engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)

    assert differences == []
    assert "customers" in Base.metadata.tables
