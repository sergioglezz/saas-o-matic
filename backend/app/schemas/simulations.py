"""Schemas of the simulation routes (spec 004 RF-1, RF-2, RF-4 and RF-5).

Input rules live here, at the API edge (constitution principle 3). Strict mode rejects 1.0,
1e0, "15", true and null for every integer, as in the quote (plan 002 DT-2).
"""

import dataclasses
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field

from app.domain.customers import MAX_CUSTOMER_ID
from app.domain.pricing import MAX_USERS, build_quote
from app.domain.simulations import (
    MAX_API_CALLS_PER_MONTH,
    MAX_STORAGE_GB,
    NewSimulation,
    Simulation,
    SimulationPage,
)
from app.schemas.pricing import USERS_INVALID_MESSAGE, TierLineResponse

CUSTOMER_ID_INVALID_MESSAGE = "Debe ser un número entero positivo"
CUSTOMER_COUNTRY_UNSUPPORTED_MESSAGE = "El país del cliente no está soportado"
STORAGE_INVALID_MESSAGE = "Debe ser un número entero entre 0 y 1000000"
API_CALLS_INVALID_MESSAGE = "Debe ser un número entero entre 0 y 1000000000"

# Message for a field that is present but invalid, whatever rule it breaks (002 CA-6.3).
SIMULATION_INVALID_MESSAGES = {
    "customer_id": CUSTOMER_ID_INVALID_MESSAGE,
    "active_users": USERS_INVALID_MESSAGE,  # the same rule as the quote's users (CA-2.2)
    "storage_gb": STORAGE_INVALID_MESSAGE,
    "api_calls_per_month": API_CALLS_INVALID_MESSAGE,
}


class SimulationCreate(BaseModel):
    """Body of POST /simulations: four JSON integers, case-sensitive names (RF-2).

    No country and no amount: the backend prices with the customer's country (CA-2.6, CA-3.3).
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    customer_id: Annotated[int, Field(ge=1, le=MAX_CUSTOMER_ID)]
    active_users: Annotated[int, Field(ge=0, le=MAX_USERS)]
    storage_gb: Annotated[int, Field(ge=0, le=MAX_STORAGE_GB)]
    api_calls_per_month: Annotated[int, Field(ge=0, le=MAX_API_CALLS_PER_MONTH)]

    def to_new_simulation(self) -> NewSimulation:
        return NewSimulation(**self.model_dump())


class SimulationResponse(BaseModel):
    """A saved simulation as the API returns it: the contract of spec 004 section 5."""

    id: int
    customer_id: int
    active_users: int
    storage_gb: int
    api_calls_per_month: int
    currency: str
    tiers: list[TierLineResponse]
    subtotal_cents: int
    tax_rate_bp: int
    tax_cents: int
    total_cents: int
    created_at: str

    @classmethod
    def from_simulation(cls, simulation: Simulation) -> Self:
        # Simulation already uses the contract's field names, in the contract's order.
        return cls.model_validate(dataclasses.asdict(simulation))


class SimulationListResponse(BaseModel):
    """200 body of GET /customers/{id}/simulations: one page and the total (CA-5.1, CA-5.3)."""

    items: list[SimulationResponse]
    total: int

    @classmethod
    def from_page(cls, page: SimulationPage) -> Self:
        items = [SimulationResponse.from_simulation(simulation) for simulation in page.items]
        return cls(items=items, total=page.total)


def _section_5_example() -> dict[str, object]:
    """The 201 example of spec section 5, built with the real calculation so it cannot drift."""
    price = build_quote(15, 2100)
    simulation = Simulation(
        id=1,
        customer_id=1,
        active_users=15,
        storage_gb=200,
        api_calls_per_month=50_000,
        currency=price.currency,
        tiers=price.tiers,
        subtotal_cents=price.subtotal_cents,
        tax_rate_bp=price.tax_rate_bp,
        tax_cents=price.tax_cents,
        total_cents=price.total_cents,
        created_at="2026-11-16T10:00:00Z",
    )
    return SimulationResponse.from_simulation(simulation).model_dump(mode="json")


# Examples for the interactive docs (RNF-5): the ones of spec 004 section 5.
SIMULATION_REQUEST_EXAMPLE: dict[str, object] = {
    "customer_id": 1,
    "active_users": 15,
    "storage_gb": 200,
    "api_calls_per_month": 50_000,
}
SIMULATION_RESPONSE_EXAMPLE: dict[str, object] = _section_5_example()
SIMULATION_LIST_RESPONSE_EXAMPLE: dict[str, object] = {
    "items": [SIMULATION_RESPONSE_EXAMPLE],
    "total": 1,
}
