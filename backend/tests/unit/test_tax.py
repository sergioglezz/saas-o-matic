"""Tax rounding and tax rate range, spec 001 RF-6 and the domain part of RF-13.

Covers CA-6.1, CA-6.2, CA-6.3 (table 6.3, R-1 to R-9) and CA-13.1.
"""

import pytest

from app.domain.errors import InvalidTaxRateError
from app.domain.tax import tax_cents, validate_rate_bp

# (case id, subtotal_cents, tax_rate_bp, expected tax_cents)
TABLE_6_3: list[tuple[str, int, int, int]] = [
    ("R-1", 1000, 2105, 211),
    ("R-2", 1000, 2104, 210),
    ("R-3", 1000, 2106, 211),
    ("R-4", 1000, 5, 1),
    ("R-5", 1000, 4, 0),
    ("R-6", 1000, 1, 0),
    ("R-7", 50017000, 2105, 10528579),
    ("R-8", 14000, 10000, 14000),
    ("R-9", 10800, 0, 0),
]


@pytest.mark.parametrize(
    ("subtotal", "rate_bp", "expected"),
    [pytest.param(s, r, t, id=case_id) for case_id, s, r, t in TABLE_6_3],
)
def test_tax_matches_table_6_3(subtotal: int, rate_bp: int, expected: int) -> None:
    """CA-6.1, CA-6.2, CA-6.3: one rounding to the cent, halves go up."""
    result = tax_cents(subtotal, rate_bp)

    assert result == expected
    assert type(result) is int


@pytest.mark.parametrize("rate_bp", [pytest.param(0, id="min-0"), pytest.param(10_000, id="max")])
def test_accepts_rates_at_both_ends_of_the_range(rate_bp: int) -> None:
    """CA-13.1: 0 and 10000 bp are valid and are returned unchanged."""
    assert validate_rate_bp(rate_bp) == rate_bp


@pytest.mark.parametrize(
    "rate_bp",
    [
        pytest.param(-1, id="negative"),
        pytest.param(10_001, id="above-100-percent"),
        pytest.param(True, id="bool"),
        pytest.param(2100.0, id="float"),
    ],
)
def test_rejects_invalid_rates(rate_bp: object) -> None:
    """CA-13.1: outside 0..10000 or not a plain integer raises InvalidTaxRateError."""
    with pytest.raises(InvalidTaxRateError):
        validate_rate_bp(rate_bp)  # type: ignore[arg-type]  # wrong type on purpose: runtime guard
