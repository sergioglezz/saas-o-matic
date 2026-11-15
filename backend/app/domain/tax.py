"""Tax on the subtotal (spec 001 RF-6) and tax rate range (RF-13). Pure domain."""

from app.domain.errors import InvalidTaxRateError

FULL_RATE_BP = 10_000  # 10000 basis points = 100 %


def validate_rate_bp(rate_bp: int) -> int:
    """Return ``rate_bp`` if it is an integer between 0 and 10000 bp, both included (CA-13.1).

    Raises InvalidTaxRateError otherwise.
    """
    # bool is a subclass of int, so isinstance() would accept True as 1.
    if type(rate_bp) is not int or not 0 <= rate_bp <= FULL_RATE_BP:
        raise InvalidTaxRateError(rate_bp)
    return rate_bp


def tax_cents(subtotal_cents: int, rate_bp: int) -> int:
    """Tax in cents, rounded once to the nearest cent with halves going up (CA-6.1, CA-6.2).

    Adding half of the divisor before the integer division rounds 0.5 up without floats.
    Python's round() would not do: it rounds halves to even (210.5 -> 210, which breaks R-1).
    Valid because the subtotal and the rate are never negative.
    """
    return (subtotal_cents * rate_bp + FULL_RATE_BP // 2) // FULL_RATE_BP
