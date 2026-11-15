"""Customer repository (level D), spec 003: cases DB-2 and DB-7, and the search of RF-5.

Runs against a migrated temporary database, without a web server.
"""

import dataclasses

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.db.session import create_session_factory
from app.domain.customers import Customer, NewCustomer
from app.domain.errors import DuplicateTaxIdError
from app.repositories.customers import CustomerRepository

CREATED_AT = "2026-11-13T10:00:00Z"
ACME = NewCustomer(
    company_name="Acme Telecom S.L.",
    tax_id="B12345674",
    contact_email="compras@acme.example",
    country="ES",
    plan="business",
)
ZETA = dataclasses.replace(ACME, company_name="Zeta Redes S.A.", tax_id="A00000000")


def _count(session: Session) -> int:
    count: int = session.execute(text("SELECT count(*) FROM customers")).scalar_one()
    return count


def test_add_returns_the_saved_customer_and_get_reads_it_back(session: Session) -> None:
    """CA-1.3: the customer gets id 1 and the creation instant it was given."""
    repository = CustomerRepository(session)

    saved = repository.add(ACME, CREATED_AT)

    assert saved == Customer(id=1, created_at=CREATED_AT, **dataclasses.asdict(ACME))
    assert repository.get(1) == saved


def test_add_is_already_committed_for_other_sessions(
    session: Session, migrated_engine: Engine
) -> None:
    """Plan DT-5: registering is a single write, and the repository completes it."""
    CustomerRepository(session).add(ACME, CREATED_AT)

    with create_session_factory(migrated_engine)() as another_session:
        assert CustomerRepository(another_session).get(1) is not None


def test_get_returns_none_for_an_unknown_id(session: Session) -> None:
    """CA-6.2 (repository part): no customer, no error."""
    assert CustomerRepository(session).get(999) is None


def test_second_customer_with_the_same_tax_id_is_rejected(session: Session) -> None:
    """DB-2, CA-4.4: the database decides; one row remains and the session keeps working."""
    repository = CustomerRepository(session)
    repository.add(ACME, CREATED_AT)

    with pytest.raises(DuplicateTaxIdError):
        repository.add(dataclasses.replace(ACME, company_name="Otra empresa"), CREATED_AT)

    assert _count(session) == 1
    assert repository.add(ZETA, CREATED_AT).id == 2


def test_ids_are_never_reused(session: Session) -> None:
    """DB-7, CA-1.3: deleting the last customer does not free its id."""
    repository = CustomerRepository(session)
    repository.add(ACME, CREATED_AT)
    repository.add(ZETA, CREATED_AT)
    session.execute(text("DELETE FROM customers WHERE id = 2"))
    session.commit()

    new = repository.add(dataclasses.replace(ZETA, tax_id="12345678Z"), CREATED_AT)

    assert new.id == 3
