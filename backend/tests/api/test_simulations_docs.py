"""Interactive documentation of the simulation routes (level I), spec 004 task T-11 (RNF-5).

The body of POST /simulations is read by hand (plan 002 DT-1), so the route must declare it.
FastAPI drops null values from examples, so "to_users": null must be restored (plan DT-11).
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.api.simulation_requests import SI_1, SI_1_RESPONSE

SAVE_PATH = "/simulations"
HISTORY_PATH = "/customers/{customer_id}/simulations"


def _paths(client: TestClient) -> dict[str, Any]:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths: dict[str, Any] = response.json()["paths"]
    return paths


def _example(operation: dict[str, Any], status: str) -> Any:
    return operation["responses"][status]["content"]["application/json"]["example"]


def test_save_documents_its_body_and_its_201(client: TestClient) -> None:
    """RNF-5: required JSON body with the four fields and the examples of spec section 5."""
    operation = _paths(client)[SAVE_PATH]["post"]
    media = operation["requestBody"]["content"]["application/json"]

    assert operation["requestBody"]["required"] is True
    assert set(media["schema"]["properties"]) == set(SI_1)
    assert media["schema"]["additionalProperties"] is False
    assert media["example"] == SI_1
    assert _example(operation, "201") == SI_1_RESPONSE


def test_history_documents_its_parameters_and_its_200(client: TestClient) -> None:
    """RNF-5: limit and offset with a description, and a page with the section 5 example."""
    operation = _paths(client)[HISTORY_PATH]["get"]
    parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}

    assert set(parameters) == {"customer_id", "limit", "offset"}
    assert all(parameters[name]["description"] for name in ("limit", "offset"))
    assert _example(operation, "200") == {"items": [SI_1_RESPONSE], "total": 1}


@pytest.mark.parametrize(
    ("path", "method", "status"),
    [(SAVE_PATH, "post", "201"), (HISTORY_PATH, "get", "200")],
)
def test_open_tier_keeps_its_null_end(
    client: TestClient, path: str, method: str, status: str
) -> None:
    """RNF-5, CA-4.7: the documented tier 3 shows "to_users": null, as the API answers."""
    example = _example(_paths(client)[path][method], status)
    simulation = example["items"][0] if "items" in example else example

    assert simulation["tiers"][2]["to_users"] is None
    assert "to_users" in simulation["tiers"][2]


@pytest.mark.parametrize(
    ("path", "method", "statuses"),
    [
        pytest.param(SAVE_PATH, "post", {"404": "not_found", "422": "validation_error"}, id="save"),
        pytest.param(
            HISTORY_PATH, "get", {"404": "not_found", "422": "validation_error"}, id="history"
        ),
    ],
)
def test_documented_errors_use_the_single_format(
    client: TestClient, path: str, method: str, statuses: dict[str, str]
) -> None:
    """RNF-5, RNF-4: every documented error is {"error": {code, message, details}}."""
    operation = _paths(client)[path][method]
    documented_errors = {status for status in operation["responses"] if status[0] in "45"}

    assert documented_errors == set(statuses)
    for status, code in statuses.items():
        example = _example(operation, status)
        assert set(example) == {"error"}
        assert set(example["error"]) == {"code", "message", "details"}
        assert example["error"]["code"] == code
    assert "HTTPValidationError" not in str(operation)


def test_both_routes_are_in_the_docs(client: TestClient) -> None:
    """RNF-5: /docs responds and lists the new routes next to the old ones."""
    assert client.get("/docs").status_code == 200
    assert {SAVE_PATH, HISTORY_PATH, "/customers", "/pricing/quote"} <= set(_paths(client))
