"""GET /customers/{id} over HTTP (level I), spec 003 task T-15.

Covers RF-6 (CA-6.1 to CA-6.3) and RF-1 (CA-1.4) with table 6.8 (FI) and case AL-4.
"""

import pytest
from fastapi.testclient import TestClient

from tests.api.customer_requests import AL_1, AL_1_RESPONSE, CUSTOMERS_PATH, post_customer

NOT_FOUND = {"error": {"code": "not_found", "message": "Recurso no encontrado", "details": []}}


@pytest.fixture
def one_customer(client: TestClient, fixed_clock: object) -> TestClient:
    assert post_customer(client, AL_1).json() == AL_1_RESPONSE
    return client


def test_existing_customer_is_returned(one_customer: TestClient) -> None:
    """FI-1, CA-6.1: 200 with the fields of the registration."""
    response = one_customer.get(f"{CUSTOMERS_PATH}/1")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == AL_1_RESPONSE


def test_registered_customer_reads_the_same_everywhere(one_customer: TestClient) -> None:
    """AL-4, CA-1.4: the registration, the detail and the list return the same customer."""
    detail = one_customer.get(f"{CUSTOMERS_PATH}/1").json()
    listed = one_customer.get(CUSTOMERS_PATH).json()["items"]

    assert detail == AL_1_RESPONSE
    assert listed == [AL_1_RESPONSE]


@pytest.mark.parametrize(
    "identifier",
    [
        pytest.param("999", id="FI-2"),
        pytest.param("abc", id="FI-3"),
        pytest.param("0", id="FI-4"),
        pytest.param("-1", id="FI-5"),
        pytest.param("1.5", id="FI-6"),
        pytest.param("01", id="FI-7"),
        pytest.param("99999999999999999999", id="FI-8"),
        pytest.param("9223372036854775808", id="FI-8-first-number-sqlite-cannot-hold"),
        pytest.param("1%20", id="id-with-a-space"),
        pytest.param("%D9%A1", id="id-with-a-non-ascii-digit"),
    ],
)
def test_what_identifies_no_customer_is_not_found(
    one_customer: TestClient, identifier: str
) -> None:
    """FI-2 to FI-8, CA-6.2, CA-6.3: the same 404, also for text that is not an id."""
    response = one_customer.get(f"{CUSTOMERS_PATH}/{identifier}")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == NOT_FOUND


def test_largest_possible_id_is_looked_up_without_failing(one_customer: TestClient) -> None:
    """CA-6.3: 9223372036854775807 is a valid id; it simply does not exist."""
    response = one_customer.get(f"{CUSTOMERS_PATH}/9223372036854775807")

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_trailing_slash_is_another_route(one_customer: TestClient) -> None:
    """FI-9, CA-6.2 (002 CA-6.7): /customers/1/ is not found and does not redirect."""
    response = one_customer.get(f"{CUSTOMERS_PATH}/1/", follow_redirects=False)

    assert response.status_code == 404
    assert response.json() == NOT_FOUND
    assert "location" not in response.headers
