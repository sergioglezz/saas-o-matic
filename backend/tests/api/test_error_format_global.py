"""Single error format for everything the framework raises (level I), spec 003 RF-7.

Cases ER-6, ER-7 and ER-12 of table 6.9, with probe routes added only in these tests: no real
route uses typed parameters, so the safety net is exercised on purpose (review log entry 16).
"""

from typing import NoReturn

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.errors import FieldError, conflict
from tests.api.quote_requests import QUOTE_PATH, details_of


def test_framework_validation_errors_use_the_single_format(app: FastAPI) -> None:
    """ER-6, CA-7.3: one "Valor no válido" detail per parameter the framework rejects."""

    def typed(number: int, size: int = 1) -> dict[str, int]:
        return {"number": number, "size": size}

    app.add_api_route("/_probe/typed/{number}", typed, methods=["GET"])

    with TestClient(app) as client:
        response = client.get("/_probe/typed/abc?size=x")

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/json")
    error = response.json()["error"]
    assert (error["code"], error["message"]) == ("validation_error", "Datos no válidos")
    assert details_of(response) == {("number", "Valor no válido"), ("size", "Valor no válido")}
    assert len(error["details"]) == 2


def test_other_http_errors_use_the_single_format_without_internal_text(app: FastAPI) -> None:
    """ER-7, CA-7.4: same status, http_error, empty details and nothing internal leaked."""

    def teapot() -> NoReturn:
        raise HTTPException(status_code=418, detail="secret detail at /srv/internal/path.py")

    app.add_api_route("/_probe/teapot", teapot, methods=["GET"], response_model=None)

    with TestClient(app) as client:
        response = client.get("/_probe/teapot")

    assert response.status_code == 418
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "error": {"code": "http_error", "message": "Error en la petición", "details": []}
    }
    for leaked in ("secret", "/srv", ".py", "detail"):
        assert leaked not in response.text.replace('"details"', "")


def test_conflict_uses_the_single_format_with_its_detail(app: FastAPI) -> None:
    """CA-7.1: 409 conflict "El recurso ya existe" with the field detail it is given."""

    def duplicated() -> NoReturn:
        raise conflict([FieldError(field="tax_id", message="Ya existe")])

    app.add_api_route("/_probe/conflict", duplicated, methods=["POST"], response_model=None)

    with TestClient(app) as client:
        response = client.post("/_probe/conflict")

    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "El recurso ya existe",
            "details": [{"field": "tax_id", "message": "Ya existe"}],
        }
    }


def test_allow_lists_the_methods_of_every_route_on_the_path(app: FastAPI) -> None:
    """CA-7.2: two routes share a path; the 405 names the methods of both."""
    app.add_api_route("/_probe/shared", lambda: {"read": True}, methods=["GET"])
    app.add_api_route("/_probe/shared", lambda: {"created": True}, methods=["POST"])

    with TestClient(app) as client:
        response = client.delete("/_probe/shared")
        other_path = client.delete("/_probe/shared/7")

    assert response.status_code == 405
    assert response.headers["allow"] == "GET, POST"
    assert response.json() == {
        "error": {"code": "method_not_allowed", "message": "Método no permitido", "details": []}
    }
    assert other_path.status_code == 404  # a different path is not a method problem


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_quote_route_still_allows_only_post(client: TestClient, method: str) -> None:
    """ER-12, CA-7.2: the quote route keeps answering 405 with Allow: POST."""
    response = client.request(method, QUOTE_PATH)

    assert response.status_code == 405
    assert response.headers["allow"] == "POST"
