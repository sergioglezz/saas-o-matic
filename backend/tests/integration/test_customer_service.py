"""Customer use cases (level D), spec 003 RF-1, RF-3, RF-4, RF-5 and RF-6.

The service is called directly, as the seed does: it must enforce the rules by itself, without
relying on the API schema (plan 003 DT-2).
"""

import dataclasses
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.customers import Customer, NewCustomer
from app.domain.errors import (
    CustomerNotFoundError,
    DuplicateTaxIdError,
    InvalidSpanishTaxIdError,
    InvalidTaxIdFormatError,
    UnsupportedCountryError,
    UnsupportedTaxIdTypeError,
)
from app.repositories.customers import CustomerRepository
from app.repositories.tax_rates import TaxRateRepository
from app.services.customers import get_customer, register_customer, search_customers
from tests.integration.test_customer_repository import ALL_BY_NAME, TABLE_6_6_CUSTOMERS

NOW = datetime(2026, 11, 13, 10, 0, 0, 123_456, tzinfo=UTC)
ACME = NewCustomer(
    company_name="Acme Telecom S.L.",
    tax_id="B12345674",
    contact_email="compras@acme.example",
    country="ES",
    plan="business",
)


def _register(session: Session, new: NewCustomer) -> Customer:
    return register_customer(new, CustomerRepository(session), TaxRateRepository(session), NOW)


def _count(session: Session) -> int:
    count: int = session.execute(text("SELECT count(*) FROM customers")).scalar_one()
    return count


def test_register_saves_the_normalized_tax_id_and_the_instant(session: Session) -> None:
    """CA-1.2, CA-1.3: the tax id is stored normalized, with the clock's instant in UTC text."""
    saved = _register(session, dataclasses.replace(ACME, tax_id="b-12.345.674"))

    assert saved == Customer(id=1, created_at="2026-11-13T10:00:00Z", **dataclasses.asdict(ACME))
    assert CustomerRepository(session).get(1) == saved


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        pytest.param({"country": "XX"}, UnsupportedCountryError, id="country-without-rate"),
        pytest.param({"country": "es"}, UnsupportedCountryError, id="country-not-normalized"),
        pytest.param({"tax_id": "12345678A"}, InvalidSpanishTaxIdError, id="spanish-control"),
        pytest.param({"tax_id": "K1234567X"}, UnsupportedTaxIdTypeError, id="klm-type"),
        pytest.param({"tax_id": "1234"}, InvalidTaxIdFormatError, id="basic-format"),
        pytest.param(
            {"country": "PT", "tax_id": "12"}, InvalidTaxIdFormatError, id="basic-format-abroad"
        ),
    ],
)
def test_register_rejects_what_breaks_a_rule_and_saves_nothing(
    session: Session, changes: dict[str, str], error: type[Exception]
) -> None:
    """CA-1.5, CA-2.3, CA-3.2, CA-3.3, CA-3.7: the service does not trust its caller."""
    with pytest.raises(error):
        _register(session, dataclasses.replace(ACME, **changes))

    assert _count(session) == 0


def test_register_accepts_a_spanish_looking_id_abroad(session: Session) -> None:
    """CA-3.8: outside Spain only the basic format applies."""
    saved = _register(session, dataclasses.replace(ACME, country="FR", tax_id="12345678A"))

    assert (saved.country, saved.tax_id) == ("FR", "12345678A")


def test_country_is_unsupported_once_its_rate_is_removed(session: Session) -> None:
    """CA-2.3 (001 CA-4.2): supported countries are exactly the ones with a rate."""
    TaxRateRepository(session).delete("PT")

    with pytest.raises(UnsupportedCountryError):
        _register(session, dataclasses.replace(ACME, country="PT", tax_id="PT123456789"))


@pytest.mark.parametrize(
    "second",
    [
        pytest.param({"tax_id": "12345678Z"}, id="same-text"),
        pytest.param({"tax_id": "12.345.678-z"}, id="another-format"),
        pytest.param({"tax_id": "12345678z", "country": "FR"}, id="another-country"),
    ],
)
def test_register_rejects_a_tax_id_already_in_use(session: Session, second: dict[str, str]) -> None:
    """CA-4.1, CA-4.2: identifiers are compared normalized, whatever the country."""
    _register(session, dataclasses.replace(ACME, tax_id="12345678Z"))

    with pytest.raises(DuplicateTaxIdError):
        _register(session, dataclasses.replace(ACME, company_name="Otra", **second))

    assert _count(session) == 1


@pytest.fixture
def six_customers(session: Session) -> CustomerRepository:
    for company_name, tax_id, country in TABLE_6_6_CUSTOMERS:
        new = dataclasses.replace(ACME, company_name=company_name, tax_id=tax_id, country=country)
        _register(session, new)
    return CustomerRepository(session)


@pytest.mark.parametrize(
    ("q", "ids"),
    [
        pytest.param("", ALL_BY_NAME, id="empty"),
        pytest.param("   ", ALL_BY_NAME, id="only-spaces"),
        pytest.param("ACME", [6, 2], id="name-in-capitals"),
        pytest.param("  acme   telecom ", [2], id="extra-spaces"),
        pytest.param("COMPAÑÍA ñ", [3], id="non-ascii-letters"),
        pytest.param("12.345.678-z", [3], id="tax-id-with-separators"),
        pytest.param("b1234", [2], id="tax-id-in-lowercase"),
        pytest.param("...", [], id="only-separators-match-nothing"),
    ],
)
def test_search_prepares_the_text_for_names_and_tax_ids(
    six_customers: CustomerRepository, q: str, ids: list[int]
) -> None:
    """CA-5.2, CA-5.3: no text lists everybody; otherwise name or normalized tax id."""
    page = search_customers(q, 50, 0, six_customers)

    assert [customer.id for customer in page.items] == ids
    assert page.total == len(ids)


def test_search_passes_the_page_on(six_customers: CustomerRepository) -> None:
    """CA-5.6, CA-5.7: limit and offset cut the page, not the total."""
    page = search_customers("", 2, 4, six_customers)

    assert ([customer.id for customer in page.items], page.total) == ([4, 1], 6)


def test_get_customer_returns_it_or_raises(session: Session) -> None:
    """CA-6.1, CA-6.2: an unknown id is a domain error, not None."""
    saved = _register(session, ACME)
    customers = CustomerRepository(session)

    assert get_customer(1, customers) == saved
    with pytest.raises(CustomerNotFoundError):
        get_customer(2, customers)
