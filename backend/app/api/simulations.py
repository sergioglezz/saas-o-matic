"""Simulation routes (spec 004): they read, validate, call the services and answer.

No business rule and no SQL here (constitution principle 3): the amounts come from the quote
service of spec 001 and the storage is behind SimulationStore.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import ValidationError

from app.api.dependencies import get_customer_store, get_now, get_rate_source, get_simulation_store
from app.api.validation import field_errors, read_json_object, validation_error
from app.schemas.simulations import (
    SIMULATION_INVALID_MESSAGES,
    SimulationCreate,
    SimulationResponse,
)
from app.services.customers import CustomerStore
from app.services.pricing import TaxRateSource
from app.services.simulations import SimulationStore, save_simulation

router = APIRouter()


@router.post("/simulations", status_code=201, response_model=SimulationResponse)
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
