"""POST /pricing/quote (spec 002): validates, normalizes and translates; it calculates nothing.

The amounts come from the quote service of spec 001 (constitution principle 3, ADR 0004).
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_rate_source
from app.api.validation import read_json_object
from app.schemas.pricing import QuoteRequest, QuoteResponse
from app.services.pricing import TaxRateSource, quote

router = APIRouter()


@router.post("/pricing/quote", response_model=QuoteResponse)
def post_quote(
    payload: Annotated[dict[str, object], Depends(read_json_object)],
    rates: Annotated[TaxRateSource, Depends(get_rate_source)],
) -> QuoteResponse:
    """Monthly quote for a number of users and a country, without saving anything (RF-1)."""
    request = QuoteRequest.model_validate(payload)
    return QuoteResponse.from_quote(quote(request.users, request.country, rates))
