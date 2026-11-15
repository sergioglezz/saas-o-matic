"""Customer use cases: register, search and read (spec 003 RF-1, RF-4, RF-5, RF-6).

They enforce the business rules by themselves, whoever calls them: the API, the seed or a
future spec (plan 003 DT-2).
"""

import dataclasses
from datetime import datetime
from typing import Protocol

from app.core.clock import to_timestamp
from app.domain.customers import Customer, CustomerPage, NewCustomer
from app.domain.errors import CustomerNotFoundError, UnsupportedCountryError
from app.domain.tax_id import normalize_tax_id, validate_tax_id
from app.services.pricing import TaxRateSource, country_is_supported


class CustomerStore(Protocol):
    """Where customers are kept; the repository implements it."""

    def add(self, new: NewCustomer, created_at: str) -> Customer: ...

    def get(self, customer_id: int) -> Customer | None: ...

    def search(
        self, name_fragment: str, tax_id_fragment: str, limit: int, offset: int
    ) -> CustomerPage: ...


def register_customer(
    new: NewCustomer, customers: CustomerStore, rates: TaxRateSource, now: datetime
) -> Customer:
    """Register ``new`` at instant ``now`` and return it with its id (RF-1).

    ``new.country`` must already be normalised: it is looked up exactly (001 CA-4.7).
    Raises UnsupportedCountryError, a tax id error (RF-3) or DuplicateTaxIdError; nothing is
    saved in that case (CA-1.5).
    """
    if not country_is_supported(new.country, rates):
        raise UnsupportedCountryError(new.country)
    tax_id = validate_tax_id(new.tax_id, new.country)
    return customers.add(dataclasses.replace(new, tax_id=tax_id), to_timestamp(now))


def search_customers(q: str, limit: int, offset: int, customers: CustomerStore) -> CustomerPage:
    """Customers whose name or tax id contains ``q``; every customer when it is blank (RF-5).

    The same text is tried both ways: as part of a name, ignoring case, and as part of a tax
    id, normalized like one, so "12.345.678-z" finds 12345678Z (CA-5.3).
    """
    text = " ".join(q.split())
    return customers.search(text.casefold(), normalize_tax_id(text), limit, offset)


def get_customer(customer_id: int, customers: CustomerStore) -> Customer:
    """The customer with that id. Raises CustomerNotFoundError (CA-6.2)."""
    customer = customers.get(customer_id)
    if customer is None:
        raise CustomerNotFoundError(customer_id)
    return customer
