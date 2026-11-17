"""Methods, internal failure, content type and CORS of the customer routes (level I).

Spec 003 task T-16: RF-7 (CA-7.2, CA-7.5) and RF-8 (CA-8.1 to CA-8.3) with cases ER-1 to ER-5
and ER-8 to ER-11 of table 6.9.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_customer_store
from app.domain.customers import Customer, CustomerPage, NewCustomer
from app.services.customers import CustomerStore
from tests.api.customer_requests import AL_1, CUSTOMERS_PATH, post_customer

FRONTEND = "http://localhost:4200"
OTHER_ORIGIN = "http://otro-origen.example"
ALLOW_ORIGIN = "access-control-allow-origin"
DETAIL_PATH = f"{CUSTOMERS_PATH}/1"
METHOD_NOT_ALLOWED = {
    "error": {"code": "method_not_allowed", "message": "Método no permitido", "details": []}
}
NOT_FOUND = {"error": {"code": "not_found", "message": "Recurso no encontrado", "details": []}}
INTERNAL_ERROR = {
    "error": {"code": "internal_error", "message": "Error interno del servidor", "details": []}
}


class BrokenStore:
    """A customer store whose database is down, with internal details in the exception."""

    def _fail(self) -> RuntimeError:
        return RuntimeError("database file /srv/secret/saas.db is locked in app.repositories")

    def add(self, new: NewCustomer, created_at: str) -> Customer:
        raise self._fail()

    def get(self, customer_id: int) -> Customer | None:
        raise self._fail()

    def search(
        self, name_fragment: str, tax_id_fragment: str, limit: int, offset: int
    ) -> CustomerPage:
        raise self._fail()

    def delete(self, customer_id: int) -> None:  # spec 007: the store also deletes
        raise self._fail()


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE", "OPTIONS"])
def test_customers_path_names_both_of_its_methods(client: TestClient, method: str) -> None:
    """ER-1, CA-7.2: 405 in the single format with Allow: GET, POST."""
    response = client.request(method, CUSTOMERS_PATH)

    assert response.status_code == 405
    assert response.headers["allow"] == "GET, POST"
    assert response.json() == METHOD_NOT_ALLOWED


def test_head_on_customers_is_405_without_a_body(client: TestClient) -> None:
    """ER-2, CA-7.2: HEAD carries no body, so the status and the Allow header are enough."""
    response = client.head(CUSTOMERS_PATH)

    assert response.status_code == 405
    assert response.headers["allow"] == "GET, POST"
    assert response.content == b""


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH"])
def test_customer_detail_path_allows_get_and_delete(client: TestClient, method: str) -> None:
    """ER-3, CA-7.2: 405 with the methods of the path, whether or not the customer exists.

    Spec 007 CA-1.6 added DELETE to this path: it left the rejected methods and the header
    went from "GET" to "DELETE, GET" (the only earlier test that 007 changes, plan 007 §4).
    """
    response = client.request(method, DETAIL_PATH)

    assert response.status_code == 405
    assert response.headers["allow"] == "DELETE, GET"
    assert response.json() == METHOD_NOT_ALLOWED


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_customers_path_with_trailing_slash_is_not_found(client: TestClient, method: str) -> None:
    """ER-4, CA-7.5: /customers/ is an unknown route; no redirection."""
    response = client.request(method, f"{CUSTOMERS_PATH}/", follow_redirects=False)

    assert response.status_code == 404
    assert response.json() == NOT_FOUND
    assert "location" not in response.headers


def test_internal_failure_returns_500_without_internal_details(app: FastAPI) -> None:
    """ER-5, CA-7.5: the store fails on the three routes; the client gets a generic message."""

    def broken_store() -> CustomerStore:
        return BrokenStore()

    app.dependency_overrides[get_customer_store] = broken_store
    with TestClient(app, raise_server_exceptions=False) as client:
        responses = [
            post_customer(client, AL_1),
            client.get(CUSTOMERS_PATH),
            client.get(DETAIL_PATH),
        ]

    for response in responses:
        assert response.status_code == 500
        assert response.headers["content-type"].startswith("application/json")
        assert response.json() == INTERNAL_ERROR
        for leaked in ("Traceback", "RuntimeError", "secret", "/srv", ".db", "app.repositories"):
            assert leaked not in response.text


def test_get_from_the_frontend_carries_the_allowed_origin(client: TestClient) -> None:
    """ER-8, CA-8.1: the dashboard can read the list and the detail from the browser."""
    post_customer(client, AL_1)

    for path in (CUSTOMERS_PATH, DETAIL_PATH):
        response = client.get(path, headers={"origin": FRONTEND})
        assert response.status_code == 200
        assert response.headers[ALLOW_ORIGIN] == FRONTEND


def test_post_from_the_frontend_carries_the_allowed_origin(client: TestClient) -> None:
    """CA-8.1: registering from the dashboard is allowed too."""
    response = post_customer(client, AL_1, headers={"origin": FRONTEND})

    assert response.status_code == 201
    assert response.headers[ALLOW_ORIGIN] == FRONTEND


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_preflight_from_the_frontend_is_accepted(client: TestClient, method: str) -> None:
    """ER-9, CA-8.2: 200 for the preflight of GET and of POST."""
    response = client.options(
        CUSTOMERS_PATH,
        headers={
            "origin": FRONTEND,
            "access-control-request-method": method,
            "access-control-request-headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers[ALLOW_ORIGIN] == FRONTEND
    assert method in response.headers["access-control-allow-methods"]


def test_another_origin_gets_no_permission(client: TestClient) -> None:
    """ER-10, CA-8.3: neither the GET nor its preflight carry Access-Control-Allow-Origin."""
    get = client.get(CUSTOMERS_PATH, headers={"origin": OTHER_ORIGIN})
    preflight = client.options(
        CUSTOMERS_PATH,
        headers={"origin": OTHER_ORIGIN, "access-control-request-method": "GET"},
    )

    assert ALLOW_ORIGIN not in get.headers
    assert ALLOW_ORIGIN not in preflight.headers


def test_every_kind_of_response_is_json(client: TestClient) -> None:
    """ER-11, CA-7.5: successes and errors alike (201, 200, 409, 422, 404 and 405)."""
    responses = {
        "AL-1": post_customer(client, AL_1),
        "LI-1": client.get(CUSTOMERS_PATH),
        "FI-1": client.get(DETAIL_PATH),
        "CO-1": post_customer(client, AL_1),
        "VA-1": post_customer(client, {}),
        "FI-2": client.get(f"{CUSTOMERS_PATH}/999"),
        "ER-1": client.delete(CUSTOMERS_PATH),
    }

    statuses = {case: response.status_code for case, response in responses.items()}
    assert statuses == {
        "AL-1": 201, "LI-1": 200, "FI-1": 200, "CO-1": 409, "VA-1": 422, "FI-2": 404, "ER-1": 405
    }  # fmt: skip
    for case, response in responses.items():
        assert response.headers["content-type"].startswith("application/json"), case
