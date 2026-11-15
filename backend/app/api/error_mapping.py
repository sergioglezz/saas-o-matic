"""The single place where a domain error becomes an HTTP response (00-spec-first section 6).

Domain errors carry no user-facing text (plan 001 DT-8). The table lives in the API layer and
not in app.core, so the error format itself knows no feature (spec 003 RF-7, plan DT-14).
"""

from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.api.validation import validation_error
from app.core.errors import ApiError, FieldError, error_response
from app.domain.errors import InvalidUsersError, UnsupportedCountryError
from app.schemas.pricing import COUNTRY_UNSUPPORTED_MESSAGE, USERS_INVALID_MESSAGE


def _invalid_field(field: str, message: str) -> Callable[[], ApiError]:
    return lambda: validation_error([FieldError(field=field, message=message)])


_DOMAIN_ERRORS: dict[type[Exception], Callable[[], ApiError]] = {
    UnsupportedCountryError: _invalid_field("country", COUNTRY_UNSUPPORTED_MESSAGE),
    InvalidUsersError: _invalid_field("users", USERS_INVALID_MESSAGE),
}


def register_domain_error_handlers(app: FastAPI) -> None:
    for error_type in _DOMAIN_ERRORS:
        app.add_exception_handler(error_type, _handle_domain_error)


async def _handle_domain_error(_request: Request, exc: Exception) -> Response:
    return error_response(_DOMAIN_ERRORS[type(exc)]())
