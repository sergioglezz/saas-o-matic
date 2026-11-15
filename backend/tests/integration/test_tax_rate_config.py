"""Tax rate configuration through the service (level D), spec 001 task T-11.

Covers CA-13.1 and CA-13.2 with table 6.4 (C-1 to C-5) and table 6.3 (R-1 to R-9) at level D.
"""

import pytest
from sqlalchemy.orm import Session

from app.domain.errors import InvalidTaxRateError, UnsupportedCountryError
from app.repositories.tax_rates import TaxRateRepository
from app.services.pricing import quote, set_tax_rate

# (case id, users, tax_rate_bp configured for ES, subtotal_cents, tax_cents, total_cents)
TABLE_6_3: list[tuple[str, int, int, int, int, int]] = [
    ("R-1", 1, 2105, 1000, 211, 1211),
    ("R-2", 1, 2104, 1000, 210, 1210),
    ("R-3", 1, 2106, 1000, 211, 1211),
    ("R-4", 1, 5, 1000, 1, 1001),
    ("R-5", 1, 4, 1000, 0, 1000),
    ("R-6", 1, 1, 1000, 0, 1000),
    ("R-7", 100000, 2105, 50017000, 10528579, 60545579),
    ("R-8", 15, 10000, 14000, 14000, 28000),
    ("R-9", 11, 0, 10800, 0, 10800),
]


@pytest.fixture
def repository(session: Session) -> TaxRateRepository:
    return TaxRateRepository(session)


@pytest.mark.parametrize(
    "rate_bp",
    [
        pytest.param(10_001, id="C-1"),
        pytest.param(-1, id="C-2"),
        pytest.param(True, id="bool"),
    ],
)
def test_invalid_rate_is_rejected_and_the_previous_one_is_kept(
    repository: TaxRateRepository, rate_bp: int
) -> None:
    """C-1, C-2, CA-13.1: rejected before touching the database; ES keeps 2100."""
    with pytest.raises(InvalidTaxRateError):
        set_tax_rate("ES", rate_bp, repository)

    assert repository.get_rate_bp("ES") == 2100
    assert quote(15, "ES", repository).tax_cents == 2940


def test_rates_at_both_ends_of_the_range_are_accepted(repository: TaxRateRepository) -> None:
    """C-3, CA-13.1: 10000 bp and then 0 bp are both accepted."""
    set_tax_rate("ES", 10_000, repository)
    assert repository.get_rate_bp("ES") == 10_000

    set_tax_rate("ES", 0, repository)
    assert repository.get_rate_bp("ES") == 0


def test_country_whose_rate_was_removed_is_no_longer_supported(
    repository: TaxRateRepository,
) -> None:
    """C-4, CA-4.6: after removing PT's rate, quoting PT raises UnsupportedCountryError."""
    repository.delete("PT")

    with pytest.raises(UnsupportedCountryError):
        quote(1, "PT", repository)


def test_rate_change_applies_to_the_next_quote(repository: TaxRateRepository) -> None:
    """C-5, CA-13.2: the new rate is used from the next quote on, with the same calculation."""
    assert quote(15, "ES", repository).tax_cents == 2940

    set_tax_rate("ES", 2200, repository)
    after = quote(15, "ES", repository)

    assert (after.tax_rate_bp, after.tax_cents, after.total_cents) == (2200, 3080, 17080)


@pytest.mark.parametrize(
    ("users", "rate_bp", "subtotal", "tax", "total"),
    [pytest.param(*row[1:], id=row[0]) for row in TABLE_6_3],
)
def test_rounding_with_a_configured_rate_matches_table_6_3(
    repository: TaxRateRepository, users: int, rate_bp: int, subtotal: int, tax: int, total: int
) -> None:
    """R-1 to R-9 at level D: ES is set to the rate of the row, then quoted."""
    set_tax_rate("ES", rate_bp, repository)

    result = quote(users, "ES", repository)

    assert (result.subtotal_cents, result.tax_rate_bp) == (subtotal, rate_bp)
    assert (result.tax_cents, result.total_cents) == (tax, total)
