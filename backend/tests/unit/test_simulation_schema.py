"""Simulation schemas without a server (level U), spec 004 task T-06.

Covers RF-2 (CA-2.1 to CA-2.6, CA-2.8) with the JSON values of table 6.3, decoded like the API
decodes them, and RF-4 (CA-4.7) for the response. The body checks (CA-2.7) and the customer
checks (RF-3) need the server: they are tested over HTTP in T-08.
"""

import json

import pytest
from pydantic import ValidationError

from app.api.validation import field_errors
from app.domain.pricing import build_quote
from app.domain.simulations import NewSimulation, Simulation
from app.schemas.simulations import (
    SIMULATION_INVALID_MESSAGES,
    SIMULATION_RESPONSE_EXAMPLE,
    SimulationCreate,
    SimulationResponse,
)
from tests.simulations_data import CALLS, CUSTOMER, STORAGE, SV_CASES, USERS, raw_body


def _tier(tier: int, from_users: int, to_users: int | None, units: int, price: int) -> object:
    return {
        "tier": tier,
        "from_users": from_users,
        "to_users": to_users,
        "units": units,
        "unit_price_cents": price,
        "amount_cents": units * price,
    }


# The 201 response of spec 004 section 5.
SECTION_5_RESPONSE: dict[str, object] = {
    "id": 1,
    "customer_id": 1,
    "active_users": 15,
    "storage_gb": 200,
    "api_calls_per_month": 50000,
    "currency": "EUR",
    "tiers": [_tier(1, 1, 10, 10, 1000), _tier(2, 11, 50, 5, 800), _tier(3, 51, None, 0, 500)],
    "subtotal_cents": 14000,
    "tax_rate_bp": 2100,
    "tax_cents": 2940,
    "total_cents": 16940,
    "created_at": "2026-11-16T10:00:00Z",
}


def _decode(changes: dict[str, str | None]) -> dict[str, object]:
    decoded: dict[str, object] = json.loads(raw_body(changes))
    return decoded


def _details(changes: dict[str, str | None]) -> set[tuple[str, str]]:
    with pytest.raises(ValidationError) as raised:
        SimulationCreate.model_validate(_decode(changes))
    errors = field_errors(raised.value, SIMULATION_INVALID_MESSAGES)
    return {(error.field, error.message) for error in errors}


def test_valid_request_becomes_a_new_simulation() -> None:
    """CA-2.1 to CA-2.4: SI-1 is valid and keeps its four values."""
    request = SimulationCreate.model_validate(_decode({}))

    assert request.to_new_simulation() == NewSimulation(1, 15, 200, 50_000)


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        pytest.param({USERS: "-0"}, NewSimulation(1, 0, 200, 50_000), id="SI-12-minus-zero"),
        pytest.param({USERS: "0", STORAGE: "0", CALLS: "0"}, NewSimulation(1, 0, 0, 0), id="zeros"),
        pytest.param(
            {USERS: "100000", STORAGE: "1000000", CALLS: "1000000000"},
            NewSimulation(1, 100_000, 1_000_000, 1_000_000_000),
            id="SI-9-maximums",
        ),
        pytest.param(
            {CUSTOMER: "9223372036854775807"},
            NewSimulation(2**63 - 1, 15, 200, 50_000),
            id="largest-customer-id",
        ),
    ],
)
def test_accepts_the_limits(changes: dict[str, str | None], expected: NewSimulation) -> None:
    """CA-2.1 to CA-2.4: both ends of every range; -0 is 0 (002 CA-2.1)."""
    request = SimulationCreate.model_validate(_decode(changes))

    assert request.to_new_simulation() == expected


@pytest.mark.parametrize(("changes", "expected"), SV_CASES)
def test_rejects_invalid_requests(
    changes: dict[str, str | None], expected: set[tuple[str, str]]
) -> None:
    """CA-2.1 to CA-2.6, CA-2.8: one detail per field, all at once, with the texts of section 5."""
    assert _details(changes) == expected


def test_response_is_the_contract_of_section_5() -> None:
    """CA-1.1, CA-4.7, spec decision D-2: no "users", integers and "to_users": null."""
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

    dumped = SimulationResponse.from_simulation(simulation).model_dump(mode="json")

    assert dumped == SECTION_5_RESPONSE
    assert list(dumped) == list(SECTION_5_RESPONSE)


def test_documented_example_is_the_one_of_section_5() -> None:
    """RNF-5: the example shown in /docs is the exact response of section 5."""
    assert SIMULATION_RESPONSE_EXAMPLE == SECTION_5_RESPONSE
