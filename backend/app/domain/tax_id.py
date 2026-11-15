"""Tax identifier rules (spec 003 RF-3, ADR 0009). Pure domain: standard library only."""

import re

from app.domain.errors import (
    InvalidSpanishTaxIdError,
    InvalidTaxIdFormatError,
    UnsupportedTaxIdTypeError,
)

SPAIN = "ES"

# Separators people type inside an identifier (CA-3.1); they are removed anywhere, and only
# a-z are uppercased, so a letter such as "ß" is never turned into valid-looking ASCII.
_NORMALIZATION = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", " \t\n\r-."
)
_BASIC_FORMAT = re.compile(r"[A-Z0-9]{5,20}")

# [0-9] and not \d: \d also matches digits of other alphabets.
_DNI = re.compile(r"[0-9]{8}[A-Z]")
_NIE = re.compile(r"[XYZ][0-9]{7}[A-Z]")
_CIF = re.compile(r"[ABCDEFGHJNPQRSUVW][0-9]{7}[0-9A-J]")
_DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_NIE_PREFIX_DIGIT = {"X": "0", "Y": "1", "Z": "2"}
_CIF_CONTROL_LETTERS = "JABCDEFGHI"
# The AEAT does not publish which entities take a letter or a digit; this is the most
# widespread convention among validators (ADR 0009).
_CIF_LETTER_ONLY = frozenset("NPQRSW")
_CIF_DIGIT_ONLY = frozenset("ABEH")
# Special NIF types without a published control method (ADR 0009).
_UNSUPPORTED_PREFIXES = frozenset("KLM")


def normalize_tax_id(value: str) -> str:
    """``value`` in uppercase and without spaces, hyphens or dots (CA-3.1, RN-11)."""
    return value.translate(_NORMALIZATION)


def validate_tax_id(value: str, country: str | None) -> str:
    """The normalized tax id, once it passes the rules of ``country`` (RF-3).

    Every country gets the basic format (CA-3.2); Spain also gets the control character
    (CA-3.3). ``country`` is None when the caller has no valid country: only the basic format
    applies then (CA-3.9).
    Raises InvalidTaxIdFormatError, UnsupportedTaxIdTypeError or InvalidSpanishTaxIdError.
    """
    tax_id = normalize_tax_id(value)
    if not _BASIC_FORMAT.fullmatch(tax_id):
        raise InvalidTaxIdFormatError(tax_id)
    if country != SPAIN:
        return tax_id
    if tax_id[0] in _UNSUPPORTED_PREFIXES:
        raise UnsupportedTaxIdTypeError(tax_id)
    if not (_is_valid_dni(tax_id) or _is_valid_nie(tax_id) or _is_valid_cif(tax_id)):
        raise InvalidSpanishTaxIdError(tax_id)
    return tax_id


def _is_valid_dni(tax_id: str) -> bool:
    """8 digits and the letter at position (number mod 23) of the official table (CA-3.4)."""
    return bool(_DNI.fullmatch(tax_id)) and tax_id[8] == _DNI_LETTERS[int(tax_id[:8]) % 23]


def _is_valid_nie(tax_id: str) -> bool:
    """X, Y or Z counts as 0, 1 or 2 and the rest is the DNI calculation (CA-3.5)."""
    if not _NIE.fullmatch(tax_id):
        return False
    return _is_valid_dni(_NIE_PREFIX_DIGIT[tax_id[0]] + tax_id[1:])


def _is_valid_cif(tax_id: str) -> bool:
    """Entity letter, 7 digits and the control the entity requires (CA-3.6)."""
    if not _CIF.fullmatch(tax_id):
        return False
    entity, control = tax_id[0], tax_id[8]
    digit = _cif_control_digit(tax_id[1:8])
    as_digit, as_letter = str(digit), _CIF_CONTROL_LETTERS[digit]
    if entity in _CIF_LETTER_ONLY:
        return control == as_letter
    if entity in _CIF_DIGIT_ONLY:
        return control == as_digit
    return control in (as_digit, as_letter)


def _cif_control_digit(digits: str) -> int:
    """(10 - (A + B) mod 10) mod 10 over the 7 digits of a CIF.

    A adds the digits in even positions; B adds, for the digits in odd positions, the figures
    of their double (7 -> 14 -> 1 + 4).
    """
    even_sum = sum(int(digit) for digit in digits[1::2])
    odd_sum = sum(sum(divmod(int(digit) * 2, 10)) for digit in digits[0::2])
    return (10 - (even_sum + odd_sum) % 10) % 10
