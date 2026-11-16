"""Customer types (spec 003 RF-1, RF-5). Pure domain: standard library only."""

from dataclasses import dataclass

# The plan never changes a price (CA-2.4); it is only recorded.
PLANS: tuple[str, ...] = ("starter", "business", "enterprise")
# A customer id is a positive integer up to the largest one SQLite can hold (003 CA-6.3,
# 004 CA-2.1).
MAX_CUSTOMER_ID = 2**63 - 1


@dataclass(frozen=True, slots=True)
class NewCustomer:
    """A customer about to be registered, with its fields already normalized."""

    company_name: str
    tax_id: str
    contact_email: str
    country: str
    plan: str


@dataclass(frozen=True, slots=True)
class Customer:
    """A registered customer; field names match the contract of spec 003 section 5."""

    id: int
    company_name: str
    tax_id: str
    contact_email: str
    country: str
    plan: str
    created_at: str  # ISO 8601 UTC text, e.g. 2026-11-13T10:00:00Z (CA-1.3)


@dataclass(frozen=True, slots=True)
class CustomerPage:
    """One page of a search and the number of customers that match it (CA-5.7)."""

    items: tuple[Customer, ...]
    total: int
