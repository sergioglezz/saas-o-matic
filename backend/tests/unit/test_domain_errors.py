"""Domain error hierarchy from plan section 4: every pricing error derives from PricingError."""

import pytest

from app.domain.errors import (
    InvalidTaxRateError,
    InvalidUsersError,
    PricingError,
    UnsupportedCountryError,
)


@pytest.mark.parametrize(
    "error_type", [InvalidUsersError, UnsupportedCountryError, InvalidTaxRateError]
)
def test_domain_errors_share_a_common_base(error_type: type[Exception]) -> None:
    assert issubclass(error_type, PricingError)


def test_unsupported_country_error_keeps_the_country() -> None:
    """CA-4.6: the error says which country has no configured rate."""
    assert UnsupportedCountryError("XX").country == "XX"
