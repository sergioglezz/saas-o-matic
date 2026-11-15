"""POST /pricing/quote happy path and body reading over HTTP (level I), spec 002 task T-11.

Covers RF-1 (CA-1.1 to CA-1.3), RF-3 (CA-3.1, CA-3.6), RF-4 (CA-4.1 to CA-4.4) and RF-7
(CA-7.1 to CA-7.3) with Q-1 to Q-20, O-1, O-2, O-6, O-7, O-9, O-15 and E-37 to E-42.
"""

import pytest
from fastapi.testclient import TestClient

from tests.api.quote_requests import (
    SPEC_SECTION_5_EXAMPLE,
    details_of,
    json_without_floats,
    post_quote,
)

# JSON escapes as written in the spec ("\tEs\n"): raw control characters are not valid JSON.
JSON_TAB, JSON_LF = chr(92) + "t", chr(92) + "n"

# (case id, JSON body, subtotal_cents, tax_rate_bp, tax_cents, total_cents)
# Q-1 to Q-10 are the requests of spec 001 T-1 to T-10; Q-11 to Q-20 come from table 6.1.
TABLE_6_1: list[tuple[str, str, int, int, int, int]] = [
    ("Q-1", '{"users": 0, "country": "ES"}', 0, 2100, 0, 0),
    ("Q-2", '{"users": 1, "country": "PT"}', 1000, 2300, 230, 1230),
    ("Q-3", '{"users": 11, "country": "DE"}', 10800, 1900, 2052, 12852),
    ("Q-4", '{"users": 15, "country": "ES"}', 14000, 2100, 2940, 16940),
    ("Q-5", '{"users": 15, "country": "US"}', 14000, 0, 0, 14000),
    ("Q-6", '{"users": 51, "country": "FR"}', 42500, 2000, 8500, 51000),
    ("Q-7", '{"users": 60, "country": "ES"}', 47000, 2100, 9870, 56870),
    ("Q-8", '{"users": 100, "country": "GB"}', 67000, 2000, 13400, 80400),
    ("Q-9", '{"users": 10, "country": "IT"}', 10000, 2200, 2200, 12200),
    ("Q-10", '{"users": 100000, "country": "ES"}', 50017000, 2100, 10503570, 60520570),
    ("Q-11", '{"users": 15, "country": "es"}', 14000, 2100, 2940, 16940),
    ("Q-12", '{"users": 15, "country": " ES "}', 14000, 2100, 2940, 16940),
    (
        "Q-13",
        '{"users": 15, "country": "' + JSON_TAB + "Es" + JSON_LF + '"}',
        14000,
        2100,
        2940,
        16940,
    ),
    ("Q-14", '{"users": 1, "country": "pt"}', 1000, 2300, 230, 1230),
    ("Q-15", '{"users": 1, "country": "fr"}', 1000, 2000, 200, 1200),
    ("Q-16", '{"users": 1, "country": "de"}', 1000, 1900, 190, 1190),
    ("Q-17", '{"users": 1, "country": "it"}', 1000, 2200, 220, 1220),
    ("Q-18", '{"users": 1, "country": "gb"}', 1000, 2000, 200, 1200),
    ("Q-19", '{"users": 1, "country": "us"}', 1000, 0, 0, 1000),
    ("Q-20", '{"users": -0, "country": "US"}', 0, 0, 0, 0),
]

Q4_BODY = '{"users": 15, "country": "ES"}'
BODY_DETAIL = {("body", "El cuerpo debe ser un objeto JSON")}


@pytest.mark.parametrize(
    ("body", "subtotal", "rate_bp", "tax", "total"),
    [pytest.param(*row[1:], id=row[0]) for row in TABLE_6_1],
)
def test_valid_quotes_match_table_6_1(
    client: TestClient, body: str, subtotal: int, rate_bp: int, tax: int, total: int
) -> None:
    """CA-1.1, CA-3.1, CA-3.6, CA-4.4: 200 with the amounts of the calculation of spec 001."""
    response = post_quote(client, body)

    assert response.status_code == 200
    data = response.json()
    assert (data["subtotal_cents"], data["tax_rate_bp"]) == (subtotal, rate_bp)
    assert (data["tax_cents"], data["total_cents"]) == (tax, total)
    assert data["currency"] == "EUR"


def test_q4_returns_exactly_the_example_of_spec_section_5(client: TestClient) -> None:
    """Q-4, CA-4.1 to CA-4.4: the whole body, field by field."""
    response = post_quote(client, Q4_BODY)

    assert response.status_code == 200
    assert response.json() == SPEC_SECTION_5_EXAMPLE


def test_minus_zero_users_is_returned_as_zero(client: TestClient) -> None:
    """Q-20, CA-4.2: -0 is accepted and returned as the integer 0."""
    response = post_quote(client, '{"users": -0, "country": "US"}')

    assert response.json()["users"] == 0


@pytest.mark.parametrize(
    ("case", "body", "content_type"),
    [
        ("O-1", Q4_BODY, "application/json; charset=utf-8"),
        ("O-2", '{"users": 1, "users": 15, "country": "ES"}', "application/json"),
        ("O-15", Q4_BODY, "Application/JSON"),
    ],
    ids=["O-1", "O-2", "O-15"],
)
def test_json_variants_are_quoted_like_q4(
    client: TestClient, case: str, body: str, content_type: str
) -> None:
    """CA-7.1, CA-7.3: charset, repeated key (last wins) and media type case."""
    response = post_quote(client, body, content_type=content_type)

    assert response.status_code == 200, case
    assert response.json() == SPEC_SECTION_5_EXAMPLE


def test_same_request_twice_gives_identical_responses(client: TestClient) -> None:
    """O-6, CA-1.3."""
    first, second = post_quote(client, Q4_BODY), post_quote(client, Q4_BODY)

    assert first.status_code == second.status_code == 200
    assert first.content == second.content


def test_quoting_creates_no_resource(client: TestClient) -> None:
    """O-7, CA-1.2: 200 (never 201), no Location header and no id field."""
    response = post_quote(client, Q4_BODY)

    assert response.status_code == 200
    assert "location" not in response.headers
    assert "id" not in response.json()


@pytest.mark.parametrize("body", [row[1] for row in TABLE_6_1], ids=[row[0] for row in TABLE_6_1])
def test_every_number_in_the_response_is_an_integer(client: TestClient, body: str) -> None:
    """O-9, CA-4.1: no decimals and no exponent anywhere in a 200 body."""
    response = post_quote(client, body)

    assert response.status_code == 200  # otherwise an error body would pass vacuously
    json_without_floats(response)


@pytest.mark.parametrize(
    ("body", "content_type"),
    [
        pytest.param(b"no es json", "application/json", id="E-37"),
        pytest.param(b'[15, "ES"]', "application/json", id="E-38"),
        pytest.param(b"null", "application/json", id="E-39"),
        pytest.param(b"", "application/json", id="E-40"),
        pytest.param(Q4_BODY.encode(), "text/plain", id="E-41"),
        pytest.param(Q4_BODY.encode(), None, id="E-42"),
    ],
)
def test_bodies_that_are_not_a_json_object_are_rejected(
    client: TestClient, body: bytes, content_type: str | None
) -> None:
    """CA-7.2: 422 validation_error with the single detail body."""
    response = post_quote(client, body, content_type=content_type)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert details_of(response) == BODY_DETAIL
