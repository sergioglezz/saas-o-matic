"""Pricing use cases: join the pure calculation with the configured tax rates (plan sections 2, 5).

This is the public entry point that spec 002 (quote endpoint) and the simulations spec consume.
"""

from typing import Protocol

from app.domain.errors import UnsupportedCountryError
from app.domain.pricing import PriceQuote, build_quote, validate_users


class TaxRateSource(Protocol):
    """Anything that returns the rate of an exact country code, or None if it has none."""

    def get_rate_bp(self, country: str) -> int | None: ...


def quote(users: int, country: str, rates: TaxRateSource) -> PriceQuote:
    """Monthly quote for ``users`` in ``country``, with the country's configured tax rate.

    ``country`` must already be normalised by the caller: it is looked up exactly (CA-4.7).
    Raises InvalidUsersError or UnsupportedCountryError; nothing is calculated in that case.
    """
    # Users first: when both inputs are wrong the users error wins (CA-3.5).
    valid_users = validate_users(users)
    # A single read, so the whole quote uses one consistent rate (CA-13.3).
    rate_bp = rates.get_rate_bp(country)
    if rate_bp is None:
        raise UnsupportedCountryError(country)
    return build_quote(valid_users, rate_bp)
