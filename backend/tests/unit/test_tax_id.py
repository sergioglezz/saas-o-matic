"""Tax identifier rules (level U), spec 003 RF-3: tables 6.1 and 6.2, ADR 0009.

Pure domain: no database and no web server (RNF-1). Every identifier is synthetic.
"""

import pytest

from app.domain.errors import InvalidTaxIdFormatError
from app.domain.tax_id import normalize_tax_id, validate_tax_id

# (case id, input, country, normalized value, or None when the basic format rejects it)
TABLE_6_2: list[tuple[str, str, str, str | None]] = [
    ("TG-1", "PT123456789", "PT", "PT123456789"),
    ("TG-2", "1234", "PT", None),
    ("TG-3", "12345", "PT", "12345"),
    ("TG-4", "A" * 20, "PT", "A" * 20),
    ("TG-5", "A" * 21, "PT", None),
    ("TG-6", "ab-12.34 5", "FR", "AB12345"),
    ("TG-7", "ABC$1234", "FR", None),
    ("TG-8", "12345678A", "FR", "12345678A"),
    ("TG-9", "ÑB12345", "DE", None),
    ("TG-10", "", "DE", None),
    ("TG-11", "- . -", "DE", None),
]


@pytest.mark.parametrize(
    ("value", "country", "expected"),
    [pytest.param(*row[1:], id=row[0]) for row in TABLE_6_2],
)
def test_basic_format_matches_table_6_2(value: str, country: str, expected: str | None) -> None:
    """CA-3.1, CA-3.2, CA-3.8: normalized, then 5 to 20 letters A-Z or digits; no Spanish check."""
    if expected is None:
        with pytest.raises(InvalidTaxIdFormatError):
            validate_tax_id(value, country)
    else:
        assert validate_tax_id(value, country) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param("12.345.678-z", "12345678Z", id="TI-5"),
        pytest.param("x-1234567-l", "X1234567L", id="TI-23"),
        pytest.param(" b 12\t345\n67\r4 ", "B12345674", id="whitespace-anywhere"),
        pytest.param("B12345674", "B12345674", id="already-normalized"),
        pytest.param("straße", "STRAßE", id="only-ascii-letters-are-uppercased"),
        pytest.param("a_b", "A_B", id="other-symbols-are-kept"),
    ],
)
def test_normalization_removes_separators_and_uppercases(value: str, expected: str) -> None:
    """CA-3.1: spaces, hyphens and dots go away anywhere; a-z become A-Z, and nothing else."""
    assert normalize_tax_id(value) == expected


@pytest.mark.parametrize("country", [None, "XX", "", "es"])
def test_without_a_spanish_country_only_the_basic_format_applies(country: str | None) -> None:
    """CA-3.9: a missing, invalid or unsupported country never triggers the Spanish check."""
    assert validate_tax_id("12345678A", country) == "12345678A"
    with pytest.raises(InvalidTaxIdFormatError):
        validate_tax_id("1234", country)
