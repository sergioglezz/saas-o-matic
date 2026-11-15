"""Tax rate repository against the migrated database: spec 001 CA-4.1 and CA-4.7 (task T-09)."""

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import TaxRate
from app.db.session import create_session_factory
from app.repositories.tax_rates import TaxRateRepository


def _row_count(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(TaxRate)) or 0


def test_returns_the_rate_of_a_configured_country(session: Session) -> None:
    """CA-4.1: the rate is read from the configured table."""
    assert TaxRateRepository(session).get_rate_bp("ES") == 2100


@pytest.mark.parametrize(
    "country",
    [
        pytest.param("XX", id="unknown"),
        pytest.param("es", id="lowercase"),
        pytest.param(" ES", id="leading-space"),
        pytest.param("", id="empty"),
    ],
)
def test_returns_none_when_the_exact_code_has_no_rate(session: Session, country: str) -> None:
    """CA-4.7: the code is looked up exactly as received, without normalising it."""
    assert TaxRateRepository(session).get_rate_bp(country) is None


def test_upsert_inserts_a_new_country(session: Session) -> None:
    repository = TaxRateRepository(session)

    repository.upsert("ZZ", 1500)

    assert repository.get_rate_bp("ZZ") == 1500
    assert _row_count(session) == 8


def test_upsert_updates_an_existing_country_without_duplicating_it(session: Session) -> None:
    repository = TaxRateRepository(session)

    repository.upsert("ES", 2200)

    assert repository.get_rate_bp("ES") == 2200
    assert _row_count(session) == 7


def test_delete_removes_the_rate(session: Session) -> None:
    repository = TaxRateRepository(session)

    repository.delete("PT")

    assert repository.get_rate_bp("PT") is None
    assert _row_count(session) == 6


def test_delete_of_an_unknown_country_changes_nothing(session: Session) -> None:
    TaxRateRepository(session).delete("XX")

    assert _row_count(session) == 7


def test_upsert_surfaces_the_database_check_as_soon_as_it_is_called(session: Session) -> None:
    """CA-13.1 (database part): an out-of-range rate fails at the call, not at a later commit."""
    with pytest.raises(IntegrityError):
        TaxRateRepository(session).upsert("ES", 10_001)


def test_committed_changes_are_visible_from_a_new_session(migrated_engine: Engine) -> None:
    """The caller owns the transaction: after its commit, other sessions see the change."""
    session_factory = create_session_factory(migrated_engine)
    with session_factory() as writer:
        TaxRateRepository(writer).upsert("ES", 2200)
        writer.commit()

    with session_factory() as reader:
        assert TaxRateRepository(reader).get_rate_bp("ES") == 2200
