"""Interactive documentation of POST /pricing/quote (level I), spec 002 task T-15 (RNF-5, RF-1).

The body is read by hand (plan DT-1), so FastAPI cannot infer it: the route must declare it.
"""

from typing import Any

from fastapi.testclient import TestClient

from tests.api.quote_requests import QUOTE_PATH, SPEC_SECTION_5_EXAMPLE


def _quote_operation(client: TestClient) -> dict[str, Any]:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    operation: dict[str, Any] = response.json()["paths"][QUOTE_PATH]["post"]
    return operation


def test_request_body_is_documented_with_its_schema_and_example(client: TestClient) -> None:
    """RNF-5: required JSON body with users and country and the example {15, "ES"}."""
    body = _quote_operation(client)["requestBody"]
    media = body["content"]["application/json"]

    assert body["required"] is True
    assert set(media["schema"]["properties"]) == {"users", "country"}
    assert media["schema"]["additionalProperties"] is False
    assert media["example"] == {"users": 15, "country": "ES"}


def test_200_response_is_documented_with_the_example_of_spec_section_5(
    client: TestClient,
) -> None:
    """RNF-5: the 200 example is exactly the one of spec section 5."""
    media = _quote_operation(client)["responses"]["200"]["content"]["application/json"]

    assert media["example"] == SPEC_SECTION_5_EXAMPLE


def test_interactive_docs_page_is_served(client: TestClient) -> None:
    """RNF-5: /docs responds."""
    assert client.get("/docs").status_code == 200
