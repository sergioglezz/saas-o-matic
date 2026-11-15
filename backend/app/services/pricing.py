"""Pricing use cases: join the pure calculation with the configured tax rates (plan sections 2, 5).

This is the public entry point that spec 002 (quote endpoint) and the simulations spec consume.
"""

from typing import Protocol

from app.domain.errors import UnsupportedCountryError
from app.domain.pricing import PriceQuote, build_quote, validate_users
from app.domain.tax import validate_rate_bp
from app.repositories.tax_rates import TaxRateRepository


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


def country_is_supported(country: str, rates: TaxRateSource) -> bool:
    """True when the exact code ``country`` has a configured tax rate (001 CA-4.2).

    Lets the API report "país no soportado" together with other field errors (spec 002 E-35),
    which ``quote`` cannot do because it stops at the users error first.
    """
    return rates.get_rate_bp(country) is not None


def set_tax_rate(country: str, rate_bp: int, repository: TaxRateRepository) -> None:
    """Configure the tax rate of ``country`` (CA-13.1, CA-13.2).

    The rate is validated before touching the database, so an invalid value raises
    InvalidTaxRateError and leaves the previous rate untouched. The caller commits.
    """
    repository.upsert(country, validate_rate_bp(rate_bp))
