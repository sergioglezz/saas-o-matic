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

# The six customers of spec table 6.6, in creation order (ids 1 to 6).
TABLE_6_6_CUSTOMERS = [
    ("Zeta Redes S.A.", "A00000000", "ES"),
    ("acme telecom s.l.", "B12345674", "ES"),
    ("COMPAÑÍA Ñandú", "12345678Z", "ES"),
    ("Telefónica Demo", "PT123456789", "PT"),
    ("100% Fibra GmbH", "DE1234567", "DE"),
    ("Acme Cloud Ltd", "GB7654321", "GB"),
]
ALL_BY_NAME = [5, 6, 2, 3, 4, 1]


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


@pytest.fixture
def six_customers(session: Session) -> CustomerRepository:
    repository = CustomerRepository(session)
    for company_name, tax_id, country in TABLE_6_6_CUSTOMERS:
        new = dataclasses.replace(ACME, company_name=company_name, tax_id=tax_id, country=country)
        repository.add(new, CREATED_AT)
    return repository


def test_connections_have_a_casefold_function_for_any_letter(session: Session) -> None:
    """CA-5.3, plan DT-6: SQLite's own lower() leaves non-ASCII capitals as they are."""
    row = session.execute(text("SELECT casefold('COMPAÑÍA Ñandú'), lower('COMPAÑÍA')")).one()

    assert row == ("compañía ñandú", "compaÑÍa")


@pytest.mark.parametrize(
    ("name_fragment", "tax_id_fragment", "limit", "offset", "ids", "total"),
    [
        pytest.param("", "", 50, 0, ALL_BY_NAME, 6, id="no-filter-ordered-by-name"),
        pytest.param("acme", "ACME", 50, 0, [6, 2], 2, id="name-ignoring-case"),
        pytest.param("compañía ñ", "COMPAÑÍAÑ", 50, 0, [3], 1, id="name-with-non-ascii-letters"),
        pytest.param("b1234", "B1234", 50, 0, [2], 1, id="tax-id-fragment"),
        pytest.param("12.345.678-z", "12345678Z", 50, 0, [3], 1, id="tax-id-with-separators"),
        pytest.param("fibra", "", 50, 0, [5], 1, id="name-only"),
        pytest.param("", "GB76", 50, 0, [6], 1, id="tax-id-only"),
        pytest.param("%", "%", 50, 0, [5], 1, id="percent-is-literal"),
        pytest.param("_", "_", 50, 0, [], 0, id="underscore-is-literal"),
        pytest.param("telefonica", "TELEFONICA", 50, 0, [], 0, id="accents-are-not-folded"),
        pytest.param("inexistente", "INEXISTENTE", 50, 0, [], 0, id="no-match"),
        pytest.param("", "", 2, 0, [5, 6], 6, id="limit"),
        pytest.param("", "", 2, 4, [4, 1], 6, id="limit-and-offset"),
        pytest.param("", "", 50, 6, [], 6, id="offset-past-the-end"),
        pytest.param("acme", "ACME", 1, 0, [6], 2, id="total-ignores-the-page"),
    ],
)
def test_search_filters_orders_and_pages(
    six_customers: CustomerRepository,
    name_fragment: str,
    tax_id_fragment: str,
    limit: int,
    offset: int,
    ids: list[int],
    total: int,
) -> None:
    """CA-5.3 to CA-5.7: literal fragments, order by name then id, page and full count."""
    page = six_customers.search(name_fragment, tax_id_fragment, limit, offset)

    assert [customer.id for customer in page.items] == ids
    assert page.total == total


def test_search_treats_sql_as_plain_text(six_customers: CustomerRepository) -> None:
    """CA-5.4, RNF-2: a fragment full of SQL finds nothing and breaks nothing."""
    attack = "'; drop table customers;--"

    assert six_customers.search(attack, attack.upper(), 50, 0).total == 0
    assert six_customers.search("", "", 50, 0).total == 6
