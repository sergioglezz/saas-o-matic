"""The single place where a domain error becomes an HTTP response (00-spec-first section 6).

Domain errors carry no user-facing text (plan 001 DT-8). The table lives in the API layer and
not in app.core, so the error format itself knows no feature (spec 003 RF-7, plan DT-14).
"""

from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.api.validation import validation_error
from app.core.errors import ApiError, FieldError, conflict, error_response, not_found
from app.domain.errors import (
    CustomerNotFoundError,
    DuplicateTaxIdError,
    InvalidApiCallsError,
    InvalidSpanishTaxIdError,
    InvalidStorageError,
    InvalidTaxIdFormatError,
    InvalidUsersError,
    UnsupportedCountryError,
    UnsupportedCustomerCountryError,
    UnsupportedTaxIdTypeError,
)
from app.schemas.customers import (
    TAX_ID_DUPLICATED_MESSAGE,
    TAX_ID_INVALID_MESSAGE,
    TAX_ID_SPANISH_MESSAGE,
    TAX_ID_UNSUPPORTED_TYPE_MESSAGE,
)
from app.schemas.pricing import COUNTRY_UNSUPPORTED_MESSAGE, USERS_INVALID_MESSAGE
from app.schemas.simulations import (
    API_CALLS_INVALID_MESSAGE,
    CUSTOMER_COUNTRY_UNSUPPORTED_MESSAGE,
    STORAGE_INVALID_MESSAGE,
)


def _invalid_field(field: str, message: str) -> Callable[[], ApiError]:
    return lambda: validation_error([FieldError(field=field, message=message)])


_DOMAIN_ERRORS: dict[type[Exception], Callable[[], ApiError]] = {
    UnsupportedCountryError: _invalid_field("country", COUNTRY_UNSUPPORTED_MESSAGE),
    InvalidUsersError: _invalid_field("users", USERS_INVALID_MESSAGE),
    InvalidTaxIdFormatError: _invalid_field("tax_id", TAX_ID_INVALID_MESSAGE),
    InvalidSpanishTaxIdError: _invalid_field("tax_id", TAX_ID_SPANISH_MESSAGE),
    UnsupportedTaxIdTypeError: _invalid_field("tax_id", TAX_ID_UNSUPPORTED_TYPE_MESSAGE),
    # The detail names the field so the form can show the text next to it (flow 1 of the 00).
    DuplicateTaxIdError: lambda: conflict(
        [FieldError(field="tax_id", message=TAX_ID_DUPLICATED_MESSAGE)]
    ),
    CustomerNotFoundError: not_found,
    # Spec 004: the schema stops storage and API calls first; these back the service (DT-2).
    InvalidStorageError: _invalid_field("storage_gb", STORAGE_INVALID_MESSAGE),
    InvalidApiCallsError: _invalid_field("api_calls_per_month", API_CALLS_INVALID_MESSAGE),
    # On customer_id: a simulation request has no country field (CA-3.4, plan 004 DT-3).
    UnsupportedCustomerCountryError: _invalid_field(
        "customer_id", CUSTOMER_COUNTRY_UNSUPPORTED_MESSAGE
    ),
}


def register_domain_error_handlers(app: FastAPI) -> None:
    for error_type in _DOMAIN_ERRORS:
        app.add_exception_handler(error_type, _handle_domain_error)


async def _handle_domain_error(_request: Request, exc: Exception) -> Response:
    return error_response(_DOMAIN_ERRORS[type(exc)]())
