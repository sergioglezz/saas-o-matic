"""POST /pricing/quote (spec 002): validates, normalizes and translates; it calculates nothing.

The amounts come from the quote service of spec 001 (constitution principle 3, ADR 0004).
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import ValidationError

from app.api.countries import invalid_request
from app.api.dependencies import get_rate_source
from app.api.validation import read_json_object
from app.schemas.pricing import (
    INVALID_FIELD_MESSAGES,
    QUOTE_REQUEST_EXAMPLE,
    QUOTE_RESPONSE_EXAMPLE,
    QuoteRequest,
    QuoteResponse,
)
from app.services.pricing import TaxRateSource, quote

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
        # Also reports an unsupported country next to the other invalid fields (E-35).
        raise invalid_request(error, INVALID_FIELD_MESSAGES, payload, rates) from None
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
