"""Methods, internal failure, content type and CORS of the simulation routes (level I).

Spec 004 task T-10: RF-6 (CA-6.1 to CA-6.3) with cases ER-1 to ER-10 of table 6.7. Plan DT-14
expects no new code: the global error format and CORS of spec 003 already cover these routes.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from app.api.dependencies import get_simulation_store
from app.domain.pricing import PriceQuote
from app.domain.simulations import NewSimulation, Simulation, SimulationPage
from app.services.simulations import SimulationStore
from tests.api.customer_requests import CUSTOMERS_PATH
from tests.api.simulation_requests import (
    SI_1,
    SIMULATIONS_PATH,
    SettableClock,
    create_starting_customers,
    history_path,
    post_simulation,
)

FRONTEND = "http://localhost:4200"
OTHER_ORIGIN = "http://otro-origen.example"
ALLOW_ORIGIN = "access-control-allow-origin"
HISTORY_PATH = history_path(1)
METHOD_NOT_ALLOWED = {
    "error": {"code": "method_not_allowed", "message": "Método no permitido", "details": []}
}
NOT_FOUND = {"error": {"code": "not_found", "message": "Recurso no encontrado", "details": []}}
INTERNAL_ERROR = {
    "error": {"code": "internal_error", "message": "Error interno del servidor", "details": []}
}


class BrokenSimulationStore:
    """A simulation store whose database is down, with internal details in the exception."""

    def _fail(self) -> RuntimeError:
        return RuntimeError("database file /srv/secret/saas.db is locked in app.repositories")

    def add(self, new: NewSimulation, price: PriceQuote, created_at: str) -> Simulation:
        raise self._fail()

    def list_for_customer(self, customer_id: int, limit: int, offset: int) -> SimulationPage:
        raise self._fail()


@pytest.fixture
def client_with_customers(client: TestClient, simulation_clock: SettableClock) -> TestClient:
    create_starting_customers(client)
    return client


def _preflight(client: TestClient, path: str, method: str, origin: str) -> Response:
    response: Response = client.options(
        path,
        headers={
            "origin": origin,
            "access-control-request-method": method,
            "access-control-request-headers": "content-type",
        },
    )
    return response


@pytest.mark.parametrize("method", ["GET", "PUT", "PATCH", "DELETE", "OPTIONS"])
def test_er_1_simulations_path_allows_only_post(client: TestClient, method: str) -> None:
    """ER-1, CA-6.2: 405 in the single format with Allow: POST."""
    response = client.request(method, SIMULATIONS_PATH)

    assert response.status_code == 405
    assert response.headers["allow"] == "POST"
    assert response.json() == METHOD_NOT_ALLOWED


def test_er_2_head_on_simulations_is_405_without_a_body(client: TestClient) -> None:
    """ER-2, CA-6.2: HEAD carries no body; the status and Allow are enough."""
    response = client.head(SIMULATIONS_PATH)

    assert response.status_code == 405
    assert response.headers["allow"] == "POST"
    assert response.content == b""


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_er_3_history_path_allows_only_get(client: TestClient, method: str) -> None:
    """ER-3, CA-6.2: 405 with Allow: GET."""
    response = client.request(method, HISTORY_PATH)

    assert response.status_code == 405
    assert response.headers["allow"] == "GET"
    assert response.json() == METHOD_NOT_ALLOWED


def test_er_4_trailing_slash_is_not_found(client_with_customers: TestClient) -> None:
    """ER-4, CA-6.1: POST /simulations/ is an unknown route; no redirection."""
    response = client_with_customers.post(f"{SIMULATIONS_PATH}/", json=SI_1, follow_redirects=False)

    assert response.status_code == 404
    assert response.json() == NOT_FOUND
    assert "location" not in response.headers


def test_er_5_internal_failure_is_500_without_details(
    app: FastAPI, client_with_customers: TestClient
) -> None:
    """ER-5, CA-6.1: the store fails on both routes; the client gets a generic message."""

    def broken_store() -> SimulationStore:
        return BrokenSimulationStore()

    app.dependency_overrides[get_simulation_store] = broken_store
    responses = [
        post_simulation(client_with_customers, SI_1),
        client_with_customers.get(HISTORY_PATH),
    ]

    for response in responses:
        assert response.status_code == 500
        assert response.headers["content-type"].startswith("application/json")
        assert response.json() == INTERNAL_ERROR
        for leaked in ("Traceback", "RuntimeError", "secret", "/srv", ".db", "app.repositories"):
            assert leaked not in response.text


def test_er_6_save_from_the_frontend_carries_the_allowed_origin(
    client_with_customers: TestClient,
) -> None:
    """ER-6, CA-6.3: the dashboard can save from the browser."""
    response = post_simulation(client_with_customers, SI_1, headers={"origin": FRONTEND})

    assert response.status_code == 201
    assert response.headers[ALLOW_ORIGIN] == FRONTEND


def test_history_from_the_frontend_carries_the_allowed_origin(
    client_with_customers: TestClient,
) -> None:
    """CA-6.3: the dashboard can read the history from the browser."""
    response = client_with_customers.get(HISTORY_PATH, headers={"origin": FRONTEND})

    assert response.status_code == 200
    assert response.headers[ALLOW_ORIGIN] == FRONTEND


@pytest.mark.parametrize(("path", "method"), [(SIMULATIONS_PATH, "POST"), (HISTORY_PATH, "GET")])
def test_er_7_preflight_from_the_frontend_is_accepted(
    client: TestClient, path: str, method: str
) -> None:
    """ER-7, CA-6.3: 200 for the preflight of the save and of the history."""
    response = _preflight(client, path, method, FRONTEND)

    assert response.status_code == 200
    assert response.headers[ALLOW_ORIGIN] == FRONTEND


def test_er_8_other_origins_get_no_permission(client_with_customers: TestClient) -> None:
    """ER-8, CA-6.3: neither the save nor its preflight carry the header for another origin."""
    saved = post_simulation(client_with_customers, SI_1, headers={"origin": OTHER_ORIGIN})
    preflight = _preflight(client_with_customers, SIMULATIONS_PATH, "POST", OTHER_ORIGIN)

    assert saved.status_code == 201
    assert ALLOW_ORIGIN not in saved.headers
    assert ALLOW_ORIGIN not in preflight.headers


def test_er_9_every_answer_is_json(client_with_customers: TestClient) -> None:
    """ER-9, CA-6.1: SI-1, HI-1, SV-1, SC-1, HI-10 and ER-1 all answer JSON."""
    responses = [
        post_simulation(client_with_customers, SI_1),
        client_with_customers.get(HISTORY_PATH),
        post_simulation(client_with_customers, {}),
        post_simulation(client_with_customers, {**SI_1, "customer_id": 999}),
        client_with_customers.get(history_path(999)),
        client_with_customers.get(SIMULATIONS_PATH),
    ]

    assert [response.status_code for response in responses] == [201, 200, 422, 404, 404, 405]
    for response in responses:
        assert response.headers["content-type"].startswith("application/json")


@pytest.mark.parametrize(
    ("path", "allow"),
    [
        pytest.param(CUSTOMERS_PATH, "GET, POST", id="customers"),
        pytest.param(f"{CUSTOMERS_PATH}/1", "DELETE, GET", id="customer-detail"),
        pytest.param("/pricing/quote", "POST", id="quote"),
    ],
)
def test_er_10_existing_routes_keep_their_allow(client: TestClient, path: str, allow: str) -> None:
    """ER-10, CA-6.2: the new routes change no Allow header of the routes before them.

    Spec 007 CA-1.6 made DELETE a method of the customer detail, so the probe is PUT, which no
    path here allows, and that path now announces "DELETE, GET".
    """
    response = client.put(path)

    assert response.status_code == 405
    assert response.headers["allow"] == allow
