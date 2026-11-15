"""Customer routes (spec 003): they read, validate, call the service and answer.

No business rule and no SQL here (constitution principle 3): the tax id control is domain
code and the storage is behind CustomerStore.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import ValidationError

from app.api.countries import invalid_request
from app.api.dependencies import get_customer_store, get_now, get_rate_source
from app.api.validation import read_json_object
from app.schemas.customers import CUSTOMER_INVALID_MESSAGES, CustomerCreate, CustomerResponse
from app.services.customers import CustomerStore, register_customer
from app.services.pricing import TaxRateSource

router = APIRouter()


@router.post("/customers", status_code=201, response_model=CustomerResponse)
def post_customer(
    payload: Annotated[dict[str, object], Depends(read_json_object)],
    customers: Annotated[CustomerStore, Depends(get_customer_store)],
    rates: Annotated[TaxRateSource, Depends(get_rate_source)],
    now: Annotated[datetime, Depends(get_now)],
) -> CustomerResponse:
    """Register a customer and return it with its id and creation instant (RF-1)."""
    try:
        request = CustomerCreate.model_validate(payload)
    except ValidationError as error:
        raise invalid_request(error, CUSTOMER_INVALID_MESSAGES, payload, rates) from None
    # The service may still raise an unsupported country (VA-17) or a duplicated tax id (409);
    # app.api.error_mapping turns both into responses.
    customer = register_customer(request.to_new_customer(), customers, rates, now)
    return CustomerResponse.from_customer(customer)
