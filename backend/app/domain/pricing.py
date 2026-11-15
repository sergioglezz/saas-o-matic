"""Cumulative tiered pricing and full quote (spec 001 RF-1 to RF-4, RF-6, RF-7).

Pure domain: standard library only.
"""

from dataclasses import dataclass

from app.domain.errors import InvalidUsersError
from app.domain.tax import tax_cents, validate_rate_bp

MAX_USERS = 100_000
BASE_CURRENCY = "EUR"


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


@dataclass(frozen=True, slots=True)
class PriceQuote:
    """Monthly quote; field names match the observable contract of spec 001 section 5."""

    users: int
    currency: str
    tiers: tuple[TierLine, ...]
    subtotal_cents: int
    tax_rate_bp: int
    tax_cents: int
    total_cents: int


TIERS: tuple[Tier, ...] = (
    Tier(number=1, from_users=1, to_users=10, unit_price_cents=1000),
    Tier(number=2, from_users=11, to_users=50, unit_price_cents=800),
    Tier(number=3, from_users=51, to_users=None, unit_price_cents=500),
)


def validate_users(users: int) -> int:
    """Return ``users`` if it is an integer between 0 and MAX_USERS, both included (RF-3).

    Raises InvalidUsersError otherwise.
    """
    # bool is a subclass of int, so isinstance() would accept True as 1 (CA-3.4).
    if type(users) is not int or not 0 <= users <= MAX_USERS:
        raise InvalidUsersError(users)
    return users


def build_quote(users: int, rate_bp: int) -> PriceQuote:
    """Full monthly quote for ``users`` with the tax rate already resolved by the caller.

    Raises InvalidUsersError or InvalidTaxRateError before calculating anything.
    """
    valid_users = validate_users(users)
    valid_rate_bp = validate_rate_bp(rate_bp)
    tiers = tier_breakdown(valid_users)
    subtotal = sum(line.amount_cents for line in tiers)
    tax = tax_cents(subtotal, valid_rate_bp)
    return PriceQuote(
        users=valid_users,
        currency=BASE_CURRENCY,
        tiers=tiers,
        subtotal_cents=subtotal,
        tax_rate_bp=valid_rate_bp,
        tax_cents=tax,
        total_cents=subtotal + tax,
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
