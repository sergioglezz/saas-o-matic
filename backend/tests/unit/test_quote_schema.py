"""Quote request and response schemas without a server (level U), spec 002 tasks T-06 to T-08.

Special characters are built with chr() so the source shows exactly what is sent:
TAB, LF, CR, NBSP (non-breaking space, E-23) and the full-width letters of E-22.
"""

import json

import pytest
from pydantic import ValidationError

from app.api.validation import field_errors
from app.schemas.pricing import INVALID_FIELD_MESSAGES, QuoteRequest, normalize_country

TAB, LF, CR = chr(9), chr(10), chr(13)
NBSP = chr(0xA0)
FULL_WIDTH_ES = chr(0xFF25) + chr(0xFF33)
JSON_NBSP_ESCAPE = chr(92) + "u00a0"  # the six characters of the JSON escape for NBSP

OBL = "Campo obligatorio"
USR = "Debe ser un número entero entre 0 y 100000"
FMT = "Debe ser un código de país de 2 letras"
NPE = "Campo no permitido"

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


# --- T-07: QuoteRequest and field_errors (RF-2, RF-3, RF-5, RF-6 CA-6.3) ------------------

# (case id, JSON body as sent, expected details as (field, message) pairs). E-17 and E-35
# need the tax rate table (unsupported country) and are checked over HTTP in T-12.
TABLE_6_2_SCHEMA: list[tuple[str, str, set[tuple[str, str]]]] = [
    ("E-1", '{"users": -1, "country": "ES"}', {("users", USR)}),
    ("E-2", '{"users": 100001, "country": "ES"}', {("users", USR)}),
    ("E-3", '{"users": 1.5, "country": "ES"}', {("users", USR)}),
    ("E-4", '{"users": 15.0, "country": "ES"}', {("users", USR)}),
    ("E-5", '{"users": 1e2, "country": "ES"}', {("users", USR)}),
    ("E-6", '{"users": 100000.0, "country": "ES"}', {("users", USR)}),
    ("E-7", '{"users": 0.0, "country": "ES"}', {("users", USR)}),
    ("E-8", '{"users": "15", "country": "ES"}', {("users", USR)}),
    ("E-9", '{"users": "", "country": "ES"}', {("users", USR)}),
    ("E-10", '{"users": true, "country": "ES"}', {("users", USR)}),
    ("E-11", '{"users": null, "country": "ES"}', {("users", USR)}),
    ("E-12", '{"users": [], "country": "ES"}', {("users", USR)}),
    ("E-13", '{"users": {}, "country": "ES"}', {("users", USR)}),
    ("E-14", '{"users": 99999999999999999999, "country": "ES"}', {("users", USR)}),
    ("E-15", '{"users": -1.5, "country": "ES"}', {("users", USR)}),
    ("E-16", '{"country": "ES"}', {("users", OBL)}),
    ("E-18", '{"users": 15, "country": "ESP"}', {("country", FMT)}),
    ("E-19", '{"users": 15, "country": "E"}', {("country", FMT)}),
    ("E-20", '{"users": 15, "country": "12"}', {("country", FMT)}),
    ("E-21", '{"users": 15, "country": "E S"}', {("country", FMT)}),
    ("E-22", '{"users": 15, "country": "' + FULL_WIDTH_ES + '"}', {("country", FMT)}),
    ("E-23", '{"users": 15, "country": "' + JSON_NBSP_ESCAPE + 'ES"}', {("country", FMT)}),
    ("E-24", '{"users": 15, "country": "   "}', {("country", FMT)}),
    ("E-25", '{"users": 15, "country": ""}', {("country", FMT)}),
    ("E-26", '{"users": 15, "country": 34}', {("country", FMT)}),
    ("E-27", '{"users": 15, "country": null}', {("country", FMT)}),
    ("E-28", '{"users": 15, "country": ["ES"]}', {("country", FMT)}),
    ("E-29", '{"users": 15, "country": {"code": "ES"}}', {("country", FMT)}),
    ("E-30", '{"users": 15}', {("country", OBL)}),
    ("E-31", "{}", {("users", OBL), ("country", OBL)}),
    ("E-32", '{"users": 15, "country": "ES", "subtotal_cents": 1}', {("subtotal_cents", NPE)}),
    (
        "E-33",
        '{"users": 15, "country": "ES", "subtotal_cents": 1, "tax_rate_bp": 0}',
        {("subtotal_cents", NPE), ("tax_rate_bp", NPE)},
    ),
    (
        "E-34",
        '{"users": -1, "country": "ES", "subtotal_cents": 1}',
        {("users", USR), ("subtotal_cents", NPE)},
    ),
    ("E-36", '{"Users": 15, "country": "ES"}', {("Users", NPE), ("users", OBL)}),
]


@pytest.mark.parametrize(
    ("body", "expected"),
    [pytest.param(body, expected, id=case_id) for case_id, body, expected in TABLE_6_2_SCHEMA],
)
def test_invalid_requests_produce_the_details_of_table_6_2(
    body: str, expected: set[tuple[str, str]]
) -> None:
    """CA-2.2, CA-2.3, CA-3.2, CA-3.3, CA-3.5, CA-5.1, CA-5.2, CA-6.3: one detail per field."""
    with pytest.raises(ValidationError) as error:
        QuoteRequest.model_validate(json.loads(body))

    details = field_errors(error.value, INVALID_FIELD_MESSAGES)
    assert {(d.field, d.message) for d in details} == expected
    assert len(details) == len(expected)


@pytest.mark.parametrize(
    ("body", "users", "country"),
    [
        pytest.param('{"users": -0, "country": "US"}', 0, "US", id="Q-20"),
        pytest.param('{"users": 0, "country": "ES"}', 0, "ES", id="min"),
        pytest.param('{"users": 100000, "country": "ES"}', 100000, "ES", id="max"),
        pytest.param('{"users": 15, "country": " es "}', 15, "ES", id="normalized"),
    ],
)
def test_valid_requests_are_accepted_and_normalized(body: str, users: int, country: str) -> None:
    """CA-2.1, CA-3.6: JSON integers 0..100000 (also -0) and a normalized country."""
    request = QuoteRequest.model_validate(json.loads(body))

    assert (request.users, request.country) == (users, country)
    assert type(request.users) is int
