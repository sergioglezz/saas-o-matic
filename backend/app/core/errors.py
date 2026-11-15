"""Single API error format {"error": {code, message, details}} (spec 002 RF-6, 00-spec-first 8.4).

Every error response is built here, so the format and the top-level texts live in one place
(00-spec-first section 6, plan 002 DT-5). This module knows no feature: domain errors are mapped
in app.api.error_mapping (spec 003 RF-7).
"""

from dataclasses import dataclass, field

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.routing import Match

VALIDATION_ERROR_MESSAGE = "Datos no válidos"
NOT_FOUND_MESSAGE = "Recurso no encontrado"
METHOD_NOT_ALLOWED_MESSAGE = "Método no permitido"
CONFLICT_MESSAGE = "El recurso ya existe"
HTTP_ERROR_MESSAGE = "Error en la petición"
# For a parameter the framework rejects before any route code runs (spec 003 CA-7.3).
INVALID_VALUE_MESSAGE = "Valor no válido"
INTERNAL_ERROR_MESSAGE = "Error interno del servidor"

_HTTP_METHODS = ("DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT")


@dataclass(frozen=True, slots=True)
class FieldError:
    field: str
    message: str


@dataclass(slots=True)
class ApiError(Exception):
    """An error the API reports on purpose, with its status and its field details."""

    status: int
    code: str
    message: str
    details: list[FieldError] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)


def not_found() -> ApiError:
    """404 not_found, for unknown routes and for resources that do not exist (002 CA-6.7)."""
    return ApiError(status=404, code="not_found", message=NOT_FOUND_MESSAGE)


def conflict(details: list[FieldError]) -> ApiError:
    """409 conflict with the field that collides (spec 003 CA-7.1)."""
    return ApiError(status=409, code="conflict", message=CONFLICT_MESSAGE, details=details)


def error_response(error: ApiError) -> JSONResponse:
    body = {
        "error": {
            "code": error.code,
            "message": error.message,
            "details": [{"field": d.field, "message": d.message} for d in error.details],
        }
    }
    return JSONResponse(body, status_code=error.status, headers=error.headers or None)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _handle_api_error)
    app.add_exception_handler(RequestValidationError, _handle_request_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(Exception, _handle_unexpected_error)


async def _handle_api_error(_request: Request, exc: Exception) -> Response:
    assert isinstance(exc, ApiError)
    return error_response(exc)


async def _handle_request_validation_error(_request: Request, exc: Exception) -> Response:
    """Safety net: the routes validate by hand, but a typed parameter must not change the format."""
    assert isinstance(exc, RequestValidationError)
    # loc is ("path" | "query" | "body", name, ...): the name is what the client sent wrong.
    fields = dict.fromkeys(
        str(item["loc"][1 if len(item["loc"]) > 1 else 0]) for item in exc.errors()
    )
    details = [FieldError(field=name, message=INVALID_VALUE_MESSAGE) for name in fields]
    return error_response(
        ApiError(
            status=422, code="validation_error", message=VALIDATION_ERROR_MESSAGE, details=details
        )
    )


async def _handle_http_exception(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, StarletteHTTPException)
    if exc.status_code == 404:
        return error_response(not_found())
    if exc.status_code == 405:
        return error_response(
            ApiError(
                status=405,
                code="method_not_allowed",
                message=METHOD_NOT_ALLOWED_MESSAGE,
                headers={"Allow": _allowed_methods(request)},
            )
        )
    # Any other status keeps its code and headers, but never its internal text (003 CA-7.4).
    return error_response(
        ApiError(
            status=exc.status_code,
            code="http_error",
            message=HTTP_ERROR_MESSAGE,
            headers=dict(exc.headers or {}),
        )
    )


def _allowed_methods(request: Request) -> str:
    """Methods served on the requested path by any route (002 CA-8.1, 003 CA-7.2).

    Starlette's own Allow header names only the first route that matches the path, so a path
    served by two routes (GET and POST /customers) would advertise half of its methods. Each
    method is tried against the routes instead of reading their ``methods``: an included router
    is one nested route that only tells whether it matches.
    """
    routes = request.app.routes
    allowed = [
        method
        for method in _HTTP_METHODS
        if any(
            route.matches({**request.scope, "method": method})[0] == Match.FULL for route in routes
        )
    ]
    return ", ".join(allowed)


async def _handle_unexpected_error(_request: Request, _exc: Exception) -> Response:
    # The exception is still logged by the server; the client only gets a generic message.
    return error_response(
        ApiError(status=500, code="internal_error", message=INTERNAL_ERROR_MESSAGE)
    )
