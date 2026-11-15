"""Single error format, 404 and 500: spec 002 RF-6 (CA-6.1, CA-6.2, CA-6.5 to CA-6.7), task T-05.

Cases O-13 and O-14 of table 6.3, plus probe routes added only in these tests.
"""

from typing import NoReturn

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import ApiError, FieldError


def _error(response_json: dict[str, object]) -> dict[str, object]:
    error = response_json["error"]
    assert isinstance(error, dict)
    return error


def test_unknown_route_returns_404_in_the_single_format(client: TestClient) -> None:
    """O-13, CA-6.2, CA-6.6, CA-6.7: unknown routes use the API error format."""
    response = client.get("/no-existe")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "error": {"code": "not_found", "message": "Recurso no encontrado", "details": []}
    }


def test_quote_path_with_trailing_slash_is_not_found(client: TestClient) -> None:
    """O-14, CA-6.7: /pricing/quote/ is a different, unknown route."""
    response = client.post("/pricing/quote/", json={"users": 15, "country": "ES"})

    assert response.status_code == 404
    assert _error(response.json())["code"] == "not_found"
    assert "location" not in response.headers


def test_trailing_slash_on_an_existing_route_is_404_not_a_redirect(app: FastAPI) -> None:
    """CA-6.7: no redirection to the route without the slash (plan 002 DT-6)."""
    app.add_api_route("/_probe/ok", lambda: {"ok": True}, methods=["GET"])

    with TestClient(app) as client:
        response = client.get("/_probe/ok/", follow_redirects=False)

    assert response.status_code == 404
    assert "location" not in response.headers


def test_unexpected_failure_returns_500_without_internal_details(app: FastAPI) -> None:
    """CA-6.2, CA-6.5, CA-6.6: generic message, empty details, nothing internal leaked."""

    def broken() -> NoReturn:
        raise RuntimeError("secret detail at /srv/internal/path.py")

    # response_model=None: a NoReturn annotation is not a response model FastAPI can build.
    app.add_api_route("/_probe/broken", broken, methods=["GET"], response_model=None)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/_probe/broken")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Error interno del servidor", "details": []}
    }
    for leaked in ("Traceback", "RuntimeError", "secret", "/srv", ".py"):
        assert leaked not in response.text


def test_api_error_uses_the_single_format_with_field_details(app: FastAPI) -> None:
    """CA-6.1: {"error": {code, message, details}} with details as a list of {field, message}."""

    def invalid() -> NoReturn:
        raise ApiError(
            status=422,
            code="validation_error",
            message="Datos no válidos",
            details=[FieldError(field="users", message="Campo obligatorio")],
        )

    app.add_api_route("/_probe/invalid", invalid, methods=["GET"], response_model=None)

    with TestClient(app) as client:
        response = client.get("/_probe/invalid")

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "Datos no válidos",
            "details": [{"field": "users", "message": "Campo obligatorio"}],
        }
    }
