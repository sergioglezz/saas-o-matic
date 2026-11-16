"""Simulation types and usage rules (spec 004 RF-2, RF-4, RF-5). Pure domain: standard library only.

A simulation stores a snapshot of the calculation of spec 001; nothing here calculates a price.
"""

from dataclasses import dataclass

from app.domain.errors import InvalidApiCallsError, InvalidStorageError
from app.domain.pricing import TierLine

# Upper bounds chosen in spec 004 decision D-5: they reject absurd values and anything SQLite
# could not store. Storage and API calls never change a price (RN-9).
MAX_STORAGE_GB = 1_000_000
MAX_API_CALLS_PER_MONTH = 1_000_000_000


@dataclass(frozen=True, slots=True)
class NewSimulation:
    """A simulation about to be saved: the four input fields of CA-2.1 to CA-2.4."""

    customer_id: int
    active_users: int
    storage_gb: int
    api_calls_per_month: int


@dataclass(frozen=True, slots=True)
class Simulation:
    """A saved simulation; field names and order match the contract of spec 004 section 5.

    The quote's ``users`` is left out: it would repeat ``active_users`` (spec decision D-2).
    """

    id: int
    customer_id: int
    active_users: int
    storage_gb: int
    api_calls_per_month: int
    currency: str
    tiers: tuple[TierLine, ...]
    subtotal_cents: int
    tax_rate_bp: int
    tax_cents: int
    total_cents: int
    created_at: str  # ISO 8601 UTC text, e.g. 2026-11-16T10:00:00Z (CA-1.2)


@dataclass(frozen=True, slots=True)
class SimulationPage:
    """One page of a customer's history and how many simulations it has (CA-5.3)."""

    items: tuple[Simulation, ...]
    total: int


def validate_usage(storage_gb: int, api_calls_per_month: int) -> None:
    """Check storage and API calls; storage first (CA-2.3, CA-2.4).

    Raises InvalidStorageError or InvalidApiCallsError. The service calls it whoever the
    caller is, so the seed follows the same rules as the API (plan 004 DT-2).
    """
    if not _is_integer_between(storage_gb, MAX_STORAGE_GB):
        raise InvalidStorageError(storage_gb)
    if not _is_integer_between(api_calls_per_month, MAX_API_CALLS_PER_MONTH):
        raise InvalidApiCallsError(api_calls_per_month)


def _is_integer_between(value: int, maximum: int) -> bool:
    # bool is a subclass of int, so isinstance() would accept True as 1 (as in validate_users).
    return type(value) is int and 0 <= value <= maximum
