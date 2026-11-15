"""Domain errors for pricing and tax.

They carry no user-facing text on purpose: the API layer (spec 002) maps each one to its
Spanish message in a single place.
"""


class PricingError(Exception):
    """Base class for every pricing rule violation."""


class InvalidUsersError(PricingError):
    """``users`` is not an integer between 0 and MAX_USERS (CA-3.3, CA-3.4)."""


class UnsupportedCountryError(PricingError):
    """The country has no configured tax rate (CA-4.6)."""

    def __init__(self, country: str) -> None:
        super().__init__(country)
        self.country = country


class InvalidTaxRateError(PricingError):
    """``rate_bp`` is not an integer between 0 and 10000 (CA-13.1)."""
