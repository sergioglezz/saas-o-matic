"""Shared page parameters and customer id of the route (level U), spec 004 task T-05.

Plan 004 DT-9 and DT-10 move this code out of the customer routes so the history reuses it
(CA-5.3, CA-5.5). The cases are those of spec 003 (LP and FI): moving it changes nothing.
"""

import pytest
from pydantic import ValidationError

from app.api.identifiers import parse_customer_id
from app.api.validation import field_errors
from app.core.errors import ApiError
from app.schemas.pagination import PAGE_INVALID_MESSAGES, PageQuery

LIM = "Debe ser un número entero entre 1 y 100"
OFF = "Debe ser un número entero entre 0 y 1000000"


def _details(params: dict[str, str]) -> set[tuple[str, str]]:
    with pytest.raises(ValidationError) as raised:
        PageQuery.model_validate(params)
    return {(d.field, d.message) for d in field_errors(raised.value, PAGE_INVALID_MESSAGES)}


def test_defaults_are_50_and_0() -> None:
    """003 CA-5.6, 004 CA-5.3: without parameters, the first 50."""
    query = PageQuery.model_validate({})

    assert (query.limit, query.offset) == (50, 0)


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        pytest.param({"limit": "1", "offset": "0"}, (1, 0), id="minimums"),
        pytest.param({"limit": "100", "offset": "1000000"}, (100, 1_000_000), id="maximums"),
    ],
)
def test_accepts_the_limits_of_the_range(params: dict[str, str], expected: tuple[int, int]) -> None:
    """003 CA-5.8: both ends of each range are valid."""
    query = PageQuery.model_validate(params)

    assert (query.limit, query.offset) == expected


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        pytest.param({"limit": "0"}, {("limit", LIM)}, id="LP-1"),
        pytest.param({"limit": "101"}, {("limit", LIM)}, id="LP-2"),
        pytest.param({"limit": "abc"}, {("limit", LIM)}, id="LP-3"),
        pytest.param({"limit": "1.5"}, {("limit", LIM)}, id="LP-4"),
        pytest.param({"limit": "-1"}, {("limit", LIM)}, id="LP-5"),
        pytest.param({"limit": ""}, {("limit", LIM)}, id="LP-6"),
        pytest.param({"limit": "+5"}, {("limit", LIM)}, id="LP-7"),
        pytest.param({"limit": " 5"}, {("limit", LIM)}, id="LP-8"),
        pytest.param({"limit": chr(0x665)}, {("limit", LIM)}, id="LP-9"),  # ARABIC-INDIC FIVE
        pytest.param({"offset": "-1"}, {("offset", OFF)}, id="LP-10"),
        pytest.param({"offset": "1000001"}, {("offset", OFF)}, id="LP-11"),
        pytest.param({"offset": "x"}, {("offset", OFF)}, id="LP-12"),
        pytest.param({"offset": "9" * 32}, {("offset", OFF)}, id="LP-13"),
        pytest.param({"limit": "0", "offset": "-1"}, {("limit", LIM), ("offset", OFF)}, id="LP-14"),
    ],
)
def test_rejects_invalid_page_parameters(
    params: dict[str, str], expected: set[tuple[str, str]]
) -> None:
    """003 CA-5.8, 004 CA-5.3, HP-1 to HP-3: one detail per invalid parameter."""
    assert _details(params) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [pytest.param("1", 1, id="one"), pytest.param("9223372036854775807", 2**63 - 1, id="largest")],
)
def test_parses_a_customer_id(text: str, expected: int) -> None:
    """003 CA-6.3: digits only, no sign, no leading zeros, up to 2**63 - 1."""
    assert parse_customer_id(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("abc", id="FI-3"),
        pytest.param("0", id="FI-4"),
        pytest.param("-1", id="FI-5"),
        pytest.param("1.5", id="FI-6"),
        pytest.param("01", id="FI-7"),
        pytest.param("99999999999999999999", id="FI-8"),
        pytest.param("9223372036854775808", id="largest+1"),
    ],
)
def test_text_that_is_not_an_id_is_not_found(text: str) -> None:
    """003 CA-6.3, 004 CA-5.5, HI-11: the same 404 as an unknown customer."""
    with pytest.raises(ApiError) as raised:
        parse_customer_id(text)

    assert (raised.value.status, raised.value.code) == (404, "not_found")
