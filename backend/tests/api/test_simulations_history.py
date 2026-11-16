"""History of a customer over HTTP (level I), spec 004 task T-09.

RF-5 (CA-5.1 to CA-5.6) and CA-1.3 with tables 6.5 (HI) and 6.6 (HP). Starting data of 6.5: at
10:00:00Z SI-1 for customer 1 (id 1); at 10:05:00Z SI-7 (id 2) and SI-2 (id 3) for customer 1,
and SI-3 (id 4) for customer 2. Customer 3 has no simulations.
"""

import pytest
from fastapi.testclient import TestClient

from tests.api.customer_requests import CUSTOMERS_PATH
from tests.api.simulation_requests import (
    AT_10_05,
    CASE,
    SettableClock,
    create_starting_customers,
    history_path,
    post_simulation,
)

LIM = "Debe ser un número entero entre 1 y 100"
OFF = "Debe ser un número entero entre 0 y 1000000"
NOT_FOUND = {"error": {"code": "not_found", "message": "Recurso no encontrado", "details": []}}

Saved = dict[int, dict[str, object]]


@pytest.fixture
def saved(client: TestClient, simulation_clock: SettableClock) -> Saved:
    """The data of table 6.5; returns each 201 body by its id."""
    create_starting_customers(client)
    bodies = [post_simulation(client, CASE["SI-1"].body()).json()]
    simulation_clock.now = AT_10_05
    for case in ("SI-7", "SI-2", "SI-3"):
        bodies.append(post_simulation(client, CASE[case].body()).json())
    return {int(str(body["id"])): body for body in bodies}


def _ids(client: TestClient, path: str) -> tuple[list[object], object]:
    response = client.get(path)
    assert response.status_code == 200
    body = response.json()
    return [item["id"] for item in body["items"]], body["total"]


@pytest.mark.parametrize(
    ("path", "expected_ids", "total"),
    [
        pytest.param(history_path(1), [3, 2, 1], 3, id="HI-1"),
        pytest.param(history_path(2), [4], 1, id="HI-2"),
        pytest.param(history_path(3), [], 0, id="HI-3"),
        pytest.param(f"{history_path(1)}?limit=2", [3, 2], 3, id="HI-4"),
        pytest.param(f"{history_path(1)}?limit=2&offset=2", [1], 3, id="HI-5"),
        pytest.param(f"{history_path(1)}?offset=3", [], 3, id="HI-6"),
        pytest.param(f"{history_path(1)}?limit=1&limit=2", [3, 2], 3, id="HI-7"),
        pytest.param(f"{history_path(1)}?desconocido=1", [3, 2, 1], 3, id="HI-8"),
    ],
)
def test_history_order_pages_and_totals(
    client: TestClient, saved: Saved, path: str, expected_ids: list[int], total: int
) -> None:
    """HI-1 to HI-8, CA-5.1 to CA-5.4: newest first, by id within the same second (D-9)."""
    assert _ids(client, path) == (expected_ids, total)


def test_hi_9_each_item_is_its_201(client: TestClient, saved: Saved) -> None:
    """HI-9, CA-1.3, CA-5.1: the history repeats, field by field, what the save returned."""
    customer_1 = client.get(history_path(1)).json()["items"]
    customer_2 = client.get(history_path(2)).json()["items"]

    assert customer_1 == [saved[3], saved[2], saved[1]]
    assert customer_2 == [saved[4]]


@pytest.mark.parametrize(
    "customer_id",
    [
        pytest.param("999", id="HI-10"),
        *[
            pytest.param(text, id=f"HI-11-{text}")
            for text in ("abc", "0", "-1", "1.5", "01", "99999999999999999999")
        ],
    ],
)
def test_unknown_or_malformed_customer_is_404(
    client: TestClient, saved: Saved, customer_id: str
) -> None:
    """HI-10, HI-11, CA-5.5: the same 404 with no details, without an internal error."""
    response = client.get(history_path(customer_id))

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_hi_12_trailing_slash_is_404_without_redirect(client: TestClient, saved: Saved) -> None:
    """HI-12, CA-6.1: /customers/1/simulations/ is an unknown route."""
    response = client.get(f"{history_path(1)}/", follow_redirects=False)

    assert response.status_code == 404
    assert response.json() == NOT_FOUND
    assert "location" not in response.headers


def test_hi_13_customer_detail_does_not_change(client: TestClient, saved: Saved) -> None:
    """HI-13, CA-5.6: GET /customers/{id} still returns only the customer data."""
    body = client.get(f"{CUSTOMERS_PATH}/1").json()

    assert set(body) == {
        "id",
        "company_name",
        "tax_id",
        "contact_email",
        "country",
        "plan",
        "created_at",
    }


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        *[
            pytest.param(query, {("limit", LIM)}, id=f"HP-1-{query}")
            for query in ("limit=0", "limit=101", "limit=abc", "limit=", "limit=%2B5")
        ],
        *[
            pytest.param(query, {("offset", OFF)}, id=f"HP-2-{query}")
            for query in ("offset=-1", "offset=1000001", "offset=x")
        ],
        pytest.param("limit=0&offset=-1", {("limit", LIM), ("offset", OFF)}, id="HP-3"),
    ],
)
def test_invalid_page_parameters_are_422(
    client: TestClient, saved: Saved, query: str, expected: set[tuple[str, str]]
) -> None:
    """HP-1 to HP-3, CA-5.3: the messages of GET /customers, one per parameter."""
    response = client.get(f"{history_path(1)}?{query}")

    assert response.status_code == 422
    error = response.json()["error"]
    assert (error["code"], error["message"]) == ("validation_error", "Datos no válidos")
    assert {(detail["field"], detail["message"]) for detail in error["details"]} == expected


@pytest.mark.parametrize("customer_id", ["999", "abc"])
def test_hp_4_not_found_goes_before_the_parameters(
    client: TestClient, saved: Saved, customer_id: str
) -> None:
    """HP-4, CA-5.5, spec decision D-7: without a customer there is nothing to page."""
    response = client.get(f"{history_path(customer_id)}?limit=0")

    assert response.status_code == 404
    assert response.json() == NOT_FOUND
