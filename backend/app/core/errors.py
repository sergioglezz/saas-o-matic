"""Single API error format {"error": {code, message, details}} (spec 002 RF-6, 00-spec-first 8.4).

Every error response is built here, so the format and the top-level texts live in one place
(00-spec-first section 6, plan 002 DT-5).
"""

from dataclasses import dataclass, field

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.errors import InvalidUsersError, UnsupportedCountryError
from app.schemas.pricing import COUNTRY_UNSUPPORTED_MESSAGE, USERS_INVALID_MESSAGE

VALIDATION_ERROR_MESSAGE = "Datos no válidos"
NOT_FOUND_MESSAGE = "Recurso no encontrado"
INTERNAL_ERROR_MESSAGE = "Error interno del servidor"


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
    app.add_exception_handler(UnsupportedCountryError, _handle_domain_error)
    app.add_exception_handler(InvalidUsersError, _handle_domain_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(Exception, _handle_unexpected_error)


# Domain errors carry no user-facing text (plan 001 DT-8); this is the single place where they
# become HTTP responses (00-spec-first section 6).
_DOMAIN_ERROR_DETAILS: dict[type[Exception], FieldError] = {
    UnsupportedCountryError: FieldError(field="country", message=COUNTRY_UNSUPPORTED_MESSAGE),
    InvalidUsersError: FieldError(field="users", message=USERS_INVALID_MESSAGE),
}


async def _handle_domain_error(_request: Request, exc: Exception) -> Response:
    detail = _DOMAIN_ERROR_DETAILS[type(exc)]
    return error_response(
        ApiError(
            status=422, code="validation_error", message=VALIDATION_ERROR_MESSAGE, details=[detail]
        )
    )


async def _handle_api_error(_request: Request, exc: Exception) -> Response:
    assert isinstance(exc, ApiError)
    return error_response(exc)


async def _handle_http_exception(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, StarletteHTTPException)
    if exc.status_code == 404:
        return error_response(ApiError(status=404, code="not_found", message=NOT_FOUND_MESSAGE))
    # Statuses this spec does not map yet keep FastAPI's default response.
    return await http_exception_handler(request, exc)


async def _handle_unexpected_error(_request: Request, _exc: Exception) -> Response:
    # The exception is still logged by the server; the client only gets a generic message.
    return error_response(
        ApiError(status=500, code="internal_error", message=INTERNAL_ERROR_MESSAGE)
    )
