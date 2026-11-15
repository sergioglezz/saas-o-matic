"""Quote request and response schemas without a server (level U), spec 002 tasks T-06 to T-08.

Special characters are built with chr() so the source shows exactly what is sent:
TAB, LF, CR, NBSP (non-breaking space, E-23) and the full-width letters of E-22.
"""

import pytest

from app.schemas.pricing import normalize_country

TAB, LF, CR = chr(9), chr(10), chr(13)
NBSP = chr(0xA0)
FULL_WIDTH_ES = chr(0xFF25) + chr(0xFF33)

# --- T-06: normalize_country (RF-3: CA-3.1, CA-3.2, CA-3.6) ------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("es", "ES", id="Q-11"),
        pytest.param(" ES ", "ES", id="Q-12"),
        pytest.param(TAB + "Es" + LF, "ES", id="Q-13"),
        pytest.param("pt", "PT", id="Q-14"),
        pytest.param("fr", "FR", id="Q-15"),
        pytest.param("de", "DE", id="Q-16"),
        pytest.param("it", "IT", id="Q-17"),
        pytest.param("gb", "GB", id="Q-18"),
        pytest.param("us", "US", id="Q-19"),
        pytest.param(CR + " es " + CR, "ES", id="carriage-return"),
        pytest.param("ES", "ES", id="already-normalized"),
    ],
)
def test_normalize_country_trims_edges_and_uppercases(raw: str, expected: str) -> None:
    """CA-3.1, CA-3.6: only space, tab, line feed and carriage return are trimmed; a-z upper."""
    assert normalize_country(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param("ESP", id="E-18"),
        pytest.param("E", id="E-19"),
        pytest.param("12", id="E-20"),
        pytest.param("E S", id="E-21"),
        pytest.param(FULL_WIDTH_ES, id="E-22"),
        pytest.param(NBSP + "ES", id="E-23"),
        pytest.param("   ", id="E-24"),
        pytest.param("", id="E-25"),
        pytest.param("ß", id="sharp-s-would-become-SS"),
    ],
)
def test_normalize_country_rejects_anything_but_two_ascii_letters(raw: str) -> None:
    """CA-3.2: after trimming and uppercasing it must be exactly 2 letters A-Z."""
    with pytest.raises(ValueError, match="Debe ser un código de país de 2 letras"):
        normalize_country(raw)
