"""Simulation types and usage validation in the domain: spec 004 RF-2 and RF-4, plan DT-2.

Covers CA-2.3 and CA-2.4 as domain rules (the API reports them in T-06) and the shape of the
snapshot of CA-4.2. Task T-01.
"""

import dataclasses

import pytest

from app.domain.errors import (
    InvalidApiCallsError,
    InvalidStorageError,
    SimulationError,
    UnsupportedCustomerCountryError,
)
from app.domain.pricing import tier_breakdown
from app.domain.simulations import (
    MAX_API_CALLS_PER_MONTH,
    MAX_STORAGE_GB,
    NewSimulation,
    Simulation,
    SimulationPage,
    validate_usage,
)

# Field names of the 201 response in spec 004 section 5, in order.
CONTRACT_FIELDS = (
    "id",
    "customer_id",
    "active_users",
    "storage_gb",
    "api_calls_per_month",
    "currency",
    "tiers",
    "subtotal_cents",
    "tax_rate_bp",
    "tax_cents",
    "total_cents",
    "created_at",
)
NOT_PLAIN_INTEGERS = [
    pytest.param(True, id="true"),
    pytest.param(False, id="false"),
    pytest.param(1.5, id="decimal"),
    pytest.param(2.0, id="float-looking-integer"),
    pytest.param("200", id="text"),
    pytest.param(None, id="none"),
]


def test_usage_maximums_are_the_ones_of_the_spec() -> None:
    """CA-2.3, CA-2.4 (spec decision D-5): 1000000 GB and 1000000000 calls a month."""
    assert MAX_STORAGE_GB == 1_000_000
    assert MAX_API_CALLS_PER_MONTH == 1_000_000_000


@pytest.mark.parametrize(
    ("storage_gb", "api_calls_per_month"),
    [
        pytest.param(0, 0, id="both-zero"),
        pytest.param(MAX_STORAGE_GB, MAX_API_CALLS_PER_MONTH, id="both-max"),
        pytest.param(200, 50_000, id="SI-1"),
    ],
)
def test_accepts_integers_inside_both_ranges(storage_gb: int, api_calls_per_month: int) -> None:
    """CA-2.3, CA-2.4: 0 and the maximums are valid, both included."""
    validate_usage(storage_gb, api_calls_per_month)


@pytest.mark.parametrize(
    "storage_gb", [pytest.param(-1, id="negative"), pytest.param(MAX_STORAGE_GB + 1, id="max+1")]
)
def test_rejects_storage_out_of_range(storage_gb: int) -> None:
    """CA-2.3: storage_gb outside 0..1000000 raises InvalidStorageError."""
    with pytest.raises(InvalidStorageError):
        validate_usage(storage_gb, 0)


@pytest.mark.parametrize(
    "api_calls_per_month",
    [pytest.param(-1, id="negative"), pytest.param(MAX_API_CALLS_PER_MONTH + 1, id="max+1")],
)
def test_rejects_api_calls_out_of_range(api_calls_per_month: int) -> None:
    """CA-2.4: api_calls_per_month outside 0..1000000000 raises InvalidApiCallsError."""
    with pytest.raises(InvalidApiCallsError):
        validate_usage(0, api_calls_per_month)


@pytest.mark.parametrize("storage_gb", NOT_PLAIN_INTEGERS)
def test_rejects_storage_that_is_not_a_plain_integer(storage_gb: object) -> None:
    """CA-2.3: booleans, floats, text and None are not integers, even if they look like one."""
    with pytest.raises(InvalidStorageError):
        validate_usage(storage_gb, 0)  # type: ignore[arg-type]  # wrong type on purpose


@pytest.mark.parametrize("api_calls_per_month", NOT_PLAIN_INTEGERS)
def test_rejects_api_calls_that_are_not_a_plain_integer(api_calls_per_month: object) -> None:
    """CA-2.4: booleans, floats, text and None are not integers, even if they look like one."""
    with pytest.raises(InvalidApiCallsError):
        validate_usage(0, api_calls_per_month)  # type: ignore[arg-type]  # wrong type on purpose


def test_storage_is_checked_before_api_calls() -> None:
    """Plan section 4: with both wrong, the domain stops at storage; the API reports both."""
    with pytest.raises(InvalidStorageError):
        validate_usage(-1, -1)


@pytest.mark.parametrize(
    "error_type", [InvalidStorageError, InvalidApiCallsError, UnsupportedCustomerCountryError]
)
def test_simulation_errors_share_a_common_base(error_type: type[Exception]) -> None:
    """Plan section 4: every simulation rule violation derives from SimulationError."""
    assert issubclass(error_type, SimulationError)


def test_unsupported_customer_country_error_keeps_the_customer() -> None:
    """CA-3.4: the error says which customer has a country without tax rate."""
    assert UnsupportedCustomerCountryError(7).customer_id == 7


def test_simulation_fields_match_the_contract() -> None:
    """CA-1.1, CA-4.2 (spec decision D-2): the snapshot fields, without "users"."""
    assert tuple(field.name for field in dataclasses.fields(Simulation)) == CONTRACT_FIELDS


def test_new_simulation_has_only_the_four_input_fields() -> None:
    """CA-2.6: a simulation request carries no country and no amount."""
    names = tuple(field.name for field in dataclasses.fields(NewSimulation))

    assert names == ("customer_id", "active_users", "storage_gb", "api_calls_per_month")


def test_simulation_types_are_immutable() -> None:
    """CA-4.3: a saved snapshot cannot be changed after it is built."""
    simulation = Simulation(
        id=1,
        customer_id=1,
        active_users=15,
        storage_gb=200,
        api_calls_per_month=50_000,
        currency="EUR",
        tiers=tier_breakdown(15),
        subtotal_cents=14_000,
        tax_rate_bp=2100,
        tax_cents=2940,
        total_cents=16_940,
        created_at="2026-11-16T10:00:00Z",
    )
    page = SimulationPage(items=(simulation,), total=1)

    with pytest.raises(dataclasses.FrozenInstanceError):
        simulation.total_cents = 0  # type: ignore[misc]  # mutation on purpose
    with pytest.raises(dataclasses.FrozenInstanceError):
        page.total = 0  # type: ignore[misc]  # mutation on purpose
