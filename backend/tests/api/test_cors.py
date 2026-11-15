"""CORS limited to the frontend origin (level I), spec 002 task T-14.

Covers RF-9 (CA-9.1 to CA-9.4) with cases O-10, O-11 and O-12.
"""

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.main import create_app
from tests.api.quote_requests import QUOTE_PATH, SPEC_SECTION_5_EXAMPLE, post_quote

FRONTEND = "http://localhost:4200"
OTHER_ORIGIN = "http://otro-origen.example"
ALLOW_ORIGIN = "access-control-allow-origin"


def _preflight(client: TestClient, origin: str) -> dict[str, str]:
    response = client.options(
        QUOTE_PATH,
        headers={
            "origin": origin,
            "access-control-request-method": "POST",
            "access-control-request-headers": "content-type",
        },
    )
    return {"status": str(response.status_code), **response.headers}


def test_preflight_from_the_frontend_is_allowed(client: TestClient) -> None:
    """O-10, CA-9.1, CA-9.2: 200, the frontend origin, POST and Content-Type allowed."""
    headers = _preflight(client, FRONTEND)

    assert headers["status"] == "200"
    assert headers[ALLOW_ORIGIN] == FRONTEND
    assert "POST" in headers["access-control-allow-methods"]
    assert "content-type" in headers["access-control-allow-headers"].lower()


def test_preflight_from_another_origin_gets_no_permission(client: TestClient) -> None:
    """O-11, CA-9.4: no Access-Control-Allow-Origin, so the browser blocks the call."""
    assert ALLOW_ORIGIN not in _preflight(client, OTHER_ORIGIN)


def test_quote_from_the_frontend_carries_the_allowed_origin(client: TestClient) -> None:
    """O-12, CA-9.3: same answer as Q-4, plus Access-Control-Allow-Origin."""
    body = '{"users": 15, "country": "ES"}'
    response = post_quote(client, body, headers={"origin": FRONTEND})

    assert response.status_code == 200
    assert response.json() == SPEC_SECTION_5_EXAMPLE
    assert response.headers[ALLOW_ORIGIN] == FRONTEND


def test_quote_from_another_origin_gets_no_permission(client: TestClient) -> None:
    """CA-9.4: a POST from another origin is answered without Access-Control-Allow-Origin."""
    body = '{"users": 15, "country": "ES"}'
    response = post_quote(client, body, headers={"origin": OTHER_ORIGIN})

    assert ALLOW_ORIGIN not in response.headers


def test_allowed_origin_is_configurable(database_url: str, migrated_engine: Engine) -> None:
    """CA-9.1: another configured origin replaces the default one."""
    app = create_app(database_url=database_url, frontend_origin="http://127.0.0.1:4300")

    with TestClient(app) as client:
        assert _preflight(client, "http://127.0.0.1:4300")[ALLOW_ORIGIN] == "http://127.0.0.1:4300"
        assert ALLOW_ORIGIN not in _preflight(client, FRONTEND)
