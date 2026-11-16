"""Simulation use cases: save one and list a customer's history (spec 004 RF-1, RF-3 to RF-5).

Nothing here calculates a price: the amounts come from the quote service of spec 001, the same
code that answers POST /pricing/quote (plan 004 DT-1, ADR 0004).
"""

from datetime import datetime
from typing import Protocol

from app.core.clock import to_timestamp
from app.domain.errors import UnsupportedCountryError, UnsupportedCustomerCountryError
from app.domain.pricing import PriceQuote, validate_users
from app.domain.simulations import NewSimulation, Simulation, SimulationPage, validate_usage
from app.services.customers import CustomerStore, get_customer
from app.services.pricing import TaxRateSource, quote


class SimulationStore(Protocol):
    """Where simulations are kept; the repository implements it."""

    def add(self, new: NewSimulation, price: PriceQuote, created_at: str) -> Simulation: ...

    def list_for_customer(self, customer_id: int, limit: int, offset: int) -> SimulationPage: ...


def save_simulation(
    new: NewSimulation,
    customers: CustomerStore,
    simulations: SimulationStore,
    rates: TaxRateSource,
    now: datetime,
) -> Simulation:
    """Price ``new`` for its customer's country and save it at instant ``now`` (RF-1, RF-4).

    The input is checked first, whoever the caller is (plan DT-2), so a wrong value is reported
    before an unknown customer (CA-3.2). Raises InvalidUsersError, InvalidStorageError,
    InvalidApiCallsError, CustomerNotFoundError or UnsupportedCustomerCountryError; nothing is
    saved in that case (CA-1.4).
    """
    validate_users(new.active_users)
    validate_usage(new.storage_gb, new.api_calls_per_month)
    customer = get_customer(new.customer_id, customers)
    try:
        # One read of the rate for the whole snapshot (001 CA-13.3).
        price = quote(new.active_users, customer.country, rates)
    except UnsupportedCountryError:
        # Reported on customer_id: the request has no country field (CA-3.4, plan DT-3).
        raise UnsupportedCustomerCountryError(customer.id) from None
    return simulations.add(new, price, to_timestamp(now))


def list_simulations(
    customer_id: int, limit: int, offset: int, simulations: SimulationStore
) -> SimulationPage:
    """One page of the customer's history, newest first (RF-5).

    The caller checks first that the customer exists: the route must answer 404 before it
    validates the page parameters (CA-5.5, plan DT-8).
    """
    return simulations.list_for_customer(customer_id, limit, offset)
