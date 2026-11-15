"""Interactive documentation of the customer routes (level I), spec 003 task T-17 (RNF-4).

The body of POST /customers is read by hand (plan 002 DT-1), so the route must declare it; and
the documented errors must show the single format, not the framework's own.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.api.customer_requests import AL_1, AL_1_RESPONSE

LIST_PATH = "/customers"
DETAIL_PATH = "/customers/{customer_id}"


def _paths(client: TestClient) -> dict[str, Any]:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths: dict[str, Any] = response.json()["paths"]
    return paths


def _example(operation: dict[str, Any], status: str) -> Any:
    return operation["responses"][status]["content"]["application/json"]["example"]


def test_registration_documents_its_body_and_its_201(client: TestClient) -> None:
    """RNF-4: required JSON body with the five fields and the examples of spec section 5."""
    operation = _paths(client)[LIST_PATH]["post"]
    media = operation["requestBody"]["content"]["application/json"]

    assert operation["requestBody"]["required"] is True
    assert set(media["schema"]["properties"]) == set(AL_1)
    assert media["schema"]["additionalProperties"] is False
    assert media["schema"]["properties"]["plan"]["enum"] == ["starter", "business", "enterprise"]
    assert media["example"] == AL_1
    assert _example(operation, "201") == AL_1_RESPONSE


def test_list_documents_its_parameters_and_its_200(client: TestClient) -> None:
    """RNF-4: q, limit and offset with a description, and the list example of section 5."""
    operation = _paths(client)[LIST_PATH]["get"]
    parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}

    assert set(parameters) == {"q", "limit", "offset"}
    assert all(parameter["description"] for parameter in parameters.values())
    assert all(parameter["required"] is False for parameter in parameters.values())
    assert _example(operation, "200") == {"items": [AL_1_RESPONSE], "total": 1}


def test_detail_documents_its_200(client: TestClient) -> None:
    """RNF-4: the detail returns the same object as the registration."""
    operation = _paths(client)[DETAIL_PATH]["get"]

    assert _example(operation, "200") == AL_1_RESPONSE


@pytest.mark.parametrize(
    ("path", "method", "statuses"),
    [
        pytest.param(LIST_PATH, "post", {"409": "conflict", "422": "validation_error"}, id="post"),
        pytest.param(LIST_PATH, "get", {"422": "validation_error"}, id="list"),
        pytest.param(DETAIL_PATH, "get", {"404": "not_found"}, id="detail"),
    ],
)
def test_documented_errors_use_the_single_format(
    client: TestClient, path: str, method: str, statuses: dict[str, str]
) -> None:
    """RNF-4, RNF-3: every documented error is {"error": {code, message, details}}."""
    operation = _paths(client)[path][method]
    documented_errors = {status for status in operation["responses"] if status[0] in "45"}

    assert documented_errors == set(statuses)
    for status, code in statuses.items():
        example = _example(operation, status)
        assert set(example) == {"error"}
        assert set(example["error"]) == {"code", "message", "details"}
        assert example["error"]["code"] == code
    # The framework's own 422 schema must not be advertised: the API never answers with it.
    assert "HTTPValidationError" not in str(operation)


def test_interactive_docs_page_is_still_served(client: TestClient) -> None:
    """RNF-4: /docs responds with the customer routes included."""
    assert client.get("/docs").status_code == 200
    assert {LIST_PATH, DETAIL_PATH, "/pricing/quote"} <= set(_paths(client))
