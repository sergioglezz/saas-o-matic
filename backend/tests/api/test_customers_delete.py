"""DELETE /customers/{id} (level I), spec 007 task T-02.

Cases BR-1 to BR-7, BR-9 and BR-10 of the spec table (RF-1, CA-1.1 to CA-1.7).
"""

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.api.customer_requests import AL_1, CUSTOMERS_PATH, post_customer, total_customers
from tests.api.simulation_requests import (
    create_starting_customers,
    history_path,
    post_simulation,
    saved_simulations,
    simulation,
)

FRONTEND = "http://localhost:4200"
NOT_FOUND = {"error": {"code": "not_found", "message": "Recurso no encontrado", "details": []}}
METHOD_NOT_ALLOWED = {
    "error": {"code": "method_not_allowed", "message": "Método no permitido", "details": []}
}


def _path(customer_id: int | str) -> str:
    return f"{CUSTOMERS_PATH}/{customer_id}"


def _count(app: FastAPI, sql: str) -> int:
    with app.state.session_factory() as session:
        count: int = session.execute(text(sql)).scalar_one()
        return count


@pytest.fixture
def with_history(client: TestClient) -> TestClient:
    """The six starting customers of spec 004; Acme (1) with 2 simulations, Lusitânia (2) with 1."""
    create_starting_customers(client)
    for body in (simulation(), simulation(active_users=60), simulation(customer_id=2)):
        assert post_simulation(client, body).status_code == 201
    return client


def test_br1_deleting_a_customer_without_history(client: TestClient) -> None:
    """BR-1, CA-1.1: 204 without a body; the detail is 404 and the list has one less."""
    post_customer(client, AL_1)

    response = client.delete(_path(1))

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(_path(1)).status_code == 404
    assert total_customers(client) == 0


def test_br2_deleting_a_customer_takes_its_history(with_history: TestClient, app: FastAPI) -> None:
    """BR-2, CA-1.1 and CA-1.4: its simulations and tiers go; the other customers keep theirs."""
    response = with_history.delete(_path(1))

    assert response.status_code == 204
    assert _count(app, "SELECT count(*) FROM simulations WHERE customer_id = 1") == 0
    assert _count(app, "SELECT count(*) FROM simulation_tiers") == 3
    assert with_history.get(history_path(2)).json()["total"] == 1
    assert total_customers(with_history) == 5


def test_br3_an_unknown_customer_is_404_and_nothing_is_deleted(
    with_history: TestClient, app: FastAPI
) -> None:
    """BR-3, CA-1.3."""
    response = with_history.delete(_path(999))

    assert response.status_code == 404
    assert response.json() == NOT_FOUND
    assert total_customers(with_history) == 6
    assert saved_simulations(app) == 3


@pytest.mark.parametrize("customer_id", ["abc", "0", "01", "-1"])
def test_br4_what_is_not_an_id_is_404(with_history: TestClient, customer_id: str) -> None:
    """BR-4, CA-1.3: the same rules as the detail (003 CA-6.3, D-4)."""
    response = with_history.delete(_path(customer_id))

    assert response.status_code == 404
    assert response.json() == NOT_FOUND
    assert total_customers(with_history) == 6


def test_br5_deleting_twice_is_204_and_then_404(with_history: TestClient) -> None:
    """BR-5: the second request, from another tab for instance, finds nothing to delete."""
    assert with_history.delete(_path(1)).status_code == 204

    second = with_history.delete(_path(1))

    assert second.status_code == 404
    assert second.json() == NOT_FOUND


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH"])
def test_br6_other_methods_name_delete_and_get(with_history: TestClient, method: str) -> None:
    """BR-6, CA-1.6: 405 with Allow: DELETE, GET, and the customer stays."""
    response = with_history.request(method, _path(1))

    assert response.status_code == 405
    assert response.headers["allow"] == "DELETE, GET"
    assert response.json() == METHOD_NOT_ALLOWED
    assert with_history.get(_path(1)).status_code == 200


def test_br7_the_frontend_may_delete_from_the_browser(with_history: TestClient) -> None:
    """BR-7, CA-1.6: the preflight of DELETE is accepted, and so is the request itself."""
    preflight = with_history.options(
        _path(1), headers={"origin": FRONTEND, "access-control-request-method": "DELETE"}
    )
    response = with_history.delete(_path(1), headers={"origin": FRONTEND})

    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == FRONTEND
    assert "DELETE" in preflight.headers["access-control-allow-methods"]
    assert response.status_code == 204
    assert response.headers["access-control-allow-origin"] == FRONTEND


def test_br9_the_tax_id_is_freed_and_the_id_is_not_reused(client: TestClient) -> None:
    """BR-9, CA-1.5: the same tax id registers again with a new, greater id (003 CA-1.3)."""
    post_customer(client, AL_1)
    client.delete(_path(1))

    again = post_customer(client, AL_1)

    assert again.status_code == 201
    assert again.json()["id"] == 2


def test_br10_the_route_is_documented_with_204_and_404(client: TestClient) -> None:
    """BR-10, CA-1.7: no body in the 204 and the single format in the 404."""
    paths: dict[str, Any] = client.get("/openapi.json").json()["paths"]
    responses = paths["/customers/{customer_id}"]["delete"]["responses"]

    assert set(responses) == {"204", "404"}
    assert "content" not in responses["204"]
    assert responses["404"]["content"]["application/json"]["example"] == {
        "error": {"code": "not_found", "message": "Recurso no encontrado", "details": []}
    }
