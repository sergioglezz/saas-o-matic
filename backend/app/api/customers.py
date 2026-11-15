"""Customer routes (spec 003): they read, validate, call the service and answer.

No business rule and no SQL here (constitution principle 3): the tax id control is domain
code and the storage is behind CustomerStore.
"""

import re
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import ValidationError

from app.api.countries import invalid_request
from app.api.dependencies import get_customer_store, get_now, get_rate_source
from app.api.validation import field_errors, read_json_object, validation_error
from app.core.errors import not_found
from app.schemas.customers import (
    CUSTOMER_INVALID_MESSAGES,
    LIST_INVALID_MESSAGES,
    CustomerCreate,
    CustomerListQuery,
    CustomerListResponse,
    CustomerResponse,
)
from app.services.customers import (
    CustomerStore,
    get_customer,
    register_customer,
    search_customers,
)
from app.services.pricing import TaxRateSource

router = APIRouter()

# A customer id as the API writes it: digits only, no sign and no leading zeros (CA-6.3).
_CUSTOMER_ID = re.compile(r"[1-9][0-9]{0,18}")
_LARGEST_ID = 2**63 - 1  # the largest integer SQLite can hold


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


@router.get("/customers", response_model=CustomerListResponse)
def list_customers(
    customers: Annotated[CustomerStore, Depends(get_customer_store)],
    q: Annotated[
        str | None,
        Query(description="Texto que debe aparecer en el nombre o en el identificador fiscal."),
    ] = None,
    limit: Annotated[
        str | None,
        Query(description="Máximo de clientes devueltos: entero de 1 a 100. Por defecto, 50."),
    ] = None,
    offset: Annotated[
        str | None,
        Query(description="Posición del primer cliente: entero de 0 a 1000000. Por defecto, 0."),
    ] = None,
) -> CustomerListResponse:
    """List the customers, or search them by company name or tax id (RF-5)."""
    # Declared as text so the framework never rejects them with its own format:
    # CustomerListQuery validates them and words the error (plan 003 DT-7).
    received = {"q": q, "limit": limit, "offset": offset}
    try:
        query = CustomerListQuery.model_validate(
            {name: value for name, value in received.items() if value is not None}
        )
    except ValidationError as error:
        raise validation_error(field_errors(error, LIST_INVALID_MESSAGES)) from None
    page = search_customers(query.q, query.limit, query.offset, customers)
    return CustomerListResponse.from_page(page)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer_detail(
    customer_id: str, customers: Annotated[CustomerStore, Depends(get_customer_store)]
) -> CustomerResponse:
    """The data of one customer (RF-6)."""
    # Declared as text: what is not an id names no customer, so it is the same 404 as an
    # unknown id and not a validation error (CA-6.3, spec decision D-3).
    if not _CUSTOMER_ID.fullmatch(customer_id) or int(customer_id) > _LARGEST_ID:
        raise not_found()
    return CustomerResponse.from_customer(get_customer(int(customer_id), customers))
