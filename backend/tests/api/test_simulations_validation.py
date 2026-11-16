"""Save errors over HTTP (level I), spec 004 task T-08.

RF-2 (CA-2.1 to CA-2.8), RF-3 (CA-3.1, CA-3.2, CA-3.4) and RF-1 (CA-1.4) with tables 6.3 (SV)
and 6.4 (SC). Nothing may be saved after any of them; the rows are counted in the database, so
these tests do not depend on the history route.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.api.simulation_requests import (
    SI_1,
    SettableClock,
    change_rate,
    create_starting_customers,
    post_simulation,
    saved_simulations,
    simulation,
)
from tests.simulations_data import BODY, CNS, SV_CASES, USERS, USR, raw_body

NOT_FOUND = {"error": {"code": "not_found", "message": "Recurso no encontrado", "details": []}}


def _details(body: dict[str, object]) -> set[tuple[str, str]]:
    error = body["error"]
    assert isinstance(error, dict)
    assert (error["code"], error["message"]) == ("validation_error", "Datos no válidos")
    return {(detail["field"], detail["message"]) for detail in error["details"]}


@pytest.fixture
def client_with_customers(client: TestClient, simulation_clock: SettableClock) -> TestClient:
    create_starting_customers(client)
    return client


@pytest.mark.parametrize(("changes", "expected"), SV_CASES)
def test_sv_invalid_bodies_are_422_and_save_nothing(
    app: FastAPI,
    client_with_customers: TestClient,
    changes: dict[str, str | None],
    expected: set[tuple[str, str]],
) -> None:
    """SV-1 to SV-16, CA-2.1 to CA-2.6, CA-2.8, CA-1.4: one detail per field, all at once."""
    response = post_simulation(client_with_customers, raw_body(changes))

    assert response.status_code == 422
    assert _details(response.json()) == expected
    assert saved_simulations(app) == 0


@pytest.mark.parametrize(
    ("raw", "content_type"),
    [
        pytest.param("no es json", "application/json", id="not-json"),
        pytest.param("[1]", "application/json", id="list"),
        pytest.param(raw_body({}), "text/plain", id="text-plain"),
    ],
)
def test_sv_17_body_must_be_a_json_object(
    app: FastAPI, client_with_customers: TestClient, raw: str, content_type: str
) -> None:
    """SV-17, CA-2.7 (002 CA-7.1 to CA-7.3): the single body detail."""
    response = post_simulation(client_with_customers, raw, content_type=content_type)

    assert response.status_code == 422
    assert _details(response.json()) == {("body", BODY)}
    assert saved_simulations(app) == 0


def test_sv_18_validation_goes_before_the_customer(
    app: FastAPI, client_with_customers: TestClient
) -> None:
    """SV-18, CA-3.2: an unknown customer with a wrong value is 422, never 404."""
    response = post_simulation(client_with_customers, simulation(customer_id=999, active_users=-1))

    assert response.status_code == 422
    assert _details(response.json()) == {(USERS, USR)}
    assert saved_simulations(app) == 0


@pytest.mark.parametrize(
    "customer_id",
    [pytest.param(999, id="SC-1"), pytest.param(2**63 - 1, id="SC-2-largest-id")],
)
def test_sc_unknown_customer_is_404(
    app: FastAPI, client_with_customers: TestClient, customer_id: int
) -> None:
    """SC-1, SC-2, CA-3.1: 404 not_found with no details, without an internal error."""
    response = post_simulation(client_with_customers, simulation(customer_id=customer_id))

    assert response.status_code == 404
    assert response.json() == NOT_FOUND
    assert saved_simulations(app) == 0


def test_sc_3_customer_country_without_rate(
    app: FastAPI, client_with_customers: TestClient
) -> None:
    """SC-3, CA-3.4, spec decision D-4: 422 with the CNS detail on customer_id."""
    change_rate(app, "PT", None)

    response = post_simulation(client_with_customers, simulation(customer_id=2, active_users=1))

    assert response.status_code == 422
    assert _details(response.json()) == {("customer_id", CNS)}


def test_sc_4_failed_saves_leave_nothing(app: FastAPI, client_with_customers: TestClient) -> None:
    """SC-4, CA-1.4: after SC-1 to SC-3 there is no simulation, and a valid one still saves."""
    post_simulation(client_with_customers, simulation(customer_id=999))
    change_rate(app, "PT", None)
    post_simulation(client_with_customers, simulation(customer_id=2, active_users=1))

    assert saved_simulations(app) == 0
    assert post_simulation(client_with_customers, SI_1).status_code == 201
