"""Simulation routes (spec 004): they read, validate, call the services and answer.

No business rule and no SQL here (constitution principle 3): the amounts come from the quote
service of spec 001 and the storage is behind SimulationStore.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import ValidationError

from app.api.dependencies import get_customer_store, get_now, get_rate_source, get_simulation_store
from app.api.identifiers import parse_customer_id
from app.api.simulations_docs import HISTORY_RESPONSES, SAVE_BODY_DOC, SAVE_RESPONSES
from app.api.validation import field_errors, read_json_object, validation_error
from app.schemas.pagination import PAGE_INVALID_MESSAGES, PageQuery
from app.schemas.simulations import (
    SIMULATION_INVALID_MESSAGES,
    SimulationCreate,
    SimulationListResponse,
    SimulationResponse,
)
from app.services.customers import CustomerStore, get_customer
from app.services.pricing import TaxRateSource
from app.services.simulations import SimulationStore, list_simulations, save_simulation

router = APIRouter()


@router.post(
    "/simulations",
    status_code=201,
    response_model=SimulationResponse,
    openapi_extra=SAVE_BODY_DOC,
    responses=SAVE_RESPONSES,
)
def post_simulation(
    payload: Annotated[dict[str, object], Depends(read_json_object)],
    customers: Annotated[CustomerStore, Depends(get_customer_store)],
    simulations: Annotated[SimulationStore, Depends(get_simulation_store)],
    rates: Annotated[TaxRateSource, Depends(get_rate_source)],
    now: Annotated[datetime, Depends(get_now)],
) -> SimulationResponse:
    """Price a simulation for its customer's country and save it (RF-1)."""
    try:
        request = SimulationCreate.model_validate(payload)
    except ValidationError as error:
        # Every invalid field at once, before looking for the customer (CA-2.8, CA-3.2).
        raise validation_error(field_errors(error, SIMULATION_INVALID_MESSAGES)) from None
    # The service may still raise an unknown customer (404) or a country without rate (422);
    # app.api.error_mapping turns both into responses.
    simulation = save_simulation(request.to_new_simulation(), customers, simulations, rates, now)
    return SimulationResponse.from_simulation(simulation)


@router.get(
    "/customers/{customer_id}/simulations",
    response_model=SimulationListResponse,
    responses=HISTORY_RESPONSES,
)
def list_customer_simulations(
    customer_id: str,
    customers: Annotated[CustomerStore, Depends(get_customer_store)],
    simulations: Annotated[SimulationStore, Depends(get_simulation_store)],
    limit: Annotated[
        str | None,
        Query(description="Máximo de simulaciones devueltas: entero de 1 a 100. Por defecto, 50."),
    ] = None,
    offset: Annotated[
        str | None,
        Query(description="Posición de la primera simulación: entero de 0 a 1000000."),
    ] = None,
) -> SimulationListResponse:
    """The customer's simulations, newest first (RF-5)."""
    # The customer first, then the page: without a customer there is nothing to page, so a
    # 404 wins over a 422 (CA-5.5, spec decision D-7, plan DT-8).
    customer = get_customer(parse_customer_id(customer_id), customers)
    received = {"limit": limit, "offset": offset}
    try:
        page = PageQuery.model_validate(
            {name: value for name, value in received.items() if value is not None}
        )
    except ValidationError as error:
        raise validation_error(field_errors(error, PAGE_INVALID_MESSAGES)) from None
    history = list_simulations(customer.id, page.limit, page.offset, simulations)
    return SimulationListResponse.from_page(history)
