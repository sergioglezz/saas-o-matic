"""Full calculation result, spec 001 RF-4 (with the rate given), RF-6 and RF-7.

Covers CA-4.4, CA-4.5, CA-6.3 and CA-7.1 to CA-7.3 with tables 6.2 (T-1 to T-10, rate from
its column) and 6.3 (R-1 to R-9), plus the example of spec section 5.
"""

import dataclasses

import pytest

from app.domain.errors import InvalidTaxRateError, InvalidUsersError
from app.domain.pricing import PriceQuote, TierLine, build_quote

# (case id, users, tax_rate_bp, subtotal_cents, tax_cents, total_cents)
TABLE_6_2: list[tuple[str, int, int, int, int, int]] = [
    ("T-1", 0, 2100, 0, 0, 0),
    ("T-2", 1, 2300, 1000, 230, 1230),
    ("T-3", 11, 1900, 10800, 2052, 12852),
    ("T-4", 15, 2100, 14000, 2940, 16940),
    ("T-5", 15, 0, 14000, 0, 14000),
    ("T-6", 51, 2000, 42500, 8500, 51000),
    ("T-7", 60, 2100, 47000, 9870, 56870),
    ("T-8", 100, 2000, 67000, 13400, 80400),
    ("T-9", 10, 2200, 10000, 2200, 12200),
    ("T-10", 100000, 2100, 50017000, 10503570, 60520570),
]

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

QUOTE_PARAMS = [
    pytest.param(users, rate, subtotal, tax, total, id=case_id)
    for case_id, users, rate, subtotal, tax, total in TABLE_6_2 + TABLE_6_3
]


@pytest.mark.parametrize(("users", "rate_bp", "subtotal", "tax", "total"), QUOTE_PARAMS)
def test_quote_amounts_match_tables_6_2_and_6_3(
    users: int, rate_bp: int, subtotal: int, tax: int, total: int
) -> None:
    """CA-4.4, CA-4.5, CA-6.3, CA-7.3: subtotal, rate, tax and total match the tables."""
    quote = build_quote(users, rate_bp)

    assert quote.users == users
    assert quote.subtotal_cents == subtotal
    assert quote.tax_rate_bp == rate_bp
    assert quote.tax_cents == tax
    assert quote.total_cents == total
    assert quote.total_cents == quote.subtotal_cents + quote.tax_cents


@pytest.mark.parametrize(("users", "rate_bp", "subtotal", "tax", "total"), QUOTE_PARAMS)
def test_quote_amounts_are_integers_in_eur(
    users: int, rate_bp: int, subtotal: int, tax: int, total: int
) -> None:
    """CA-7.1, CA-7.2: every amount and rate is a plain int and the currency is EUR."""
    quote = build_quote(users, rate_bp)

    assert quote.currency == "EUR"
    for field in ("users", "subtotal_cents", "tax_rate_bp", "tax_cents", "total_cents"):
        assert type(getattr(quote, field)) is int, field


def test_fifteen_users_in_spain_matches_spec_section_5_field_by_field() -> None:
    """Spec section 5 example: users = 15, country = ES (rate 2100 bp)."""
    expected = PriceQuote(
        users=15,
        currency="EUR",
        tiers=(
            TierLine(
                tier=1,
                from_users=1,
                to_users=10,
                units=10,
                unit_price_cents=1000,
                amount_cents=10000,
            ),
            TierLine(
                tier=2,
                from_users=11,
                to_users=50,
                units=5,
                unit_price_cents=800,
                amount_cents=4000,
            ),
            TierLine(
                tier=3,
                from_users=51,
                to_users=None,
                units=0,
                unit_price_cents=500,
                amount_cents=0,
            ),
        ),
        subtotal_cents=14000,
        tax_rate_bp=2100,
        tax_cents=2940,
        total_cents=16940,
    )

    assert dataclasses.asdict(build_quote(15, 2100)) == dataclasses.asdict(expected)


def test_rejects_invalid_users_before_calculating() -> None:
    """CA-3.3: an invalid number of users produces no result."""
    with pytest.raises(InvalidUsersError):
        build_quote(-1, 2100)


def test_rejects_invalid_rate_before_calculating() -> None:
    """CA-13.1: an invalid tax rate produces no result."""
    with pytest.raises(InvalidTaxRateError):
        build_quote(15, 10_001)
