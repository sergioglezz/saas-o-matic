"""Tax identifier rules (spec 003 RF-3, ADR 0009). Pure domain: standard library only."""

import re

from app.domain.errors import InvalidTaxIdFormatError

# Separators people type inside an identifier (CA-3.1); they are removed anywhere, and only
# a-z are uppercased, so a letter such as "ß" is never turned into valid-looking ASCII.
_NORMALIZATION = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", " \t\n\r-."
)
_BASIC_FORMAT = re.compile(r"[A-Z0-9]{5,20}")


def normalize_tax_id(value: str) -> str:
    """``value`` in uppercase and without spaces, hyphens or dots (CA-3.1, RN-11)."""
    return value.translate(_NORMALIZATION)


def validate_tax_id(value: str, country: str | None) -> str:
    """The normalized tax id, once it passes the rules of ``country`` (RF-3).

    Every country gets the basic format (CA-3.2). ``country`` is None when the caller has no
    valid country: only the basic format applies then (CA-3.9).
    Raises InvalidTaxIdFormatError.
    """
    tax_id = normalize_tax_id(value)
    if not _BASIC_FORMAT.fullmatch(tax_id):
        raise InvalidTaxIdFormatError(tax_id)
    return tax_id
