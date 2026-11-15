"""Single error format for everything the framework raises (level I), spec 003 RF-7.

Cases ER-6 and ER-7 of table 6.9, with probe routes added only in these tests: no real
route uses typed parameters, so the safety net is exercised on purpose (review log entry 16).
"""

from typing import NoReturn

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.errors import FieldError, conflict
from tests.api.quote_requests import details_of


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
