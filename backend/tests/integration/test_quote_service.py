"""Quote service against the migrated database (level D), spec 001 task T-10.

Covers CA-3.5, CA-4.1, CA-4.6, CA-4.7 and CA-13.3 with tables 6.1 (P-1 to P-10, country US),
6.2 (T-1 to T-10), 6.5 (X-1, X-2, X-4 to X-7) and the example of spec section 5.
"""

import dataclasses

import pytest
from sqlalchemy.orm import Session

from app.domain.errors import InvalidUsersError, UnsupportedCountryError
from app.domain.pricing import PriceQuote, TierLine
from app.repositories.tax_rates import TaxRateRepository
from app.services.pricing import TaxRateSource, quote

# (case id, users, (units, amount_cents) for tiers 1..3, subtotal_cents)
TABLE_6_1: list[tuple[str, int, tuple[tuple[int, int], ...], int]] = [
    ("P-1", 0, ((0, 0), (0, 0), (0, 0)), 0),
    ("P-2", 1, ((1, 1000), (0, 0), (0, 0)), 1000),
    ("P-3", 10, ((10, 10000), (0, 0), (0, 0)), 10000),
    ("P-4", 11, ((10, 10000), (1, 800), (0, 0)), 10800),
    ("P-5", 15, ((10, 10000), (5, 4000), (0, 0)), 14000),
    ("P-6", 50, ((10, 10000), (40, 32000), (0, 0)), 42000),
    ("P-7", 51, ((10, 10000), (40, 32000), (1, 500)), 42500),
    ("P-8", 60, ((10, 10000), (40, 32000), (10, 5000)), 47000),
    ("P-9", 100, ((10, 10000), (40, 32000), (50, 25000)), 67000),
    ("P-10", 100000, ((10, 10000), (40, 32000), (99950, 49975000)), 50017000),
]

# (case id, users, country, subtotal_cents, tax_rate_bp, tax_cents, total_cents)
TABLE_6_2: list[tuple[str, int, str, int, int, int, int]] = [
    ("T-1", 0, "ES", 0, 2100, 0, 0),
    ("T-2", 1, "PT", 1000, 2300, 230, 1230),
    ("T-3", 11, "DE", 10800, 1900, 2052, 12852),
    ("T-4", 15, "ES", 14000, 2100, 2940, 16940),
    ("T-5", 15, "US", 14000, 0, 0, 14000),
    ("T-6", 51, "FR", 42500, 2000, 8500, 51000),
    ("T-7", 60, "ES", 47000, 2100, 9870, 56870),
    ("T-8", 100, "GB", 67000, 2000, 13400, 80400),
    ("T-9", 10, "IT", 10000, 2200, 2200, 12200),
    ("T-10", 100000, "ES", 50017000, 2100, 10503570, 60520570),
]


class CountingRates:
    """Spy around a real rate source that counts how many times the rate is read."""

    def __init__(self, inner: TaxRateSource) -> None:
        self._inner = inner
        self.calls = 0

    def get_rate_bp(self, country: str) -> int | None:
        self.calls += 1
        return self._inner.get_rate_bp(country)


@pytest.fixture
def rates(session: Session) -> TaxRateRepository:
    return TaxRateRepository(session)


@pytest.mark.parametrize(
    ("users", "expected_tiers", "expected_subtotal"),
    [pytest.param(u, tiers, s, id=case_id) for case_id, u, tiers, s in TABLE_6_1],
)
def test_tiers_through_the_service_match_table_6_1(
    rates: TaxRateRepository,
    users: int,
    expected_tiers: tuple[tuple[int, int], ...],
    expected_subtotal: int,
) -> None:
    """P-1 to P-10 at level D with US (rate 0): tiers, subtotal and total equal to subtotal."""
    result = quote(users, "US", rates)

    assert tuple((line.units, line.amount_cents) for line in result.tiers) == expected_tiers
    assert result.subtotal_cents == expected_subtotal
    assert (result.tax_cents, result.total_cents) == (0, expected_subtotal)


@pytest.mark.parametrize(
    ("users", "country", "subtotal", "rate_bp", "tax", "total"),
    [pytest.param(*row[1:], id=row[0]) for row in TABLE_6_2],
)
def test_tax_with_the_default_rates_matches_table_6_2(
    rates: TaxRateRepository,
    users: int,
    country: str,
    subtotal: int,
    rate_bp: int,
    tax: int,
    total: int,
) -> None:
    """CA-4.1: the rate comes from the configured table; T-1 to T-10 with the default rates."""
    result = quote(users, country, rates)

    assert (result.subtotal_cents, result.tax_rate_bp) == (subtotal, rate_bp)
    assert (result.tax_cents, result.total_cents) == (tax, total)


def test_fifteen_users_in_spain_matches_spec_section_5(rates: TaxRateRepository) -> None:
    expected = PriceQuote(
        users=15,
        currency="EUR",
        tiers=(
            TierLine(1, 1, 10, 10, 1000, 10000),
            TierLine(2, 11, 50, 5, 800, 4000),
            TierLine(3, 51, None, 0, 500, 0),
        ),
        subtotal_cents=14000,
        tax_rate_bp=2100,
        tax_cents=2940,
        total_cents=16940,
    )

    assert dataclasses.asdict(quote(15, "ES", rates)) == dataclasses.asdict(expected)


@pytest.mark.parametrize(
    ("users", "country"),
    [
        pytest.param(-1, "ES", id="X-1"),
        pytest.param(100_001, "ES", id="X-2"),
        pytest.param(-1, "XX", id="X-7"),
    ],
)
def test_invalid_users_win_and_the_rate_is_never_read(
    rates: TaxRateRepository, users: int, country: str
) -> None:
    """CA-3.3, CA-3.5: users are checked first, so X-7 reports users and reads no rate."""
    spy = CountingRates(rates)

    with pytest.raises(InvalidUsersError):
        quote(users, country, spy)
    assert spy.calls == 0


@pytest.mark.parametrize(
    "country",
    [
        pytest.param("XX", id="X-4"),
        pytest.param("es", id="X-5"),
        pytest.param("", id="X-6"),
    ],
)
def test_country_without_rate_is_not_supported(rates: TaxRateRepository, country: str) -> None:
    """CA-4.6, CA-4.7: no rate for the exact code means unsupported; it is never normalised."""
    with pytest.raises(UnsupportedCountryError) as error:
        quote(15, country, rates)

    assert error.value.country == country


def test_each_quote_reads_the_rate_exactly_once(rates: TaxRateRepository) -> None:
    """CA-13.3: one quote uses a single rate, read once."""
    spy = CountingRates(rates)

    quote(15, "ES", spy)
    assert spy.calls == 1

    quote(60, "ES", spy)
    assert spy.calls == 2
