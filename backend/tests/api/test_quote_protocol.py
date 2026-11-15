"""Methods not allowed, internal failure and content type (level I), spec 002 task T-13.

Covers RF-8 (CA-8.1) and RF-6 (CA-6.2, CA-6.5, CA-6.6) with cases O-3, O-4, O-5 and O-8.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_rate_source
from app.services.pricing import TaxRateSource
from tests.api.quote_requests import QUOTE_PATH, post_quote

Q4_BODY = '{"users": 15, "country": "ES"}'
METHOD_NOT_ALLOWED = {
    "error": {"code": "method_not_allowed", "message": "Método no permitido", "details": []}
}


class BrokenRates:
    """A rate source whose database is down, with internal details in the exception."""

    def get_rate_bp(self, country: str) -> int | None:
        raise RuntimeError("database file /srv/secret/saas.db is locked in app.repositories")


@pytest.mark.parametrize(
    "method",
    [
        pytest.param("GET", id="O-3"),
        pytest.param("PUT", id="O-4-PUT"),
        pytest.param("PATCH", id="O-4-PATCH"),
        pytest.param("DELETE", id="O-4-DELETE"),
        pytest.param("OPTIONS", id="O-4-OPTIONS-without-preflight"),
    ],
)
def test_other_methods_return_405_in_the_single_format(client: TestClient, method: str) -> None:
    """O-3, O-4, CA-8.1, CA-6.2: 405 method_not_allowed, empty details, Allow: POST."""
    response = client.request(method, QUOTE_PATH)

    assert response.status_code == 405
    assert response.headers["allow"] == "POST"
    assert response.json() == METHOD_NOT_ALLOWED


def test_head_returns_405_with_allow_and_no_body(client: TestClient) -> None:
    """O-4, CA-8.1: HEAD carries no body, so only the status and the Allow header count."""
    response = client.head(QUOTE_PATH)

    assert response.status_code == 405
    assert response.headers["allow"] == "POST"
    assert response.content == b""


def test_internal_failure_returns_500_without_internal_details(app: FastAPI) -> None:
    """O-5, CA-6.2, CA-6.5: the rate source fails; the client gets a generic message only."""

    def broken_rates() -> TaxRateSource:
        return BrokenRates()

    app.dependency_overrides[get_rate_source] = broken_rates
    with TestClient(app, raise_server_exceptions=False) as client:
        response = post_quote(client, Q4_BODY)

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Error interno del servidor", "details": []}
    }
    for leaked in ("Traceback", "RuntimeError", "secret", "/srv", ".db", "app.repositories"):
        assert leaked not in response.text


def test_every_kind_of_response_is_json(app: FastAPI) -> None:
    """O-8, CA-6.6: Q-4 (200), E-1 (422), O-3 (405), O-5 (500) and O-13 (404)."""
    with TestClient(app, raise_server_exceptions=False) as client:
        responses = {
            "Q-4": post_quote(client, Q4_BODY),
            "E-1": post_quote(client, '{"users": -1, "country": "ES"}'),
            "O-3": client.get(QUOTE_PATH),
            "O-13": client.get("/no-existe"),
        }
        app.dependency_overrides[get_rate_source] = lambda: BrokenRates()
        responses["O-5"] = post_quote(client, Q4_BODY)

    statuses = {case: response.status_code for case, response in responses.items()}
    assert statuses == {"Q-4": 200, "E-1": 422, "O-3": 405, "O-13": 404, "O-5": 500}
    for case, response in responses.items():
        assert response.headers["content-type"].startswith("application/json"), case
