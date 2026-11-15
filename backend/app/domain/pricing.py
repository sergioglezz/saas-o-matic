"""Cumulative tiered pricing (spec 001 RF-1, RF-2). Pure domain: standard library only."""

from dataclasses import dataclass

MAX_USERS = 100_000


@dataclass(frozen=True, slots=True)
class Tier:
    number: int
    from_users: int
    to_users: int | None
    unit_price_cents: int


@dataclass(frozen=True, slots=True)
class TierLine:
    tier: int
    from_users: int
    to_users: int | None
    units: int
    unit_price_cents: int
    amount_cents: int


TIERS: tuple[Tier, ...] = (
    Tier(number=1, from_users=1, to_users=10, unit_price_cents=1000),
    Tier(number=2, from_users=11, to_users=50, unit_price_cents=800),
    Tier(number=3, from_users=51, to_users=None, unit_price_cents=500),
)


def tier_breakdown(users: int) -> tuple[TierLine, ...]:
    """Split ``users`` across TIERS; each tier charges only the users that fall inside it.

    Expects a value already accepted by ``validate_users`` (RF-3).
    """
    return tuple(_tier_line(tier, users) for tier in TIERS)


def _tier_line(tier: Tier, users: int) -> TierLine:
    # The open-ended last tier has no upper bound, so it takes everyone above its start.
    upper = tier.to_users if tier.to_users is not None else users
    units = max(0, min(users, upper) - (tier.from_users - 1))
    return TierLine(
        tier=tier.number,
        from_users=tier.from_users,
        to_users=tier.to_users,
        units=units,
        unit_price_cents=tier.unit_price_cents,
        amount_cents=units * tier.unit_price_cents,
    )
