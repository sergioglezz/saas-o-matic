"""Validation errors of POST /pricing/quote over HTTP (level I), spec 002 task T-12.

Covers RF-2 (CA-2.1 to CA-2.3), RF-3 (CA-3.2 to CA-3.5), RF-5 (CA-5.1, CA-5.2) and RF-6
(CA-6.1, CA-6.3, CA-6.4) with every row of table 6.2 (E-1 to E-36).
"""

import pytest
from fastapi.testclient import TestClient

from tests.api.quote_requests import details_of, post_quote

OBL = "Campo obligatorio"
USR = "Debe ser un número entero entre 0 y 100000"
FMT = "Debe ser un código de país de 2 letras"
NSP = "País no soportado"
NPE = "Campo no permitido"

FULL_WIDTH_ES = chr(0xFF25) + chr(0xFF33)
JSON_NBSP_ESCAPE = chr(92) + "u00a0"  # the six characters of the JSON escape for NBSP

# (case id, JSON body, expected details as (field, message) pairs, compared as a set)
TABLE_6_2: list[tuple[str, str, set[tuple[str, str]]]] = [
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
    ("E-17", '{"users": 15, "country": "XX"}', {("country", NSP)}),
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
    ("E-35", '{"users": -1, "country": "XX"}', {("users", USR), ("country", NSP)}),
    ("E-36", '{"Users": 15, "country": "ES"}', {("Users", NPE), ("users", OBL)}),
]


@pytest.mark.parametrize(
    ("body", "expected"),
    [pytest.param(body, expected, id=case_id) for case_id, body, expected in TABLE_6_2],
)
def test_invalid_requests_return_422_with_the_details_of_table_6_2(
    client: TestClient, body: str, expected: set[tuple[str, str]]
) -> None:
    """CA-2.2, CA-2.3, CA-3.2 to CA-3.5, CA-5.1, CA-5.2, CA-6.1, CA-6.3, CA-6.4."""
    response = post_quote(client, body)

    assert response.status_code == 422
    error = response.json()["error"]
    assert (error["code"], error["message"]) == ("validation_error", "Datos no válidos")
    assert details_of(response) == expected
    assert len(error["details"]) == len(expected)  # one element per field (E-15)
