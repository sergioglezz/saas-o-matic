"""GET /customers over HTTP (level I), spec 003 task T-14.

Covers RF-5 (CA-5.1 to CA-5.11) with tables 6.6 (LI) and 6.7 (LP), and CO-5.
"""

from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from tests.api.customer_requests import (
    AL_1,
    AL_1_RESPONSE,
    CUSTOMERS_PATH,
    create_table_6_6,
    post_customer,
    total_customers,
)
from tests.api.quote_requests import details_of
from tests.customers_data import ALL_BY_NAME
from tests.unit.test_customer_schema import TABLE_6_7

SQL_TEXT = "'; DROP TABLE customers;--"


def _list(client: TestClient, query: str = "") -> Response:
    """GET /customers with the query string exactly as written (already percent-encoded)."""
    response: Response = client.get(f"{CUSTOMERS_PATH}?{query}" if query else CUSTOMERS_PATH)
    return response


def _q(text: str) -> str:
    return "q=" + quote(text, safe="")


# (case id, query string, ids of items in order, total)
TABLE_6_6: list[tuple[str, str, list[int], int]] = [
    ("LI-1", "", ALL_BY_NAME, 6),
    ("LI-2", _q("ACME"), [6, 2], 2),
    ("LI-3", _q("compañía ñ"), [3], 1),
    ("LI-4", _q("b1234"), [2], 1),
    ("LI-5", _q("12.345.678-z"), [3], 1),
    ("LI-6", _q("   "), ALL_BY_NAME, 6),
    ("LI-7", _q("inexistente"), [], 0),
    ("LI-8", _q("%"), [5], 1),
    ("LI-9", _q("_"), [], 0),
    ("LI-10", "limit=2", [5, 6], 6),
    ("LI-11", "limit=2&offset=4", [4, 1], 6),
    ("LI-12", "offset=6", [], 6),
    ("LI-13", _q("acme") + "&limit=1", [6], 2),
    ("LI-14", _q(SQL_TEXT), [], 0),
    ("LI-15", "limit=1&limit=3", [5, 6, 2], 6),
    ("LI-16", "desconocido=1", ALL_BY_NAME, 6),
    ("LI-17", _q("telefonica"), [], 0),
    ("LI-18", _q("  acme   telecom "), [2], 1),
    ("LI-20-limit-100", "limit=100", ALL_BY_NAME, 6),
    ("LI-20-offset-1000000", "limit=1&offset=1000000", [], 6),
]


@pytest.fixture
def six_customers(client: TestClient) -> TestClient:
    create_table_6_6(client)
    return client


@pytest.mark.parametrize(
    ("query", "ids", "total"),
    [pytest.param(*row[1:], id=row[0]) for row in TABLE_6_6],
)
def test_list_and_search_match_table_6_6(
    six_customers: TestClient, query: str, ids: list[int], total: int
) -> None:
    """LI-1 to LI-18 and LI-20; CA-5.1 to CA-5.7, CA-5.10, CA-5.11."""
    response = _list(six_customers, query)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert set(body) == {"items", "total"}
    assert [item["id"] for item in body["items"]] == ids
    assert body["total"] == total


def test_sql_in_the_search_text_changes_nothing(six_customers: TestClient) -> None:
    """LI-14, CA-5.4, RNF-2: after searching SQL text, the six customers are still there."""
    assert _list(six_customers, _q(SQL_TEXT)).json() == {"items": [], "total": 0}

    assert total_customers(six_customers) == 6


def test_empty_database_lists_nothing(client: TestClient) -> None:
    """LI-19, CA-5.11: 200 with an empty list, not an error."""
    response = _list(client)

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


@pytest.mark.usefixtures("fixed_clock")
def test_items_carry_the_same_fields_as_the_registration(client: TestClient) -> None:
    """CA-5.1, CA-1.4: each item is the customer exactly as POST returned it."""
    assert post_customer(client, AL_1).json() == AL_1_RESPONSE

    assert _list(client).json() == {"items": [AL_1_RESPONSE], "total": 1}


def test_a_rejected_duplicate_does_not_appear_in_the_list(client: TestClient) -> None:
    """CO-5, CA-1.5: after a 409 there is still one customer."""
    assert post_customer(client, AL_1).status_code == 201
    assert post_customer(client, AL_1).status_code == 409

    assert total_customers(client) == 1


def _query_string(params: dict[str, object]) -> str:
    return "&".join(f"{name}={quote(str(value), safe='')}" for name, value in params.items())


@pytest.mark.parametrize(
    ("params", "expected"),
    [pytest.param(params, expected, id=case_id) for case_id, params, expected in TABLE_6_7],
)
def test_invalid_parameters_return_422_with_the_details_of_table_6_7(
    six_customers: TestClient, params: dict[str, object], expected: set[tuple[str, str]]
) -> None:
    """LP-1 to LP-15; CA-5.8, CA-5.9: same error format as any other validation."""
    response = _list(six_customers, _query_string(params))

    assert response.status_code == 422
    error = response.json()["error"]
    assert (error["code"], error["message"]) == ("validation_error", "Datos no válidos")
    assert details_of(response) == expected
    assert len(error["details"]) == len(expected)
