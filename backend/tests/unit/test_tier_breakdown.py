"""Tiered pricing breakdown, spec 001 table 6.1 (P-1 to P-10).

Covers CA-1.1, CA-1.2, CA-1.3, CA-1.4 and CA-2.1 to CA-2.4.
"""

import pytest

from app.domain.pricing import TIERS, tier_breakdown

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

TABLE_PARAMS = [
    pytest.param(users, tiers, subtotal, id=case_id)
    for case_id, users, tiers, subtotal in TABLE_6_1
]
USERS_PARAMS = [pytest.param(users, id=case_id) for case_id, users, _, _ in TABLE_6_1]


@pytest.mark.parametrize(("users", "expected_tiers", "expected_subtotal"), TABLE_PARAMS)
def test_breakdown_matches_table_6_1(
    users: int,
    expected_tiers: tuple[tuple[int, int], ...],
    expected_subtotal: int,
) -> None:
    """CA-1.1, CA-1.3: units and amount of each tier and the subtotal match table 6.1."""
    lines = tier_breakdown(users)

    assert tuple((line.units, line.amount_cents) for line in lines) == expected_tiers
    assert sum(line.amount_cents for line in lines) == expected_subtotal


@pytest.mark.parametrize("users", USERS_PARAMS)
def test_breakdown_always_has_three_ordered_tiers_with_fixed_bounds(users: int) -> None:
    """CA-2.1, CA-2.2: always 3 tiers, ordered, with bounds 1/10, 11/50 and 51/open."""
    lines = tier_breakdown(users)

    assert [line.tier for line in lines] == [1, 2, 3]
    assert [(line.from_users, line.to_users) for line in lines] == [(1, 10), (11, 50), (51, None)]


@pytest.mark.parametrize("users", USERS_PARAMS)
def test_breakdown_amounts_are_exact_integer_products(users: int) -> None:
    """CA-1.4, CA-2.3: amount = units x unit price, as exact integers with no rounding."""
    for line in tier_breakdown(users):
        assert type(line.units) is int
        assert type(line.amount_cents) is int
        assert line.amount_cents == line.units * line.unit_price_cents


@pytest.mark.parametrize("users", USERS_PARAMS)
def test_breakdown_units_add_up_to_users(users: int) -> None:
    """CA-2.4: the units of the 3 tiers add up to the number of users."""
    assert sum(line.units for line in tier_breakdown(users)) == users


def test_unit_prices_per_tier() -> None:
    """CA-1.1: tier 1 charges 1000 cents per user, tier 2 charges 800 and tier 3 charges 500."""
    assert [tier.unit_price_cents for tier in TIERS] == [1000, 800, 500]


def test_sixty_users_is_cumulative_not_volume_pricing() -> None:
    """CA-1.2: 60 users cost 47000 cents (cumulative tiers), not 60 x 500 = 30000."""
    assert sum(line.amount_cents for line in tier_breakdown(60)) == 47000
