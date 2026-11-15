"""POST /pricing/quote (spec 002): validates, normalizes and translates; it calculates nothing.

The amounts come from the quote service of spec 001 (constitution principle 3, ADR 0004).
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import ValidationError

from app.api.dependencies import get_rate_source
from app.api.validation import field_errors, read_json_object, validation_error
from app.core.errors import ApiError, FieldError
from app.schemas.pricing import (
    COUNTRY_UNSUPPORTED_MESSAGE,
    INVALID_FIELD_MESSAGES,
    QUOTE_REQUEST_EXAMPLE,
    QUOTE_RESPONSE_EXAMPLE,
    QuoteRequest,
    QuoteResponse,
    normalize_country,
)
from app.services.pricing import TaxRateSource, country_is_supported, quote

router = APIRouter()

# The body is read by hand (plan 002 DT-1), so FastAPI cannot infer it for /docs (RNF-5).
_REQUEST_BODY_DOC = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": QuoteRequest.model_json_schema(),
                "example": QUOTE_REQUEST_EXAMPLE,
            }
        },
    }
}
_RESPONSES_DOC: dict[int | str, dict[str, object]] = {
    200: {"content": {"application/json": {"example": QUOTE_RESPONSE_EXAMPLE}}}
}


@router.post(
    "/pricing/quote",
    response_model=QuoteResponse,
    openapi_extra=_REQUEST_BODY_DOC,
    responses=_RESPONSES_DOC,
)
def post_quote(
    payload: Annotated[dict[str, object], Depends(read_json_object)],
    rates: Annotated[TaxRateSource, Depends(get_rate_source)],
) -> QuoteResponse:
    """Monthly quote for a number of users and a country, without saving anything (RF-1)."""
    try:
        request = QuoteRequest.model_validate(payload)
    except ValidationError as error:
        raise _invalid_request(error, payload, rates) from None
    # An unsupported country reaching here raises UnsupportedCountryError, mapped to 422 in
    # app.core.errors (E-17).
    return QuoteResponse.from_quote(quote(request.users, request.country, rates))


def restore_openapi_examples(schema: dict[str, Any]) -> dict[str, Any]:
    """Put the exact 200 example back into the generated OpenAPI schema (RNF-5).

    FastAPI drops every null value when it builds /openapi.json, examples included, which would
    hide "to_users": null in the last tier of the documented response.
    """
    responses = schema["paths"]["/pricing/quote"]["post"]["responses"]
    responses["200"]["content"]["application/json"]["example"] = QUOTE_RESPONSE_EXAMPLE
    return schema


def _invalid_request(
    error: ValidationError, payload: dict[str, object], rates: TaxRateSource
) -> ApiError:
    """422 with one detail per invalid field (CA-6.3).

    When the country itself is well formed, it is also checked against the rate table, so a
    request with both an invalid users value and an unsupported country reports both (E-35).
    """
    details = field_errors(error, INVALID_FIELD_MESSAGES)
    country = payload.get("country")
    country_is_well_formed = isinstance(country, str) and all(d.field != "country" for d in details)
    if country_is_well_formed and not country_is_supported(normalize_country(str(country)), rates):
        details.append(FieldError(field="country", message=COUNTRY_UNSUPPORTED_MESSAGE))
    return validation_error(details)
